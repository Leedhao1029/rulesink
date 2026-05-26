#!/usr/bin/env python3
"""
SOUL Arbiter — 宪法约束层接入器
================================
职责：在 hermes_dispatcher 的每个决策点写入事件日志
接入点：
  1. classify_intent      → 意图识别结果 + 置信度
  2. coordinate           → 跨域协调结果 / 冲突检测
  3. run_orchestrator     → 编排器执行前（域 + 任务校验）
  4. 补建触发（_auto_trigger_it） → L3 缺失检测
  5. 熔断触发             → retry_depth >= 3
  6. L1→L3直接调用         → L1绕过L2直接调用L3脚本 → BLOCK

事件类型统一：soul_arbiter
记录：触发原因、涉及层级、拦截结果（PASS/BLOCK/FLAG）
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

HERMES_HOME = Path.home() / ".hermes"
EVENTS_FILE = HERMES_HOME / "events" / "events.jsonl"

# 中文 domain 名称映射（与 hermes_dispatcher.L2_NAMES 保持一致）
DOMAIN_TO_CN = {
    "construction": "建筑工程总经理",
    "ecommerce":    "电子商务总经理",
    "investment":   "投资总经理",
    "it":          "IT技术总经理",
    "life":        "生活事务总经理",
    "multimodal":  "多模态总经理",
    "meta":        "自我进化总经理",
    "strategy":    "战略运营总经理",
    "game":        "游戏开发总经理",
    "academic":    "学术研究总经理",
    # 早期事件中可能出现的英文 key
    "investment":  "投资总经理",
    "life":        "生活事务总经理",
    "it":          "IT技术总经理",
}


def _to_cn(domain: Optional[str]) -> Optional[str]:
    """将英文 domain key 转换为中文名称"""
    if domain is None:
        return None
    return DOMAIN_TO_CN.get(domain, domain)


def _write(event_type: str, category: str, action: str,
           domain: Optional[str] = None,
           trigger_reason: str = "",
           involved_l1_parts: Optional[list] = None,
           result: str = "PASS",
           extra: Optional[dict] = None):
    """
    写入 soul_arbiter 事件

    category: 授权矩阵判断 | 调度越权拦截 | 异常熔断触发 | 意图识别审计 | 跨域协调审计
    action:   authorize | block | circuit_open | intent_routed | cross_domain_resolved
    result:   PASS | FLAG | BLOCK | ADVISORY | CIRCUIT_OPEN

    判定说明：
      PASS     = 符合规范，无需干预，正常执行
      ADVISORY = 发现潜在问题，需关注但不断开执行，记录供人工复核
      FLAG     = 发现需纠正的问题，继续执行但需修复
      BLOCK    = 违反核心约束，必须停止
      CIRCUIT_OPEN = 熔断触发
    """
    import os
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session": os.environ.get("HERMES_SESSION", "cli"),
        "event": "soul_arbiter",
        "arbiter": {
            "category": category,
            "action": action,
            "domain": _to_cn(domain),
            "trigger_reason": trigger_reason,
            "involved_l1_parts": involved_l1_parts or [],
            "result": result,
        },
        "extra": extra or {},
    }
    try:
        EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 不阻断主流程


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 1：意图识别审计
# ─────────────────────────────────────────────────────────────────────────────
def audit_intent(domain: str, confidence: float, raw_task: str, scores: dict = None):
    """在 classify_intent 之后调用"""
    _write(
        event_type="soul_arbiter",
        category="意图识别审计",
        action="intent_routed",
        domain=domain,
        trigger_reason=f"用户输入触发领域识别，命中 {domain}（置信度 {confidence:.2f}）",
        involved_l1_parts=["classify_intent"],
        result="PASS",
        extra={
            "confidence": confidence,
            "raw_task_preview": raw_task[:80],
            "all_scores": scores or {},
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 2：跨域协调审计
# ─────────────────────────────────────────────────────────────────────────────
def audit_coordinate(
    is_cross_domain: bool,
    primary: str,
    supporting: list,
    conflict: bool,
    conflict_reason: str,
    raw_task: str,
):
    """在 coordinate() 返回后调用"""
    action = "cross_domain_resolved"
    result = "PASS"
    trigger_reason = "跨域协调"

    if conflict:
        action = "block"
        result = "BLOCK"
        trigger_reason = f"检测到跨域冲突: {conflict_reason}"

    _write(
        event_type="soul_arbiter",
        category="调度越权拦截",
        action=action,
        domain=primary,
        trigger_reason=trigger_reason,
        involved_l1_parts=["coordinate", "detect_cross_domain"],
        result=result,
        extra={
            "is_cross_domain": is_cross_domain,
            "primary": primary,
            "supporting": supporting,
            "conflict": conflict,
            "conflict_reason": conflict_reason,
            "raw_task_preview": raw_task[:80],
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 3：编排器执行前授权
# ─────────────────────────────────────────────────────────────────────────────
def authorize_orchestrator(domain: str, task: str, orch_path: str):
    """
    在 run_orchestrator 入口调用
    作用：确认该域编排器存在且被授权执行
    """
    import os
    allowed_domains = {
        "construction", "ecommerce", "investment",
        "it", "life", "multimodal", "meta",
    }
    if domain not in allowed_domains:
        _write(
            event_type="soul_arbiter",
            category="授权矩阵判断",
            action="block",
            domain=domain,
            trigger_reason=f"域 '{domain}' 不在授权矩阵中",
            involved_l1_parts=["run_orchestrator", "ORCHESTRATORS"],
            result="BLOCK",
            extra={"task_preview": task[:50], "orch_path": orch_path},
        )
        return False

    _write(
        event_type="soul_arbiter",
        category="授权矩阵判断",
        action="authorize",
        domain=domain,
        trigger_reason=f"域 '{domain}' 授权执行编排器",
        involved_l1_parts=["run_orchestrator", "ORCHESTRATORS"],
        result="PASS",
        extra={"task_preview": task[:50], "orch_path": orch_path},
    )
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 4：L3 缺失检测（补建触发）
# ─────────────────────────────────────────────────────────────────────────────
def audit_l3_mismatch(
    domain: str,
    triggered: Any,  # Truthy = 触发了补建
    task: str,
    returncode: int,
    stderr: str,
):
    """
    在 _auto_trigger_it 返回后调用
    triggered 非空表示 L3 缺失，触发了补建流程
    """
    if not triggered:
        _write(
            event_type="soul_arbiter",
            category="调度越权拦截",
            action="l3_mismatch_check",
            domain=domain,
            trigger_reason="L3 能力验证通过，未触发补建",
            involved_l1_parts=["_auto_trigger_it"],
            result="PASS",
            extra={"returncode": returncode, "task_preview": task[:50]},
        )
        return

    # 触发了补建 → FLAG（系统发现能力缺口）
    _write(
        event_type="soul_arbiter",
        category="调度越权拦截",
        action="l3_mismatch_detected",
        domain=domain,
        trigger_reason=f"L3 能力缺口，触发自动建造流程（triggered_type={type(triggered).__name__}）",
        involved_l1_parts=["_auto_trigger_it", "it_orchestrator"],
        result="FLAG",
        extra={
            "triggered_type": type(triggered).__name__,
            "returncode": returncode,
            "stderr_preview": stderr[:200] if stderr else "",
            "task_preview": task[:50],
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 5：熔断触发
# ─────────────────────────────────────────────────────────────────────────────
def audit_circuit_breaker(
    domain: str,
    retry_depth: int,
    is_primary: bool,
    raw_task: str,
):
    """
    retry_depth >= 3 时调用（已达到熔断阈值）
    """
    _write(
        event_type="soul_arbiter",
        category="异常熔断触发",
        action="circuit_open",
        domain=domain,
        trigger_reason=(
            f"{'主责域' if is_primary else '配合域'} 重试次数已达上限（{retry_depth}次），"
            "执行熔断，人工介入"
        ),
        involved_l1_parts=["_main_inner", "retry_logic"],
        result="CIRCUIT_OPEN",
        extra={
            "retry_depth": retry_depth,
            "is_primary": is_primary,
            "raw_task_preview": raw_task[:50],
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 6：L2 编排器执行结果审计
# ─────────────────────────────────────────────────────────────────────────────
def audit_orchestrator_result(
    domain: str,
    returncode: int,
    task: str,
    execution_time: Optional[float] = None,
):
    """在 run_orchestrator 返回后调用"""
    result_map = {0: "PASS", 1: "FAIL"}
    _write(
        event_type="soul_arbiter",
        category="意图识别审计",
        action="orchestrator_executed",
        domain=domain,
        trigger_reason=f"编排器执行完成，返回码 {returncode}",
        involved_l1_parts=["run_orchestrator"],
        result=result_map.get(returncode, "UNKNOWN"),
        extra={
            "returncode": returncode,
            "execution_time_s": execution_time,
            "task_preview": task[:50],
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 健康类 skill 识别：扩展前缀 + 关键词双重检测
# ─────────────────────────────────────────────────────────────────────────────
HEALTH_SKILL_PATTERNS = {
    # skill 名称包含这些关键词 → 健康类 skill
    "life-health", "life-nutrition", "life-exercise", "life-sleep",
    "life-mental", "life-habit",
    "health", "nutrition", "exercise", "sleep", "mental",
}

MEDICAL_OVERREACH_PATTERNS = [
    # 诊断类（明确医疗行为）
    "诊断", "患有", "确诊", "排除癌症", "肿瘤标志物升高",
    "ct显示", "mri显示", "病理结果是", "ct平扫", "磁共振显示",
    "超声提示", "x光显示", "影像学检查",
    "这是癌症", "是恶性肿瘤", "已经是晚期",
    "this is cancer", "diagnosed with", "you have cancer",
    "it's cancer", "malignant tumor", "stage 4",
    # 处方类（明确治疗行为）
    "开药", "服用药物", "用药方案", "药物剂量", "处方药",
    "口服化疗", "靶向药", "内分泌治疗",
    "prescribe", "prescription", "take this medication",
    "you should take", "i recommend taking",
    # 手术类
    "建议手术", "必须手术", "手术切除", "需要开刀",
    "尽早手术", "根治术", "减瘤手术",
    "surgery", "operate", "remove surgically",
    "you need surgery", "surgical resection",
    # 绝对化结论类
    "100% 治愈", "一定不会", "肯定没有转移", "绝对不是癌",
    "definitely cancer", "absolutely safe", "no side effects",
    "guaranteed to work", "certainly not malignant",
    # 替代医疗类
    "喝果汁能治疗", "碱性饮食治癌", "自然疗法替代",
    "juice cure", "alkaline diet cancer", "alternative to chemo",
    "放弃化疗", "不做手术也可以", "保守治疗就够了",
    # 肿瘤/癌症相关越权
    "肺部肿瘤", "肝部肿瘤", "乳腺肿瘤", "结肠肿瘤",
    "良性肿瘤", "恶性肿瘤", "疑似肿瘤", "肿瘤可能",
    "癌症", "癌变", "癌细胞", "转移癌",
    "化疗", "放疗", "免疫治疗", "靶向治疗",
    "肿瘤标志物", "CA125", "CA199", "AFP", "PSA",
    "肺癌", "肝癌", "乳腺癌", "胃癌", "肠癌",
    "胰腺癌", "卵巢癌", "前列腺癌",
]

ADVISORY_MEDICAL_PHRASES = [
    # 建议类（需要标记"建议就医"）
    "建议去医院", "最好做个检查", "可以服用",
    "建议就诊", "应该去检查", "推荐就医",
    "去医院看看", "做个检查", "找医生看看",
    "挂个号", "门诊随访", "进一步检查",
    "you should see a doctor", "consider getting checked",
    "might want to consult", "recommend seeing a specialist",
    "see a doctor", "get it checked", "medical evaluation",
    # 风险提示类（中等风险）
    "可能有风险", "需要进一步确认", "建议排除一下",
    "不能排除", "需要鉴别诊断", "建议排查",
]


def _is_health_skill(skill_name: str) -> bool:
    """判断 skill 是否属于健康类"""
    skill_lower = skill_name.lower()
    for pattern in HEALTH_SKILL_PATTERNS:
        if pattern in skill_lower:
            return True
    return False


def _scan_medical_overreach(content: str) -> tuple[bool, list[str], list[str]]:
    """
    扫描内容中的医疗越权关键词。
    返回 (is_overreach, overreach_keywords, advisory_phrases)
    """
    content_lower = content.lower()
    found_overreach = []
    found_advisory = []

    for kw in MEDICAL_OVERREACH_PATTERNS:
        if kw.lower() in content_lower:
            found_overreach.append(kw)

    for kw in ADVISORY_MEDICAL_PHRASES:
        if kw.lower() in content_lower:
            found_advisory.append(kw)

    return found_overreach, found_advisory


def _get_health_skill_domain(skill_name: str) -> str:
    """根据 skill 名称提取健康子域"""
    skill_lower = skill_name.lower()
    if "nutrition" in skill_lower or "食" in skill_lower:
        return "health-nutrition"
    if "exercise" in skill_lower or "运动" in skill_lower or "健身" in skill_lower:
        return "health-exercise"
    if "sleep" in skill_lower or "睡眠" in skill_lower:
        return "health-sleep"
    if "mental" in skill_lower or "心理" in skill_lower:
        return "health-mental"
    return "health-general"


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 7：skill_invoke 执行层审计（盲区补全）
# ─────────────────────────────────────────────────────────────────────────────
def audit_skill_invoke(skill_name: str, args: str = ""):
    """
    在 l1_event_utils.skill_invoke() 被调用时触发。
    覆盖场景：用户直接调用 skill 而非通过 L2 编排器。
    这是 SOUL Arbiter 从编排层扩展到执行层的最小化补丁。
    """
    # 解析 skill 前缀判断域
    domain_map = {
        "it": "it", "construction": "construction", "ecommerce": "ecommerce",
        "investment": "investment", "life": "life", "multimodal": "multimodal",
        "meta": "meta", "strategy": "strategy", "game": "game",
        "academic": "academic", "shopify": "ecommerce",
    }
    prefix = skill_name.split("-")[0].split("_")[0].lower()
    domain = domain_map.get(prefix, "unknown")

    # 高风险 skill 直接标 FLAG（health 类走单独审计路径）
    high_risk = {"finance", "security", "legal", "devops"}
    is_health = _is_health_skill(skill_name)

    if is_health:
        result = "HEALTH_DOMAIN"  # 健康类走专门审计流程
    elif prefix in high_risk:
        result = "FLAG"
    else:
        result = "PASS"

    _write(
        event_type="soul_arbiter",
        category="执行层审计",
        action="skill_invoked",
        domain=domain,
        trigger_reason=f"skill '{skill_name}' 被直接调用（绕过编排器）",
        involved_l1_parts=["l1_event_utils", "skill_invoke"],
        result=result,
        extra={
            "skill": skill_name,
            "skill_prefix": prefix,
            "is_health_skill": is_health,
            "health_subdomain": _get_health_skill_domain(skill_name) if is_health else None,
            "args_preview": args[:100],
            "via_orchestrator": False,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 8：健康类 skill 内容审计（医疗越权扫描）
# 触发时机：skill 执行结果返回后（L2 编排器返回前 / skill_invoke 结果返回前）
# ─────────────────────────────────────────────────────────────────────────────
def audit_health_skill_content(
    skill_name: str,
    output_content: str,
    task: str = "",
    via_orchestrator: bool = False,
):
    """
    对健康类 skill 的输出内容进行医疗越权扫描。
    检测三类风险：
      1. 明确诊断/治疗/手术建议（BLOCK 级别）
      2. 替代医疗/绝对化结论（FLAG 级别）
      3. 建议就医但未越权（ADVISORY 标记）

    via_orchestrator=True 表示经过 L2 编排器（有专业监督）
    via_orchestrator=False 表示用户直接调用（无专业监督，最高风险）
    """
    if not _is_health_skill(skill_name):
        return  # 非健康类 skill 直接跳过

    overreach_kws, advisory_phrases = _scan_medical_overreach(output_content)
    health_subdomain = _get_health_skill_domain(skill_name)

    # 判定结果级别
    if overreach_kws:
        # 有医疗越权内容 → 根据 via_orchestrator 决定严重程度
        if via_orchestrator:
            # 经过编排器 → FLAG（专业监督存在）
            result = "FLAG"
            severity = "MEDICAL_OVERREACH_VIA_ORCHESTRATOR"
        else:
            # 直接调用 → BLOCK（无专业监督，风险最高）
            result = "BLOCK"
            severity = "MEDICAL_OVERREACH_DIRECT"
    elif advisory_phrases:
        # 有建议就医但无越权 → ADVISORY（标记供人工复核）
        result = "ADVISORY"
        severity = "MEDICAL_ADVISORY"
    else:
        # 无风险内容 → PASS
        result = "PASS"
        severity = "CLEAR"
        overreach_kws = []
        advisory_phrases = []

    _write(
        event_type="soul_arbiter",
        category="健康域医疗越权审计",
        action=severity.lower(),
        domain="life",
        trigger_reason=(
            f"健康类 skill '{skill_name}' 输出审计"
            f"{'（经编排器）' if via_orchestrator else '（直接调用）'}"
        ),
        involved_l1_parts=["audit_health_skill_content"],
        result=result,
        extra={
            "skill": skill_name,
            "health_subdomain": health_subdomain,
            "via_orchestrator": via_orchestrator,
            "medical_overreach_keywords": overreach_kws,
            "advisory_phrases": advisory_phrases,
            "severity": severity,
            "output_preview": output_content[:200],
            "task_preview": task[:80],
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点11：L1越级调用审计（P7门禁）
# ─────────────────────────────────────────────────────────────────────────────
def audit_l1_override(domain: str, override_type: str, raw_task: str):
    """
    记录L1越级调用行为（ENV_MAINTENANCE / CAPABILITY_BUILD 路径）。

    约束来源：SOUL.md v3.0 核心原则 — "只做裁判，不做选手"
    P7门禁：这些路径直接调用L3，跳过了L2编排审查，需要标记为越级行为。

    override_type: "ENV_MAINTENANCE" 或 "CAPABILITY_BUILD"
    result: FLAG 表示越级（vs PASS 表示正常调度）
    """
    _write(
        event_type="soul_arbiter",
        category="L1越级调用审计",
        action="l1_override_detected",
        domain=domain,
        trigger_reason=f"L1越级调用{override_type}路径（跳过了L2编排审查）",
        involved_l1_parts=["run_orchestrator", "_classify_task_type"],
        result="FLAG",
        extra={
            "override_type": override_type,
            "raw_task_preview": raw_task[:80],
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点10：Plan透明化检查（复杂度>=3时强制）
# ─────────────────────────────────────────────────────────────────────────────
def audit_plan_checkpoint(domain: str, complexity: int, raw_task: str, plan_summary: str):
    """
    在 run_orchestrator 入口对复杂度>=3的任务记录Plan摘要。

    约束来源：SOUL.md v3.0 五步闭环协议 — Plan步骤要求
    门禁触发：复杂度>=3
    记录内容：域、复杂度、任务摘要、Plan摘要
    """
    _write(
        event_type="soul_arbiter",
        category="Plan透明化检查",
        action="plan_recorded",
        domain=domain,
        trigger_reason=f"复杂度={complexity}（>=3门禁），记录Plan摘要",
        involved_l1_parts=["run_orchestrator", "_estimate_complexity"],
        result="PASS",
        extra={
            "complexity": complexity,
            "plan_summary": plan_summary,
            "raw_task_preview": raw_task[:80],
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 A：L1→L2 管道网关审计（CA-2026-05-13-PIPELINE）
# ─────────────────────────────────────────────────────────────────────────────
def audit_pipeline_l1_to_l2(
    domain: str,
    gate_result: str,
    complexity: int,
    complexity_details: dict,
    is_override: bool,
    override_type: str | None,
    override_reason: str | None,
    escaped_by: str | None,
    task_preview: str,
    plan_summary: str,
):
    """
    L1→L2 管道网关的审计函数（由 _pipeline_l1_to_l2() 调用）。
    gate_result: PASS | BLOCK | REDIRECT | DEGRADED
    is_override: 是否为越级决策（ENV_MAINTENANCE / CAPABILITY_BUILD）
    escaped_by: auto_redirect | user_override | None
    """
    category_map = {
        "PASS": "L1→L2网关授权",
        "BLOCK": "L1→L2网关拦截",
        "REDIRECT": "L1→L2网关重定向",
        "DEGRADED": "L1→L2网关降级",
    }
    action_map = {
        "PASS": "gate_pass",
        "BLOCK": "gate_block",
        "REDIRECT": "gate_redirect",
        "DEGRADED": "gate_degraded",
    }
    category = category_map.get(gate_result, "L1→L2网关审计")
    action = action_map.get(gate_result, "gate_decision")

    if gate_result == "BLOCK":
        result = "BLOCK"
    elif gate_result == "REDIRECT":
        result = "FLAG"  # REDIRECT 是主动行为变更，标记关注
    elif gate_result == "DEGRADED":
        result = "ADVISORY"
    else:
        result = "PASS"

    trigger_reason = f"L1→L2网关判定={gate_result}"
    if is_override and override_type:
        trigger_reason += f"（越级类型={override_type}）"
    if escaped_by:
        trigger_reason += f" | 逃脱={escaped_by}"

    _write(
        event_type="soul_arbiter",
        category=category,
        action=action,
        domain=domain,
        trigger_reason=trigger_reason,
        involved_l1_parts=["_pipeline_l1_to_l2", "_gate_p6", "_gate_p7", "_gate_p8"],
        result=result,
        extra={
            "gate_result": gate_result,
            "complexity": complexity,
            "complexity_details": complexity_details,
            "is_override": is_override,
            "override_type": override_type,
            "override_reason": override_reason,
            "escaped_by": escaped_by,
            "task_preview": task_preview,
            "plan_summary": plan_summary,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 B：L2→L3 管道网关审计（CA-2026-05-13-PIPELINE）
# ─────────────────────────────────────────────────────────────────────────────
def audit_pipeline_l2_to_l3(
    domain: str,
    gate_result: str,
    l3_count: int,
    blocked_reason: str | None,
    escaped_by: str | None,
    disclaimer: str | None,
    task_preview: str,
):
    """
    L2→L3 管道网关的审计函数（由 _pipeline_l2_to_l3() 调用）。
    gate_result: PASS | BLOCK | REDIRECT
    """
    category_map = {
        "PASS": "L2→L3网关授权",
        "BLOCK": "L2→L3网关拦截",
        "REDIRECT": "L2→L3网关重定向",
    }
    action_map = {
        "PASS": "gate_pass",
        "BLOCK": "gate_block",
        "REDIRECT": "gate_redirect",
    }
    category = category_map.get(gate_result, "L2→L3网关审计")
    action = action_map.get(gate_result, "gate_decision")

    if gate_result == "BLOCK":
        result = "BLOCK"
    elif gate_result == "REDIRECT":
        result = "FLAG"
    else:
        result = "PASS"

    trigger_reason = f"L2→L3网关判定={gate_result}（发现{l3_count}个L3）"
    if blocked_reason:
        trigger_reason += f" | 拦截原因={blocked_reason}"

    _write(
        event_type="soul_arbiter",
        category=category,
        action=action,
        domain=domain,
        trigger_reason=trigger_reason,
        involved_l1_parts=["_pipeline_l2_to_l3"],
        result=result,
        extra={
            "gate_result": gate_result,
            "l3_count": l3_count,
            "blocked_reason": blocked_reason,
            "escaped_by": escaped_by,
            "disclaimer": disclaimer,
            "task_preview": task_preview,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 P6：熔断拦截审计（CA-2026-05-13-PIPELINE）
# ─────────────────────────────────────────────────────────────────────────────
def audit_pipeline_circuit_breaker(
    domain: str,
    gate_result: str,
    blocked_reason: str,
    task_preview: str,
):
    """
    P6 熔断门禁的审计函数。
    当 P6 触发 BLOCK 时调用（熔断约束命中）。
    """
    _write(
        event_type="soul_arbiter",
        category="P6熔断拦截",
        action="p6_circuit_block",
        domain=domain,
        trigger_reason=f"P6熔断触发 | BLOCK原因={blocked_reason}",
        involved_l1_parts=["_gate_p6_failure_circuit_breaker", "_pipeline_l1_to_l2"],
        result="CIRCUIT_OPEN",
        extra={
            "gate_result": gate_result,
            "blocked_reason": blocked_reason,
            "task_preview": task_preview,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 接入点 L1→L3：L1 直接调用 L3 脚本检测（BLOCK 级别）
# 触发条件：L1 绕过 L2 编排器，直接调用 l3_*.py 脚本
# ─────────────────────────────────────────────────────────────────────────────
def audit_l1_to_l3_direct_call(
    l3_script_name: str,
    task_preview: str,
    domain: str,
    bypass_route: str,
) -> str:
    """
    Soul Arbiter L1→L3 直接调用检测。
    当 L1 绕过 L2 编排器直接调用 L3 脚本时，输出 BLOCK 并记录审计日志。

    返回值：
        "BLOCK" — 直接调用被 Soul Arbiter 拦截

    检测逻辑（由调用方在调用前执行）：
        - 若 L1 尝试 import l3_*.py 或调用 match_skill("l3_xxx") → 调用此函数
        - L3 脚本应通过 L2 编排器间接调用，L1 直接调用是越级
    """
    _write(
        event_type="soul_arbiter",
        category="L1越级调用L3",
        action="l1_to_l3_bypass_block",
        domain=domain,
        trigger_reason=f"L1直接调用L3脚本={l3_script_name}，绕过L2编排器",
        involved_l1_parts=["l1_orchestrator"],
        result="BLOCK",
        extra={
            "l3_script": l3_script_name,
            "task_preview": task_preview,
            "bypass_route": bypass_route,
            "violation": "L1直接调用L3脚本违反'只做裁判'原则",
            "correct_route": f"L1→{domain}_orchestrator→{l3_script_name}",
        },
    )
    return "BLOCK"


# ─────────────────────────────────────────────────────────────────────────────
# SoulArbiter 类 — 宪法仲裁核心（OOP接口，供 dispatch_guard 调用）
# ─────────────────────────────────────────────────────────────────────────────
class SoulArbiter:
    """
    Soul Arbiter 宪法仲裁核心类。
    dispatch_guard 插件通过 arbiter.py_audit() / arbiter.skill_audit() 调用。
    
    审计结论：
      PASS     = 符合规范，放行
      FLAG     = 发现问题，继续执行但需关注
      BLOCK    = 违反核心约束，强制拦截
      ADVISORY = 需人工复核
    """

    def py_audit(self, script_path: str, ctx: dict) -> dict:
        """
        L3 Python 脚本安全审计。
        
        检测维度：
        1. 危险API调用（eval/exec/os.system/subprocess/危险import）
        2. 硬编码凭证/密钥
        3. 文件写入路径穿越
        4. 网络请求逃逸
        5. 编码注入
        
        Returns: {"verdict": str, "reason": str, "notes": list, "suggestion": str}
        """
        import os, re
        
        if not os.path.exists(script_path):
            return {
                "verdict": "BLOCK",
                "reason": f"脚本不存在: {script_path}",
                "notes": ["path_not_found"],
                "suggestion": "检查脚本路径是否正确",
            }
        
        try:
            content = open(script_path, encoding="utf-8").read()
        except Exception as e:
            return {
                "verdict": "BLOCK",
                "reason": f"无法读取脚本: {e}",
                "notes": ["read_error"],
                "suggestion": "检查文件权限",
            }
        
        notes = []
        
        # ── 危险API检测 ─────────────────────────────────────────────────────
        DANGEROUS_PATTERNS = [
            (r'\beval\s*\(', "eval() 动态代码执行"),
            (r'\bexec\s*\(', "exec() 动态代码执行"),
            (r'os\.system\s*\(', "os.system() 命令注入风险"),
            (r'subprocess\.call\s*\(', "subprocess.call() 需审查"),
            (r'subprocess\.run\s*\(', "subprocess.run() 需审查"),
            (r'subprocess\.Popen\s*\(', "subprocess.Popen() 需审查"),
            (r'\bos\.popen\s*\(', "os.popen() 命令注入风险"),
            (r'__import__\s*\(', "__import__() 动态导入"),
            (r'pickle\.load\s*\(', "pickle.load() 反序列化风险"),
            (r'yaml\.load\s*\(', "yaml.load() 反序列化风险（应使用 Loader=yaml.SafeLoader）"),
            (r'socket\s*\.connect\s*\(', "socket连接（检查目的地）"),
            (r'requests\.get\s*\(', "requests.get() 需审查URL来源"),
            (r'eval\s*\(.*用户输入', "用户输入进入eval"),
        ]
        
        for pattern, desc in DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                notes.append(f"危险API: {desc}")
        
        # ── 凭证/密钥硬编码检测 ─────────────────────────────────────────────
        CREDENTIAL_PATTERNS = [
            (r'password\s*=\s*["\'][^"\']{3,}', "硬编码密码"),
            (r'api[_-]?key\s*=\s*["\'][A-Za-z0-9_-]{20,}', "硬编码API密钥"),
            (r'secret\s*=\s*["\'][^"\']{8,}', "硬编码secret"),
            (r'bearer\s+[A-Za-z0-9_-]{20,}', "硬编码Bearer Token"),
            (r'aws[_-]?access[_-]?key', "AWS凭证"),
            (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "私钥文件"),
        ]
        
        for pattern, desc in CREDENTIAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                notes.append(f"凭证泄露: {desc}")
        
        # ── 路径穿越检测 ───────────────────────────────────────────────────
        if re.search(r'\.\./', content):
            notes.append("路径穿越: 检测到 '../' 模式")
        
        # ── 危险度判定 ───────────────────────────────────────────────────────
        if notes:
            critical_notes = [n for n in notes if any(k in n for k in ["eval", "exec", "os.system", "私钥", "AWS", "password=", "api_key"])]
            if critical_notes:
                return {
                    "verdict": "BLOCK",
                    "reason": f"L3脚本 {os.path.basename(script_path)} 含危险操作",
                    "notes": notes,
                    "suggestion": "必须修复以下问题后重新提交:\n  " + "\n  ".join(f"- {n}" for n in notes),
                    "script_path": script_path,
                }
            else:
                return {
                    "verdict": "FLAG",
                    "reason": f"L3脚本 {os.path.basename(script_path)} 需人工审查",
                    "notes": notes,
                    "suggestion": "人工审查确认安全后重新提交",
                    "script_path": script_path,
                }
        
        return {
            "verdict": "PASS",
            "reason": f"脚本 {os.path.basename(script_path)} 审计通过",
            "notes": [],
            "suggestion": "",
            "script_path": script_path,
        }
    
    def skill_audit(self, skill_name: str, skill_path: str, ctx: dict) -> dict:
        """
        SKILL.md P0 合规性审计。
        
        检测维度：
        1. frontmatter 完整性（name/triggers/steps 必填）
        2. 危险 trigger 词（医疗越权/投资建议/政治敏感）
        3. steps 缺失或为空
        4. 危险内容模式
        
        Returns: {"verdict": str, "reason": str, "notes": list, "suggestion": str}
        """
        import os, re
        
        if not os.path.exists(skill_path):
            return {
                "verdict": "BLOCK",
                "reason": f"SKILL不存在: {skill_path}",
                "notes": ["skill_not_found"],
                "suggestion": "检查 skill 名称是否正确",
                "skill_name": skill_name,
            }
        
        try:
            content = open(skill_path, encoding="utf-8").read()
        except Exception as e:
            return {
                "verdict": "BLOCK",
                "reason": f"无法读取SKILL: {e}",
                "notes": ["read_error"],
                "suggestion": "检查文件权限",
                "skill_name": skill_name,
            }
        
        notes = []
        
        # ── frontmatter 解析 ─────────────────────────────────────────────────
        fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not fm_match:
            notes.append("frontmatter缺失（文件开头必须有 --- YAML ---）")
        else:
            fm_text = fm_match.group(1)
            required_fields = ["name:", "triggers:"]
            for field in required_fields:
                if field not in fm_text:
                    notes.append(f"必填字段缺失: {field.strip(':')}")

        # ── 元级技能豁免 ─────────────────────────────────────────────────────
        # CEO直辖的元级技能（domain=meta）不适用危险 trigger 拦截规则
        is_meta_skill = bool(re.search(r'^domain:\s*meta', fm_text, re.MULTILINE)) if fm_text else False
        is_ceo_exempt = is_meta_skill

        # ── 危险 trigger 词检测（条件性豁免）───────────────────────────────
        DANGEROUS_TRIGGERS = [
            ("投资建议", "投资建议类 trigger 需走投资域编排器"),
            ("医疗诊断", "医疗诊断类 trigger 需有免责声明"),
            ("开药", "开药类 trigger 超出健康类 skill 范围"),
            ("手术", "手术建议超出健康类 skill 范围"),
        ]

        if is_ceo_exempt:
            for kw, desc in DANGEROUS_TRIGGERS:
                if kw in content:
                    notes.append(f"[豁免] 元级技能含'{kw}'，已记录: {desc}")
        else:
            for kw, desc in DANGEROUS_TRIGGERS:
                if kw in content:
                    notes.append(f"危险trigger: {kw} — {desc}")
        
        # ── steps 缺失检测 ──────────────────────────────────────────────────
        steps_match = re.search(r'^steps:\s*$', content, re.MULTILINE)
        if steps_match:
            after_steps = content[steps_match.end():]
            next_heading = re.search(r'^[\w-]+:', after_steps, re.MULTILINE)
            steps_content = after_steps[:next_heading.start() if next_heading else len(after_steps)].strip()
            if not steps_content or len(steps_content) < 20:
                notes.append("steps 字段为空或内容过少（需有具体操作步骤）")
        
        # ── 医疗越权内容检测 ────────────────────────────────────────────────
        for kw in ["诊断为癌症", "确诊", "开药方案", "手术切除"]:
            if kw in content:
                notes.append(f"医疗越权内容: {kw}")
        
        if notes:
            critical_notes = [n for n in notes if any(k in n for k in ["投资建议", "开药", "手术", "诊断"])]
            if critical_notes:
                return {
                    "verdict": "BLOCK",
                    "reason": f"SKILL '{skill_name}' 含核心约束违反",
                    "notes": notes,
                    "suggestion": "必须修复以下问题后重新提交:\n  " + "\n  ".join(f"- {n}" for n in notes),
                    "skill_name": skill_name,
                }
            else:
                return {
                    "verdict": "FLAG",
                    "reason": f"SKILL '{skill_name}' 需人工审查",
                    "notes": notes,
                    "suggestion": "人工审查确认后重新提交",
                    "skill_name": skill_name,
                }
        
        return {
            "verdict": "PASS",
            "reason": f"SKILL '{skill_name}' 审计通过",
            "notes": [],
            "suggestion": "",
            "skill_name": skill_name,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 辅助：生成 soul_arbiter 统计报告（供 hermes --soul-stats 使用）
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# B2-B5 补充门禁函数（提案A — 2026-05-25）
# 补充 SOUL.md/PIPELINE.md 声明但此前缺失的门禁检测函数
# ─────────────────────────────────────────────────────────────────────────────

def _detect_external_api(task: str) -> bool:
    """
    P2 外部API检测。
    检测用户任务是否涉及外部API调用（如 HTTP请求、第三方SDK、数据库直连）。
    返回: True=检测到外部API, False=无
    """
    import re
    external_patterns = [
        r"https?://", r"api[_-]?key", r"fetch\(", r"requests\.",
        r"curl", r"wget", r"SDK", r"endpoint", r"http[s]?://[^\s]+",
    ]
    for pattern in external_patterns:
        if re.search(pattern, task, re.IGNORECASE):
            return True
    return False

def _detect_multi_step(task: str) -> bool:
    """
    P4 多步骤检测。
    检测用户任务是否包含多个执行步骤。
    返回: True=多步骤, False=单步
    """
    import re
    multi_step_patterns = [
        r"先.*再", r"然后", r"接着", r"最后", r"首先.*其次",
        r"批量", r"每个.*都", r"循环", r"迭代", r"依次",
    ]
    count = 0
    for pattern in multi_step_patterns:
        if re.search(pattern, task):
            count += 1
    return count >= 2

def _write_gate_proposal_timeout(event_id: str, timeout_seconds: int, decision: str):
    """
    P2-memo 超时事件记录。
    当门禁提案超时时调用，写入 events.jsonl。
    """
    _write(
        event_type="gate_proposal",
        category="timeout",
        action="proposal_timeout",
        domain="meta",
        trigger_reason=f"门禁提案超时（{timeout_seconds}秒），自动执行选项B",
        involved_l1_parts=["l1_orchestrator", "gate_proposal"],
        result="TIMEOUT",
        extra={
            "event_id": event_id,
            "timeout_seconds": timeout_seconds,
            "decision": decision,
            "auto_action": "execute_option_b"
        }
    )

def gate_proposal(task: str, domain: str, complexity: int) -> dict:
    """
    门禁提案生成。
    当 L1 需在铁律1/2覆盖范围外执行 terminal/execute_code/patch 时调用。
    返回: {"approved": bool, "route": str, "proposal_id": str, "timeout": int|None}
    """
    import time, random, string
    
    proposal_id = f"gp_{int(time.time())}_{''.join(random.choices(string.ascii_lowercase, k=4))}"
    
    if complexity < 3:
        timeout = 10
    elif complexity < 7:
        timeout = 30
    else:
        timeout = None  # 无超时（全角色调度必须等待用户明确输入）
    
    _write(
        event_type="gate_proposal",
        category="pending",
        action="proposal_created",
        domain=domain,
        trigger_reason=f"门禁提案等待用户确认（ID: {proposal_id}）",
        involved_l1_parts=["l1_orchestrator"],
        result="PENDING",
        extra={
            "proposal_id": proposal_id,
            "task_preview": task[:80],
            "complexity": complexity,
            "timeout_seconds": timeout
        }
    )
    
    return {
        "proposal_id": proposal_id,
        "complexity": complexity,
        "timeout": timeout,
        "task": task,
        "domain": domain,
        "approved": False,
        "route": f"L1→{domain}_orchestrator"
    }

# ─────────────────────────────────────────────────────────────────────────────
# B2-B5 补充门禁函数 — 结束
# ─────────────────────────────────────────────────────────────────────────────

def get_stats(days: int = 7) -> dict:
    """从 events.jsonl 读取近 N 小时的 soul_arbiter 事件并统计"""
    import os, time

    if not EVENTS_FILE.exists():
        return {"total": 0, "by_category": {}, "by_result": {}}

    cutoff = time.time() - since_hours * 3600
    stats = {"total": 0, "by_category": {}, "by_result": {}, "recent": []}

    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                    if ev.get("event") != "soul_arbiter":
                        continue
                    # 时间过滤
                    ts = ev.get("ts", "")
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if dt.timestamp() < cutoff:
                            continue
                    except Exception:
                        continue

                    stats["total"] += 1
                    arbiter = ev.get("arbiter", {})
                    cat = arbiter.get("category", "unknown")
                    res = arbiter.get("result", "unknown")
                    stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
                    stats["by_result"][res] = stats["by_result"].get(res, 0) + 1

                    if stats["total"] <= 10:
                        stats["recent"].append({
                            "ts": ts,
                            "category": cat,
                            "action": arbiter.get("action"),
                            "domain": arbiter.get("domain"),
                            "result": res,
                            "trigger_reason": arbiter.get("trigger_reason", "")[:80],
                        })
                except Exception:
                    continue
    except Exception:
        pass

    return stats
