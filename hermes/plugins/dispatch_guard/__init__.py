"""
dispatch_guard 插件 vFinal+vSoulArbiter+vL1IronClad(2026-05-23)
管道门禁：对 L1 直接调用的底层工具执行强制域归属检查和硬检查。
集成 Soul Arbiter 宪法仲裁，确保 BLOCK 结论真正被执行。

2026-05-23 修复：
- P0.6: 新增 _get_route_target() 函数，修复 NameError；skill_routing_rules 命中时真正拦截
- P1:   替换未定义的 _get_last_classification → _classify_task；补全 BLOCK 审计事件
- 铁律: skill_view/execute_code/write_file/delegate_task 等加入 AUDITED_TOOLS

生效场景：
  - 通过 hermes_dispatcher.py 路径的任务（hermes "任务"）
  - Web 端通过 app.py 调度的任务

Soul Arbiter 集成：
  - 对 L3 脚本执行进行宪法审计
  - BLOCK 结论强制执行，不得绕过
  - 移除所有后缀豁免逻辑

硬检查规则（优先级从高到低）：
 1. Soul Arbiter 审计（最高优先级，BLOCK 不可绕过）
 2. 编排域强制路由：任务被识别为 L2 编排域时直接 BLOCK
 3. 黑名单：投资建议/医疗诊断/文件删除等高危操作
 4. 跨域/多步/外部API 等复杂任务特征
"""
import sys
import os
import json
import logging
import re
import importlib.util
import uuid
import time as _time
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

HERMES_HOME = Path.home() / ".hermes"
EVENTS_FILE = HERMES_HOME / "events" / "events.jsonl"
PERSONA_ACLS_FILE = HERMES_HOME / "config" / "persona_acls.json"

# ── Persona ACL 缓存（延迟加载）────────────────────────────────────────────────
_persona_acls_cache = None


def _load_persona_acls() -> dict:
    """加载 persona ACLs 配置（带缓存）"""
    global _persona_acls_cache
    if _persona_acls_cache is not None:
        return _persona_acls_cache
    try:
        if PERSONA_ACLS_FILE.exists():
            _persona_acls_cache = json.loads(PERSONA_ACLS_FILE.read_text(encoding="utf-8"))
            logger.info(f"[dispatch_guard] Persona ACLs 已加载: {list(_persona_acls_cache.get('personas', {}).keys())}")
        else:
            _persona_acls_cache = {"personas": {}}
            logger.warning(f"[dispatch_guard] Persona ACLs 文件不存在: {PERSONA_ACLS_FILE}")
    except Exception as e:
        _persona_acls_cache = {"personas": {}}
        logger.error(f"[dispatch_guard] Persona ACLs 加载失败: {e}")
    return _persona_acls_cache


def _get_current_persona() -> str:
    """获取当前 persona（从环境变量 HERMES_PERSONA）"""
    return os.environ.get("HERMES_PERSONA", "")


def _get_persona_acl(persona: str) -> dict:
    """获取指定 persona 的 ACL 配置"""
    acls = _load_persona_acls()
    return acls.get("personas", {}).get(persona, {})


def _is_protected_path(path: str, persona: str) -> bool:
    """检查路径是否受保护（支持相对路径和绝对路径匹配）"""
    acl = _get_persona_acl(persona)
    if not acl:
        return False
    
    # 相对路径保护
    protected_rel = acl.get("protected_paths", [])
    path_obj = Path(path) if path else None
    if path_obj:
        path_str = str(path_obj)
        path_name = path_obj.name
        for protected in protected_rel:
            protected_name = Path(protected).name if "/" in protected or "\\" in protected else protected
            if protected.endswith("/") or protected.endswith("\\"):
                # 目录保护：检查路径是否以此目录开头
                if path_str.startswith(protected) or path_str.startswith(protected.rstrip("/\\")):
                    return True
            elif path_name == protected_name or path_str == protected:
                return True
    
    # 绝对路径模式保护（支持 glob 风格匹配，如 */.hermes/SOUL.md）
    protected_abs = acl.get("protected_absolute_patterns", [])
    abs_path = os.path.abspath(path) if path else ""
    for pattern in protected_abs:
        # 转换 */prefix -> 匹配任意中间路径
        regex_pattern = pattern.replace("*/", "[^/]*/")
        if re.search(regex_pattern, abs_path):
            return True
    
    return False


def _persona_gate(tool_name: str, tool_args: dict, user_task: str = "") -> dict:
    """
    Persona 权限门禁检查（小李模式）
    
    检查逻辑：
    1. 非小李用户：放行
    2. 小李使用禁用工具：拦截
    3. 小李写入受保护路径：拦截
    4. 小李触发 /yolo 或 /exit：拦截（通过 user_task 检测 slash 命令）
    """
    persona = _get_current_persona()
    
    # 非受限 persona：放行
    if persona != "xiaoli":
        return None
    
    acl = _get_persona_acl(persona)
    if not acl:
        return None
    
    # 检查禁用工具
    deny_tools = acl.get("deny_tools", [])
    if tool_name in deny_tools:
        _audit_event(
            "persona_acl_block",
            tool_name,
            user_task,
            "BLOCK",
            f"deny_tool:{tool_name}",
            persona=persona,
        )
        return {
            "action": "block",
            "message": (
                f"[PERSONA ACL] 小李角色禁止使用工具 【{tool_name}】\n"
                f"原因：{tool_name} 属于受限工具，仅小马（CEO）可用。\n"
                f"如需使用，请联系小马开通权限。"
            ),
        }
    
    # 检查受保护路径写入（write_file / patch）
    if tool_name in ("write_file", "patch"):
        path = tool_args.get("path", "") or tool_args.get("file_path", "")
        if path and _is_protected_path(path, persona):
            _audit_event(
                "persona_acl_block",
                tool_name,
                user_task,
                "BLOCK",
                f"protected_path:{path}",
                persona=persona,
            )
            return {
                "action": "block",
                "message": (
                    f"[PERSONA ACL] 小李角色禁止写入受保护路径 【{path}】\n"
                    f"原因：该路径属于核心配置文件（SOUL.md/config.yaml/scripts/plugins），仅小马（CEO）可修改。\n"
                    f"如需修改，请联系小马开通权限。"
                ),
            }
    
    # 检查禁用 slash 命令（通过 user_task 检测）
    deny_slash = acl.get("deny_slash_commands", [])
    task_lower = user_task.lower() if user_task else ""
    for cmd in deny_slash:
        if cmd.lower() in task_lower:
            _audit_event(
                "persona_acl_block",
                tool_name,
                user_task,
                "BLOCK",
                f"deny_slash_command:{cmd}",
                persona=persona,
            )
            return {
                "action": "block",
                "message": (
                    f"[PERSONA ACL] 小李角色禁止执行命令 【{cmd}】\n"
                    f"原因：{cmd} 可能绕过权限限制，仅小马（CEO）可用。\n"
                    f"如需使用，请联系小马开通权限。"
                ),
            }
    
    return None


# ── Soul Arbiter 审计结果枚举 ─────────────────────────────────────────────────
class ArbiterResult:
    """Soul Arbiter 审计结果等级"""
    PASS = "PASS"
    FLAG = "FLAG"
    BLOCK = "BLOCK"
    ADVISORY = "ADVISORY"


# ── 审计工具列表 ──────────────────────────────────────────────────────────────
# L1 不得直接调用的核心工具：所有涉及外部 API 调用、文件写入、代码执行、skill 加载的工具
# 必须经过编排器。skill_view 在内——L1 加载 skill 知识后不得直接执行，必须走 L2。
_AUDITED_TOOLS = frozenset({
    "terminal", "execute_code", "write_file", "patch",
    "skill_view", "skill_manage", "skills_list",
    "delegate_task", "browser_navigate", "browser_click",
})

# 门禁放行令牌池（approved_op_token → True 时直接放行）
approved_ops = {}              # token → True
_approved_op_timestamps = {}  # token → 创建时间
_APPROVED_OP_TTL = 300       # 秒

# ── 黑名单关键词（高危操作，直接 BLOCK）───────────────────────────────────────
_BLACKLIST_KEYWORDS = [
    "投资建议", "应该买", "该买", "推荐股票", "选股",
    "医疗诊断", "治疗方案", "开药", "手术", "处方",
    "删除文件", "rm -rf", "drop table", "truncate",
    "修改系统配置", "chmod 777",
]

# ── 多步骤指示词 ──────────────────────────────────────────────────────────────
_MULTI_STEP_KEYWORDS = ["然后", "接着", "再", "并", "生成", "首先", "其次"]

# ── 外部 API 关键词 ───────────────────────────────────────────────────────────
_EXTERNAL_API_KEYWORDS = ["查询", "实时", "API", "fetch", "curl", "wget"]


# ═══════════════════════════════════════════════════════════════════════════════
# Soul Arbiter 集成模块
# ═══════════════════════════════════════════════════════════════════════════════

# Soul Arbiter 单例（延迟加载）
_arbiter_instance = None



# ═══════════════════════════════════════════════════════════════════════════════
# DIAGNOSTIC BYPASS — 只读探查放行通道
# 诊断命令（curl/cat/ls/head/grep/echo/wc/find/which/ps/df/du）不放行写入操作
# 和安装操作，仅允许纯只读探查。放行时写入 diagnostic_bypass 事件日志。
# ═══════════════════════════════════════════════════════════════════════════════

DIAGNOSTIC_COMMANDS = frozenset({
    'curl', 'cat', 'ls', 'head', 'grep', 'echo', 'wc', 'find', 'which',
    'ps', 'df', 'du', 'stat', 'file', 'uname', 'hostname', 'env', 'printenv'
})
WRITE_OPS = {'>', '>>', '|', 'tee'}
INSTALL_CMDS = frozenset({'apt', 'apt-get', 'pip', 'pip3', 'npm', 'yum', 'dnf', 'brew', 'snap'})


# Path traversal patterns that indicate cross-domain or out-of-scope access
_PATH_TRAVERSAL_PATTERNS = (
    "..",          # path traversal sequences
    "/etc/",       # system config files
    "/root/",      # root home directory
    "/proc/",      # proc filesystem
    "/sys/",       # sys filesystem
    "/boot/",      # boot directory
    "/.ssh/",      # SSH keys
    "/.gnupg/",    # GPG keys
    "C:\\",        # Windows absolute path
    "D:\\",        # Windows absolute path
    "%USERPROFILE%",   # Windows user profile env var
    "%APPDATA%",       # Windows app data env var
    "%PROGRAMDATA%",   # Windows program data env var
)


def _is_diagnostic_command(function_name, function_args):
    """Return (is_diagnostic, reason_str)."""
    if function_name not in ("terminal", "execute_code"):
        return False, None
    cmd = str(function_args.get("command", ""))
    if not cmd.strip():
        return False, None

    # P0.6 Bug3 fix: reject path traversal attempts before any other check
    cmd_normalized = cmd.strip()
    for pattern in _PATH_TRAVERSAL_PATTERNS:
        if pattern in cmd_normalized:
            return False, f"path_traversal_rejected:{pattern}"

    cmd_lower = cmd_normalized.lower()
    first_word = cmd_lower.split()[0] if cmd_lower.split() else ""

    if first_word not in DIAGNOSTIC_COMMANDS:
        return False, None
    if any(op in cmd for op in WRITE_OPS):
        return False, None
    if first_word in INSTALL_CMDS:
        return False, None
    return True, f"diagnostic_readonly:{first_word}"


def _write_diagnostic_bypass_event(tool_name, command, reason):
    """Write diagnostic_bypass event to events.jsonl."""
    try:
        import json
        from pathlib import Path
        from datetime import datetime, timezone
        events_file = Path.home() / ".hermes" / "events" / "events.jsonl"
        events_file.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "diagnostic_bypass",
            "tool": tool_name,
            "command_preview": command[:120],
            "bypass_reason": reason,
        }
        with open(events_file, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _get_soul_arbiter():
    """
    获取 Soul Arbiter 单例（延迟加载，避免循环导入）
    
    Soul Arbiter 职责：
    1. 对 L3 脚本进行宪法审计
    2. 检查 SKILL.md 的 P0 规则合规性
    3. BLOCK 结论不可绕过
    """
    global _arbiter_instance
    if _arbiter_instance is None:
        try:
            sys.path.insert(0, str(HERMES_HOME / "soul"))
            # 直接加载 _soul_arbiter.py 获取 SoulArbiter 类
            spec = importlib.util.spec_from_file_location(
                "_soul_arbiter",
                HERMES_HOME / "soul" / "_soul_arbiter.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _arbiter_instance = module.SoulArbiter()
            logger.info("[dispatch_guard] Soul Arbiter 加载成功")
        except Exception as e:
            logger.warning(f"[dispatch_guard] Soul Arbiter 加载失败: {e}")
            _arbiter_instance = None
    return _arbiter_instance


def _detect_l3_script_from_task(task: str, tool_name: str, tool_args: dict) -> Optional[str]:
    """
    从任务和工具参数中检测 L3 脚本路径
    
    检测逻辑：
    1. 从 tool_args 中查找脚本路径（如 'skill_path', 'path', 'script'）
    2. 从 task 中提取文件名模式
    3. 识别 l3_*.py 或 *_skill.py 模式
    
    Args:
        task: 用户任务原文
        tool_name: 调用的工具名称
        tool_args: 工具参数
        
    Returns:
        检测到的 L3 脚本路径，或 None
    """
    # 路径字段映射
    path_fields = ["skill_path", "path", "script", "file", "script_path", "target"]
    
    # 1. 从 tool_args 中查找
    for field in path_fields:
        if field in tool_args:
            path = str(tool_args[field])
            if _is_l3_script_path(path):
                return path
    
    # 2. 从 task 中提取文件名
    l3_pattern = r'(l3_[a-z_]+\.py|[a-z]+-skill\.py|skill_[a-z_]+\.py)'
    match = re.search(l3_pattern, task, re.IGNORECASE)
    if match:
        filename = match.group(1)
        # 尝试在 scripts 目录查找
        scripts_dir = HERMES_HOME / "scripts"
        if scripts_dir.exists():
            for f in scripts_dir.glob(f"*{filename}*"):
                if f.suffix == ".py":
                    return str(f)
    
    return None


def _is_l3_script_path(path: str) -> bool:
    """判断路径是否指向 L3 脚本"""
    if not path:
        return False
    path_lower = path.lower()
    # L3 脚本特征：l3_*.py, *-skill.py, skill_*.py
    patterns = [
        r'/l3_[a-z_]+\.py$',
        r'/[a-z]+-skill\.py$',
        r'/skill_[a-z_]+\.py$',
        r'\\l3_[a-z_]+\.py$',
        r'\\[a-z]+-skill\.py$',
        r'\\skill_[a-z_]+\.py$',
    ]
    for p in patterns:
        if re.search(p, path_lower):
            return True
    return False


def _detect_skill_from_task(task: str, tool_args: dict) -> Optional[tuple]:
    """
    从任务中检测 SKILL.md 路径
    
    Returns:
        (skill_name, skill_path) 或 None
    """
    # skill 路径字段
    skill_fields = ["skill_name", "skill", "name"]
    
    # 1. 从 tool_args 中查找
    for field in skill_fields:
        if field in tool_args:
            skill_name = str(tool_args[field])
            # 构建标准 skill 路径
            skill_path = HERMES_HOME / "skills" / skill_name / "SKILL.md"
            if skill_path.exists():
                return (skill_name, str(skill_path))
    
    # 2. 从 task 中提取 skill 名称
    skill_pattern = r'([a-z]+-[a-z]+(?:-[a-z]+)?)'
    matches = re.findall(skill_pattern, task.lower())
    for name in matches:
        if name not in ("hermes-agent", "dispatch-guard"):
            skill_path = HERMES_HOME / "skills" / name / "SKILL.md"
            if skill_path.exists():
                return (name, str(skill_path))
    
    return None


def _soul_arbiter_gate(tool_name: str, tool_args: dict, user_task: str) -> Optional[dict]:
    """
    Soul Arbiter 宪法仲裁门禁（最高优先级）
    
    功能：
    1. 检测任务是否涉及 L3 脚本或 SKILL.md
    2. 调用 Soul Arbiter 进行宪法审计
    3. BLOCK 结论强制执行，不可绕过
    
    Returns:
        None 表示放行，返回 dict 表示拦截
    """
    arbiter = _get_soul_arbiter()
    if arbiter is None:
        logger.warning("[dispatch_guard] Soul Arbiter 不可用，跳过宪法审计")
        return None
    
    # ── 检测是否涉及 L3 脚本 ────────────────────────────────────────────────
    l3_script_path = _detect_l3_script_from_task(user_task, tool_name, tool_args)
    
    # ── 检测是否涉及 SKILL.md ───────────────────────────────────────────────
    skill_info = _detect_skill_from_task(user_task, tool_args)
    
    # ── 执行审计 ────────────────────────────────────────────────────────────
    audit_result = None
    audit_type = None
    
    if l3_script_path:
        # L3 脚本审计（Python 脚本安全与语法审计）
        try:
            audit_result = arbiter.py_audit(l3_script_path, {
                "tool_name": tool_name,
                "user_task": user_task,
                "source": "dispatch_guard",
            })
            audit_type = "py_audit"
            logger.info(f"[dispatch_guard] Soul Arbiter py_audit: {l3_script_path}")
        except Exception as e:
            logger.error(f"[dispatch_guard] Soul Arbiter py_audit 失败: {e}")
            # 审计失败时保守处理：放行但记录警告
            return None
    
    elif skill_info:
        # SKILL.md P0 审计
        skill_name, skill_path = skill_info
        try:
            audit_result = arbiter.skill_audit(skill_name, skill_path, {
                "tool_name": tool_name,
                "user_task": user_task,
                "source": "dispatch_guard",
            })
            audit_type = "skill_audit"
            logger.info(f"[dispatch_guard] Soul Arbiter skill_audit: {skill_name}")
        except Exception as e:
            logger.error(f"[dispatch_guard] Soul Arbiter skill_audit 失败: {e}")
            # 审计失败时保守处理：放行但记录警告
            return None
    
    # ── 处理审计结果 ─────────────────────────────────────────────────────────
    if audit_result is None:
        return None
    
    level = audit_result.get("verdict", "PASS")
    notes = audit_result.get("notes", [])
    
    # ═══════════════════════════════════════════════════════════════════════
    # 【核心修复】BLOCK 结论强制执行，移除所有豁免逻辑
    # ═══════════════════════════════════════════════════════════════════════
    if level == ArbiterResult.BLOCK:
        # BLOCK 结论：强制拦截，记录完整审计日志
        _audit_event(
            "soul_arbiter_block",
            tool_name,
            user_task,
            "BLOCK",
            f"soul_arbiter_{audit_type}_block",
            audit_level=level,
            audit_notes=notes,
            audit_type=audit_type,
            audit_target=audit_result.get("script_path") or audit_result.get("skill_name", ""),
        )
        _token = str(uuid.uuid4())[:16]
        approved_ops[_token] = True
        _approved_op_timestamps[_token] = _time.time()
        return {
            "action": "block",
            "message": (
                f"[SOUL ARBITER] 宪法审计否决（{audit_type}）\n"
                f"原因：{'；'.join(notes) if notes else 'P0规则违反'}\n"
                f"目标：{audit_result.get('script_path') or audit_result.get('skill_name', 'unknown')}\n"
                f"必须修复后重新提交。"
            ),
            "approved_op_token": _token,
        }
    
    # FLAG/ADVISORY：记录但不拦截
    if level in (ArbiterResult.FLAG, ArbiterResult.ADVISORY):
        _audit_event(
            "soul_arbiter_flag",
            tool_name,
            user_task,
            "FLAG",
            f"soul_arbiter_{audit_type}_flag",
            audit_level=level,
            audit_notes=notes,
            audit_type=audit_type,
        )
        # 可选：FLAG 时也拦截（严格模式）
        # return {"action": "block", "message": f"[SOUL ARBITER] 警告：{'；'.join(notes)}"}
    
    # PASS：放行
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 原有门禁逻辑（保持不变）
# ═══════════════════════════════════════════════════════════════════════════════

# ── 辅助函数：获取编排器上下文状态 ────────────────────────────────────────────
def _is_orchestrator_context() -> bool:
    try:
        hm = sys.modules.get("hermes_dispatcher")
        if hm:
            return getattr(hm, "_in_orchestrator_context", False)
    except Exception:
        pass
    return False


# ── 辅助函数：实时意图识别 ─────────────────────────────────────────────────────
def _classify_task(task: str):
    """调用系统的 classify_intent 获取域归属和置信度，失败时使用启发式兜底"""
    try:
        sys.path.insert(0, str(HERMES_HOME / "scripts"))
        from l1_intent_router import classify_intent
        return classify_intent(task)
    except Exception:
        # P0-FIX: 降级时使用启发式域检测，而非静默返回 unknown
        task_lower = task.lower()
        domain_keywords = {
            "investment": ["股票", "估值", "投资", "年报", "现金流", "复利", "安全边际"],
            "construction": ["图纸", "施工", "预算", "结构", "CAD", "混凝土", "BIM", "机电"],
            "ecommerce": ["电商", "店铺", "SKU", "流量", "发货", "DSR", "Shopify", "直播"],
            "life": ["旅游", "美食", "酒店", "健身", "行程", "攻略"],
            "multimodal": ["PPT", "Word", "PDF", "图片", "视频", "排版", "文档", "报告",
                           "JSX", "jsx", "React", "Vue", "前端", "UI", "组件", "样式",
                           "App.jsx", "App.css", "index.jsx", "index.css"],
            "strategy": ["战略", "项目管理", "Sprint", "Jira", "财务追踪"],
            "it": ["代码", "API", "架构", "Bug", "前端", "后端", "数据库"],
            "game": ["游戏", "关卡", "角色", "皮肤"],
        }
        for domain, keywords in domain_keywords.items():
            for kw in keywords:
                if kw in task_lower:
                    return domain, 0.60
        return "it", 0.55


# ── 辅助函数：动态获取编排域触发词 ─────────────────────────────────────────────
def _get_orchestrator_domains_with_triggers() -> tuple[set[str], dict[str, list[str]]]:
    """动态获取所有编排域及其触发词"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from task_classifier import get_all_orchestrator_trigger_words
        triggers = get_all_orchestrator_trigger_words()
        domains = set(triggers.keys())
        return domains, triggers
    except Exception as e:
        logger.warning(f"[dispatch_guard] 动态读取触发词失败，降级到启发式检测: {e}")
        return {"construction", "investment", "ecommerce", "life",
                "multimodal", "it", "game", "strategy"}, {}


def _get_orchestrator_domains() -> set:
    """
    获取 L2编排器域集合（P1 强制路由用）。
    
    优先级：
      1. hermes_dispatcher._ORCHESTRATOR_DOMAINS（已初始化时）
      2. l2_registry_loader._ORCHESTRATOR_DOMAINS（备用路径）
      3. 硬编码兜底（永不返回空集）
    """
    # 优先路径：从 hermes_dispatcher 读（已初始化时有内容）
    try:
        hm = sys.modules.get("hermes_dispatcher")
        if hm is not None:
            od = getattr(hm, "_ORCHESTRATOR_DOMAINS", None)
            if od and len(od) > 0:
                return od
    except Exception:
        pass
    # 备用路径：从 l2_registry_loader 读
    try:
        import sys as _sys
        _scripts = str(Path(__file__).parent.parent / "scripts")
        if _scripts not in _sys.path:
            _sys.path.insert(0, _scripts)
        import l2_registry_loader as _l2_reg
        _l2_reg._ensure_l2_loaded()
        _l2_mod = _sys.modules.get("l2_registry_loader")
        _od = getattr(_l2_mod, "_ORCHESTRATOR_DOMAINS", None) if _l2_mod else None
        if _od and len(_od) > 0:
            return _od
    except Exception:
        pass
    # 硬编码兜底：永不返回空集（确保 P1 检查始终有效）
    return {
        "construction", "ecommerce", "investment",
        "it", "life", "multimodal", "meta",
        "strategy", "game", "academic",
    }


# ── L2 域关键词加载（供 P3 跨域检测使用）────────────────────────────
_L2_DOMAIN_KEYWORDS = None

def _get_l2_domain_keywords() -> dict:
    """延迟加载 L2 域关键词（供 _detect_cross_domain 使用）"""
    global _L2_DOMAIN_KEYWORDS
    if _L2_DOMAIN_KEYWORDS is not None:
        return _L2_DOMAIN_KEYWORDS
    
    # 从 skill_routing_rules.json 提取所有 trigger 词
    rules_path = HERMES_HOME / "config" / "skill_routing_rules.json"
    if rules_path.exists():
        try:
            rules = json.loads(rules_path.read_text(encoding="utf-8"))
            kw_map = {}
            for rule in rules:
                target = rule.get("route_target", "")
                triggers = rule.get("triggers", [])
                if target and triggers:
                    if target not in kw_map:
                        kw_map[target] = []
                    kw_map[target].extend([t for t in triggers if isinstance(t, str)])
            _L2_DOMAIN_KEYWORDS = kw_map
            return _L2_DOMAIN_KEYWORDS
        except Exception:
            pass
    
    _L2_DOMAIN_KEYWORDS = {}
    return _L2_DOMAIN_KEYWORDS


# P3: 跨域检测 ─────────────────────────────────────────────────────────
def _detect_cross_domain(task: str) -> bool:
    """
    硬检查：跨域信号。匹配2+不同L2域 → True。
    用于 P3 拦截：多域任务必须走编排器协调。
    """
    if not task:
        return False
    task_lower = task.lower()
    matched = set()
    for domain, keywords in _get_l2_domain_keywords().items():
        for kw in keywords:
            if kw.lower() in task_lower:
                matched.add(domain)
                break
    return len(matched) >= 2


# P4: 多步骤检测 ──────────────────────────────────────────────────────
_STEP_SEPARATORS = ["并", "然后", "接着", "再", "生成", "；", ";"]

def _detect_multi_step(task: str) -> bool:
    """
    硬检查：多步骤信号。3+独立步骤 → True。
    用于 P4 拦截：复杂任务必须走编排器分步执行。
    """
    if not task:
        return False
    parts = [task]
    for sep in _STEP_SEPARATORS:
        new_parts = []
        for part in parts:
            new_parts.extend(part.split(sep))
        parts = new_parts
    meaningful = [p.strip() for p in parts if len(p.strip()) >= 2]
    return len(meaningful) >= 3


# P2: 外部API检测 ─────────────────────────────────────────────────────
_EXTERNAL_API_KEYWORDS = [
    "实时", "当前", "今日", "此时此刻", "now", "live",
    "最新价格", "当前价格", "最新行情", "实时行情",
    "查一下", "查询", "获取最新", "拉取",
    "API", "api", "http", "https", "调用",
    "网页", "网站", "数据库", "DB", "db",
    "行情", "交易", "价格走势", "K线", "分时",
    "资金流向", "北向资金", "融资融券", "龙虎榜",
]

def _detect_external_api(task: str) -> bool:
    """
    硬检查：外部API调用信号。实时数据/外部服务 → True。
    用于 P2 拦截：外部数据获取必须走编排器的外部调用规范。
    """
    if not task:
        return False
    task_lower = task.lower()
    return any(kw in task_lower for kw in _EXTERNAL_API_KEYWORDS)


# P1/P4: 黑名单检测 ────────────────────────────────────────────────────
_TOOL_CALL_BLACKLIST = [
    "买", "卖", "建仓", "加仓", "减仓", "清仓", "持仓",
    "投资建议", "应该买", "该买", "推荐股票", "选股", "买哪个",
    "买哪只", "要不要买", "要不要卖", "要不要建仓",
    "推荐一支", "哪支股票", "股票推荐", "选哪只", "股票哪个",
    "诊断", "患有", "确诊", "ct显示", "肿瘤", "癌症",
    "治疗方案", "开药", "手术", "处方",
    "删除", "删", "删除文件", "删除所有", "删除日志", "清空日志",
    "rm -rf", "rm -r", "rm -f",
    "nginx", "apache", "docker-compose", "systemd",
    "crontab", "服务配置", "修改配置", "更改配置",
    "Kubernetes", "k8s", "集群管理", "自动扩缩容",
    "CI/CD", "流水线配置", "部署一套", "部署系统",
    "集群", "负载均衡", "反向代理",
]

def _is_blacklisted(task: str) -> bool:
    """
    黑名单检查：投资建议/医疗诊断/文件删除/系统配置。
    命中 → 必须走提案确认，不得直接执行。
    """
    if not task:
        return False
    task_lower = task.lower()
    for kw in _TOOL_CALL_BLACKLIST:
        if kw.lower() in task_lower:
            return True
    return False


def _match_domain_by_triggers(task: str, triggers: dict[str, list[str]]) -> str | None:
    """用触发词匹配任务，返回匹配的域名称"""
    task_lower = task.lower()
    for domain, words in triggers.items():
        for word in words:
            if word in task_lower:
                return domain
    return None


# ── 辅助函数：审计事件写入 ─────────────────────────────────────────────────────
def _audit_event(event_type: str, tool_name: str, task: str,
                 decision: str, blocked_reason: str = "", **kwargs) -> None:
    """写入拦截/放行事件到 events.jsonl（fire-and-forget）"""
    try:
        event = {
            "ts": __import__("datetime").datetime.now().isoformat(),
            "event": event_type,
            "tool": tool_name,
            "task_preview": task[:80] if task else "",
            "decision": decision,
            "blocked_reason": blocked_reason,
            **kwargs,
        }
        EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EVENTS_FILE, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── 辅助函数：基于 skill_routing_rules.json 的域路由 ───────────────────────────
def _get_route_target(user_task: str) -> Optional[str]:
    """
    读取 skill_routing_rules.json，查找 route_mode=delegate_to_primary 且
    route_target 指向编排域的规则，返回对应的 route_target（域）。

    匹配评分规则：关键词越长分数越高，避免短词（如"文档"）覆盖长词（如"Word文档"）。

    用于 P0.6：skill_routing_rules.json 中明确声明要走编排器的域，
    在 pre_tool_call 阶段提前拦截，避免 L1 直接调用底层工具。

    Returns:
        域名字符串（如 "multimodal"），或 None（无匹配规则）
    """
    if not user_task:
        return None
    task_lower = user_task.lower()
    rules_path = HERMES_HOME / "config" / "skill_routing_rules.json"
    if not rules_path.exists():
        return None
    try:
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    best_score = 0
    best_target = None
    for rule in rules:
        if rule.get("route_mode") != "delegate_to_primary":
            continue
        route_target = rule.get("route_target")
        if not route_target:
            continue
        triggers = rule.get("triggers", [])
        for kw in triggers:
            if isinstance(kw, str) and kw.lower() in task_lower:
                # 关键词越长越优先（避免"文档"覆盖"Word文档"）
                score = len(kw)
                if score > best_score:
                    best_score = score
                    best_target = route_target
    return best_target


# ── 辅助函数：当前工具调用是否已获得编排域授权 ─────────────────────────────────
def _is_orch_authorized(tool_name: str, tool_args: dict, user_task: str) -> bool:
    """
    检查本次工具调用是否在编排器上下文中执行（已被 L2 编排器放行）。

    判断依据：
    1. hermes_dispatcher 模块的 _in_orchestrator_context 标志
    2. 工具参数中携带 approved_op_token 且在有效期内
    3. user_task 中包含门禁放行标记
    """
    # 路径1：dispatcher 编排上下文标志
    try:
        hm = sys.modules.get("hermes_dispatcher")
        if hm is not None:
            val = getattr(hm, "_in_orchestrator_context", False)
            if val:
                return True
    except Exception:
        pass

    # 路径2：approved_op_token（门禁提案已批准）
    try:
        opq = kwargs.get("opaque_args") or {}
        token = opq.get("approved_op_token") or ""
        if token and token in approved_ops:
            ts = _approved_op_timestamps.get(token)
            if ts is not None and _time.time() - ts <= _APPROVED_OP_TTL:
                return True
    except Exception:
        pass

    # 路径3：user_task 中的门禁放行标记
    if user_task and "门禁放行" in user_task:
        return True

    return False


# ── 提案构建器 ────────────────────────────────────────────────────────────────
def _build_proposal(
    tool_name: str,
    task: str,
    blocked_reason: str,
    domain: str = None,
    suggestion: str = None,
    reason: str = None,
) -> dict:
    """构建门禁提案返回给 pre_tool_call hook。

    pre_tool_call hook 的返回值会被 get_pre_tool_call_block_message() 消费，
    它只识别 {"action": "block", "message": str} 格式。
    所以这里把完整的结构化信息序列化成 user-facing message 返回。
    """
    lines = [f"【L1越级操作拦截】"]
    if domain:
        lines.append(f"域: {domain}")
    lines.append(f"工具: {tool_name}")
    if reason:
        lines.append(f"原因: {reason}")
    if suggestion:
        lines.append(f"建议: {suggestion}")
    lines.append(f"blocked_reason: {blocked_reason}")

    return {
        "action": "block",
        "message": "\n".join(lines),
    }


def _trigger_it_evolution_proposal(task: str, reason: str) -> None:
    """触发 IT 自进化提案 — 编排器内 L1 越权调用时通知 IT 部门补建链路。"""
    try:
        import datetime
        HERMES_HOME = Path.home() / ".hermes"
        EVENTS_DIR = HERMES_HOME / "events"
        EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        events_file = EVENTS_DIR / "events.jsonl"
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "it_evolution_proposal",
            "category": "l1_orchestrator_bypass",
            "action": "propose",
            "task_preview": task[:100],
            "reason": reason,
            "involved_l1_parts": ["_pipeline_tool_gate", "_trigger_it_evolution_proposal"],
        }
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(__import__("json").dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # 写事件失败不影响主流程，静默忽略
        pass


# ── 核心门禁：_pipeline_tool_gate ──────────────────────────────────────────────
def _pipeline_tool_gate(tool_name: str, tool_args: dict, user_task: str = "", **kwargs) -> dict:
    # G0: 共享变量
    _DG_SELF = str(Path.home() / ".hermes" / "plugins" / "dispatch_guard")
    _DG_SELF_NEW = str(Path.home() / ".hermes" / "hermes-agent" / "plugins" / "dispatch-guard")
    _opq = kwargs.get("opaque_args") or {}
    _ta = _opq.get("tool_args") or {}
    _fp = _ta.get("path") or _ta.get("file_path") or ""

    # G1 全域自修白名单
    _task_lower = user_task.lower() if user_task else ""
    _dg_path_hit = (
        (_fp and (os.path.abspath(_fp).startswith(_DG_SELF) or os.path.abspath(_fp).startswith(_DG_SELF_NEW)))
        or ("dispatch-guard" in _task_lower and "/plugins/dispatch" in _task_lower)
        or ("dispatch_guard" in _task_lower and "/plugins/dispatch" in _task_lower)
    )
    if _dg_path_hit:
        _audit_event(
            "l1_direct_tool_call", tool_name, user_task,
            "AUDIT_PASS", blocked_reason="g1_self_exempt",
        )
        return None

    # G0: 放行令牌检查（带TTL过期清理）
    _token = _opq.get("approved_op_token") or ""
    if _token and _token in approved_ops:
        ts = _approved_op_timestamps.get(_token)
        if ts is not None and _time.time() - ts <= _APPROVED_OP_TTL:
            return None
        approved_ops.pop(_token, None)
        _approved_op_timestamps.pop(_token, None)

    # P0: Soul Arbiter
    arbiter_block = _soul_arbiter_gate(tool_name, tool_args, user_task)
    if arbiter_block is not None:
        return arbiter_block

    # P0.5: Skill Routing Rule（架构级约束）— 命中 route_mode=delegate_to_primary 的域，直接提案拦截
    # 优先检查编排器上下文：编排器内部的工具调用必须在 P0.5 就放行，
    # 否则 L2 编排器调用的底层工具（terminal/execute_code 等）会在 P0.5 被误 BLOCK。
    _in_orch_before_p05 = _is_orchestrator_context()
    _route_target = _get_route_target(user_task)
    if _route_target and not _in_orch_before_p05:
        # 逃生舱：HERMES_BYPASS=1 可以绕过 P0.5（仅用于紧急自检）
        if os.environ.get("HERMES_BYPASS") == "1":
            _audit_event(
                "l1_direct_tool_call", tool_name, user_task,
                "BYPASS", f"skill_routing_rule:{_route_target}:hermes_bypass",
            )
            return None  # 紧急逃生，不走门禁

        # 正常拦截：域命中即拦截（无编排器存在检查）
        _audit_event(
            "l1_direct_tool_call", tool_name, user_task,
            "BLOCK", f"skill_routing_rule_match:{_route_target}",
        )
        return _build_proposal(
            tool_name=tool_name,
            task=user_task,
            blocked_reason="skill_routing_rule",
            domain=_route_target,
            suggestion=f"该任务属于【{_route_target}】域，必须通过 L2 编排器执行",
            reason=f"skill_routing_rules.json 声明 '{_route_target}' 域必须走 delegate_to_primary 模式，不允许 L1 直接调用底层工具",
        )

    # P0.6: Diagnostic Bypass（工具级豁免，次优先）— 只读诊断命令可绕过
    is_diag, diag_reason = _is_diagnostic_command(tool_name, tool_args)
    if is_diag:
        _write_diagnostic_bypass_event(tool_name, str(tool_args.get("command", ""))[:120], diag_reason)
        return None

    # P1: 编排域强制路由
    in_orch = False
    try:
        hm = sys.modules.get("hermes_dispatcher")
        if hm is not None:
            in_orch = getattr(hm, "_in_orchestrator_context", False) or False
    except Exception:
        pass
    if not in_orch:
        # 实时意图识别（内部有兜底，不会抛异常）
        real_domain, real_confidence = _classify_task(user_task)
        orch_domains = _get_orchestrator_domains()
        if real_domain in orch_domains and real_confidence >= 0.60:
            _audit_event(
                "l1_direct_tool_call", tool_name, user_task,
                "BLOCK", f"domain_orchestrator_gate:{real_domain}",
            )
            return _build_proposal(
                tool_name=tool_name,
                task=user_task,
                blocked_reason="domain_task_must_use_orchestrator",
                domain=real_domain,
                suggestion="走L1->L2链路",
                reason=f"域归属为'{real_domain}'（置信度{real_confidence}），该域存在编排器，必须通过L2编排器执行",
            )

    # P2-P5: 其余硬检查
    task_lower = user_task.lower() if user_task else ""
    hit_blacklist = _is_blacklisted(user_task)
    hit_cross = _detect_cross_domain(user_task)
    hit_multi = _detect_multi_step(user_task)
    hit_api = _detect_external_api(user_task)

    any_hard_hit = hit_blacklist or hit_cross or hit_multi or hit_api
    hard_check_names = [n for n, v in [
        ("blacklist", hit_blacklist),
        ("cross_domain", hit_cross),
        ("multi_step", hit_multi),
        ("external_api", hit_api),
    ] if v]

    # 场景A：编排器上下文
    if in_orch:
        if any_hard_hit:
            reason_str = "|".join(hard_check_names)
            _audit_event(
                "l1_orchestrator_bypass", tool_name, user_task,
                "FLAG", blocked_reason=reason_str,
                hard_check=reason_str,
            )
            _trigger_it_evolution_proposal(
                user_task,
                f"编排器内L1越权调用，命中硬检查: {reason_str}",
            )
            return None
        else:
            _audit_event(
                "l1_direct_tool_call", tool_name, user_task,
                "AUDIT_PASS", blocked_reason="orchestrator_context",
            )
            return None

    # 场景B：非编排器上下文
    if hit_blacklist:
        _audit_event(
            "l1_direct_tool_call", tool_name, user_task,
            "BLOCK", blocked_reason="blacklist",
        )
        return _build_proposal(
            tool_name=tool_name,
            task=user_task,
            blocked_reason="blacklist",
            suggestion="使用 /plan 通过调度器执行",
            reason="任务涉及敏感操作（投资建议/医疗诊断/文件删除/系统配置），不允许直接调用工具",
        )

    if hit_cross:
        _audit_event(
            "l1_direct_tool_call", tool_name, user_task,
            "BLOCK", blocked_reason="cross_domain",
            hard_check="cross_domain",
        )
        return _build_proposal(
            tool_name=tool_name,
            task=user_task,
            blocked_reason="cross_domain",
            suggestion="使用 /plan 明确主责域后走L1->L2链路",
            reason="任务跨多个专业域，必须通过L2编排器协调执行",
        )

    if hit_multi:
        _audit_event(
            "l1_direct_tool_call", tool_name, user_task,
            "BLOCK", blocked_reason="multi_step",
            hard_check="multi_step",
        )
        return _build_proposal(
            tool_name=tool_name,
            task=user_task,
            blocked_reason="multi_step",
            suggestion="使用 /plan 拆解任务后分步执行",
            reason="任务包含3个以上独立步骤，必须通过编排器协调",
        )

    if hit_api:
        _audit_event(
            "l1_direct_tool_call", tool_name, user_task,
            "BLOCK", blocked_reason="external_api",
            hard_check="external_api",
        )
        return _build_proposal(
            tool_name=tool_name,
            task=user_task,
            blocked_reason="external_api",
            suggestion="使用 /plan 通过调度器调用外部API",
            reason="任务涉及外部API调用，必须通过编排器执行",
        )

    return None


# ── Hook 入口：pre_tool_call ───────────────────────────────────────────────────
def pre_tool_call(tool_name: str, args: dict = None, user_task: str = "", **kwargs) -> dict:
    """pre_tool_call hook — 工具调用前置门禁"""
    # P0: Persona ACL 检查（小李权限隔离，最高优先级）
    tool_args = args or {}
    task_text = user_task or kwargs.get("user_task", "") or kwargs.get("task", "")
    persona_block = _persona_gate(tool_name, tool_args, task_text)
    if persona_block is not None:
        return persona_block
    
    if tool_name not in _AUDITED_TOOLS:
        return None
    return _pipeline_tool_gate(tool_name, tool_args, task_text)


# ── 插件注册 ──────────────────────────────────────────────────────────────────
def register(context):
    """插件入口：注册 pre_tool_call hook 到系统钩子机制"""
    context.register_hook("pre_tool_call", pre_tool_call)
