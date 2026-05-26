import json
import sys
from pathlib import Path
from functools import lru_cache

# ── 路径常量 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR.parent / "config" / "cross_domain_rules.json"


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    """加载跨部门规则配置（缓存，只读一次）"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def coordinate(task: str, content_domain: str = "unknown") -> dict:
    """
    跨领域协调。
    content_domain: detect_content_domain 检测到的内容类型
      - trading   → 强制投资域
      - code_tech → 强制IT域
      - document  → 强制多模态域
      - life_decision → 强制生活域
      - analysis_report → 走原有分析报告规则
    """
    domains = detect_domains(task)

    if not domains:
        result = _empty_domains_result()
        result["content_domain"] = content_domain
        return result

    explicit = check_explicit_conflict(task)
    if explicit:
        result = _handle_explicit(explicit, domains)
        result["content_domain"] = content_domain
        return result

    # ── ① 内容主导规则优先 ──────────────────────────────────────────────
    if content_domain != "unknown":
        content_override = _apply_content_dominant_map(content_domain, domains)
        if content_override:
            result = {
                "is_cross_domain": True,
                "domains": [d[0] for d in domains],
                "primary": content_override["primary"],
                "supporting": content_override.get("supporting", []),
                "data_flow": content_override.get("reason", ""),
                "conflict": False,
                "conflict_reason": "",
                "suggestion": f"[内容主导] {content_override.get('reason', '')}",
                "content_domain": content_domain,
                "content_override": True,
            }
            return result
        # ── Bug D 单域检测错误特殊处理 ───────────────────────────────────
        # "杭州三日游"被 detector→it，但 content_domain=life_decision
        # 单域+content_domain冲突 → 触发 L1 裁决，不应用错误的 detector 结果
        if len(domains) == 1:
            forced_domain = _load_rules().get("content_type_rules", {}).get("content_dominant_map", {}).get(content_domain, {}).get("always_domain")
            if forced_domain and forced_domain not in [d[0] for d in domains]:
                result = {
                    "is_cross_domain": True,
                    "domains": [d[0] for d in domains],
                    "primary": None,  # 需要 L1 裁决
                    "supporting": [],
                    "data_flow": "",
                    "conflict": False,
                    "conflict_reason": "",
                    "suggestion": f"单域检测（{[d[0] for d in domains]}）与 content_domain（{content_domain}）冲突，需 L1 裁决",
                    "content_domain": content_domain,
                    "_needs_l1_arbitation": True,
                }
                return result

    # ── ② 原有跨部门规则 ──────────────────────────────────────────────
    cross = check_cross_domain_rules(domains, task)
    if cross:
        result = _handle_cross_rules(cross, domains, task)
        result["content_domain"] = content_domain
        return result

    # ── ③ 无规则多域场景 → 检测到多域但无跨域规则时，触发 L1 裁决 ─────────
    # 原来 _handle_multi_domain 会自动选第一个域为 primary，这会导致
    # investment+construction 等场景被错误路由。
    if len(domains) >= 2:
        result = {
            "is_cross_domain": True,
            "domains": [d[0] for d in domains],
            "primary": None,  # 需要 L1 裁决
            "supporting": [],
            "data_flow": "",
            "conflict": False,
            "conflict_reason": "",
            "suggestion": f"检测到多领域（{[d[0] for d in domains]}），需 L1 裁决主责域",
            "content_domain": content_domain,
            "_needs_l1_arbitation": True,
        }
        return result

    result = _handle_single_domain(domains)
    result["content_domain"] = content_domain
    return result


def _apply_content_dominant_map(content_domain: str, domains: list[tuple[str, float]]) -> dict | None:
    """
    根据内容主导规则，覆盖主责域。
    trading/code_tech/document/life_decision → 强制对应域为主责。
    analysis_report → 无 always_domain，不触发覆盖，走原有领域检测。
    """
    rules = _load_rules()
    content_rules = rules.get("content_type_rules", {}).get("content_dominant_map", {})
    override = content_rules.get(content_domain)
    if not override:
        return None

    current_domains = [d[0] for d in domains]
    forced_domain = override.get("always_domain")  # e.g. "investment"
    if not forced_domain:
        return None

    # ── Bug D 修复（最终版）───────────────────────────────────────────────────
    # 内容主导规则在以下情况放弃 override：
    # 情况A：forced_domain 不在检测到的域列表中 → 放弃 override
    #   例子："帮我分析苹果股票并看看旅游攻略"，life 在列表中，不适用
    #   例子："帮我制定杭州三日游计划"，life 不在列表 → 放弃 override（但因单域+content冲突，应特殊处理）
    #
    # 情况B（真正的 Bug D）：forced_domain 在列表中但不是第一域
    #   → 说明 content_domain 的域是次要任务（如"旅游攻略"是附带需求），
    #     不应覆盖明显的主任务（投资分析）
    #   例子："分析苹果股票并看看旅游攻略"，life 是第二域 → 跳过 override
    #
    # 情况C（正确场景）：单域检测错误（如"杭州三日游"→it）但 content_domain=life_decision
    #   → forced_domain 不在列表中，但当前检测的单个域与 content_domain 明显冲突
    #   → 应触发 L1 裁决，不自行修复
    if forced_domain not in current_domains:
        # forced_domain 不在检测列表中：放弃 override，让 L1 裁决
        return None
    if len(current_domains) > 1 and current_domains[0] != forced_domain:
        # forced_domain 是次要检测域（多域场景），跳过 override，让 L1 裁决
        return None
    if len(current_domains) == 1 and current_domains[0] != forced_domain:
        # 单域检测错误（如"杭州三日游"→it，但 content_domain=life_decision）
        # 不应让错误的单域覆盖 content_domain，应放弃 override 让 L1 裁决
        return None
    reason = override.get("reason", "")

    # 被强制域如果已经在检测到的 domains 中，则将其排到第一位
    if forced_domain in current_domains:
        # 重新排序：强制域优先，其余保持相对顺序
        remaining = [d for d in current_domains if d != forced_domain]
        reordered = [forced_domain] + remaining
    else:
        # 强制域不在检测结果中：追加到首位
        reordered = [forced_domain] + current_domains

    supporting = reordered[1:] if len(reordered) > 1 else []
    return {
        "primary": forced_domain,
        "supporting": supporting,
        "reason": reason,
        "domains_reordered": reordered,
    }


def _empty_domains_result() -> dict:
    return {
        "is_cross_domain": False,
        "domains": [],
        "primary": "life",
        "supporting": [],
        "data_flow": "",
        "conflict": False,
        "conflict_reason": "",
        "suggestion": "无法识别领域，使用兜底路由",
    }


def _handle_explicit(explicit: dict, domains: list) -> dict:
    explicit_type = explicit.get("type")

    if explicit_type == "explicit_cross":
        # explicit_cross 类型：用户明确说"既要A也要B"
        # 需要 L1 裁决确定主责域，不应自行指定 primary=None 并返回
        return {
            "is_cross_domain": True,
            "domains": explicit.get("domains", [d[0] for d in domains] if domains else []),
            "primary": None,  # 需要 L1 裁决
            "supporting": [],
            "data_flow": "",
            "conflict": False,
            "conflict_reason": "",
            "suggestion": "跨领域任务，需 L1 裁决主责域",
            "_needs_l1_arbitation": True,
        }

    if explicit["conflict"]:
        return {
            "is_cross_domain": True,
            "domains": [explicit["domain_a"], explicit["domain_b"]],
            "primary": None,
            "supporting": [],
            "data_flow": "",
            "conflict": True,
            "conflict_reason": f"任务同时涉及「{explicit['part_a']}」和「{explicit['part_b']}」，分别属于 {explicit['domain_a']} 和 {explicit['domain_b']} 领域，优先级冲突",
            "suggestion": "请明确哪个是主要目标，例如：「帮我做X（这是主要的），Y作为参考」",
        }

    return {
        "is_cross_domain": False,
        "domains": [d[0] for d in domains],
        "primary": explicit["primary"],
        "supporting": [],
        "data_flow": "",
        "conflict": False,
        "conflict_reason": "",
        "suggestion": f"任务涉及同一领域（{explicit['domain_a']}），内部协调处理",
    }


def _handle_cross_rules(cross: dict, domains: list, task: str) -> dict:
    cross["domains"] = cross.pop("domains_detected", [d[0] for d in domains])
    # 如果 primary 为空（如双项目资源竞争场景），表示无明确主责
    # 使用规则中的 data_flow/suggestion，同时保留 domains 信息供 CEO 判断
    if not cross.get("primary"):
        # primary='' 表示无明确主责（如双项目资源竞争场景）
        # 不应自行推断主责，而是触发 L1 裁决
        domain_names = [d[0] for d in domains]
        return {
            "is_cross_domain": True,
            "domains": domain_names,
            "primary": None,  # 需要 L1 裁决
            "supporting": [],
            "data_flow": cross.get("data_flow", ""),
            "conflict": False,
            "conflict_reason": "",
            "suggestion": f"检测到多领域（{domain_names}），需 L1 裁决主责域",
            "_needs_l1_arbitation": True,
            "_rule_data_flow": cross.get("data_flow", ""),
        }
    supporting_str = ", ".join(cross["supporting"]) if cross["supporting"] else "无"
    primary = cross.get("primary", "")
    return {
        "is_cross_domain": True,
        **cross,
        "conflict": False,
        "conflict_reason": "",
        "suggestion": f"主责：{cross['primary']} | 配合：{supporting_str}",
        "execution": {
            "mode": "delegate_to_primary",
            "primary": primary,
            "goal": f"按跨域流水线完成：{cross.get('data_flow', '')}。主责域 {primary} 负责协调全链路，配合域 {supporting_str} 提供输入。",
            "instruction": "L1 不得自行调用 terminal/execute_code/browser。将整个任务通过 delegate_task 派给 primary 域。"
        }
    }


def _handle_multi_domain(domains: list) -> dict:
    primary = domains[0][0]
    supporting = [d[0] for d in domains[1:]]
    supporting_str = ", ".join(supporting)
    return {
        "is_cross_domain": True,
        "domains": [d[0] for d in domains],
        "primary": primary,
        "supporting": supporting,
        "data_flow": f"主责领域（{primary}）负责主导，配合领域（{supporting_str}）提供辅助支持",
        "conflict": False,
        "conflict_reason": "",
        "suggestion": f"检测到多领域任务，主责：{primary}，配合：{supporting_str}",
        "execution": {
            "mode": "delegate_to_primary",
            "primary": primary,
            "goal": f"按跨域流水线完成此任务。主责域 {primary} 负责协调全链路，配合域 {supporting_str} 提供输入。",
            "instruction": "L1 不得自行调用 terminal/execute_code/browser。将整个任务通过 delegate_task 派给 primary 域。"
        }
    }


def _handle_single_domain(domains: list) -> dict:
    domain_name = domains[0][0]
    return {
        "is_cross_domain": False,
        "domains": [domain_name],
        "primary": domain_name,
        "supporting": [],
        "data_flow": "",
        "conflict": False,
        "conflict_reason": "",
        "suggestion": f"单一领域（{domain_name}），正常路由",
        "execution": {
            "mode": "delegate_to_primary",
            "primary": domain_name,
            "goal": f"执行此任务。",
            "instruction": "将任务通过 delegate_task 派给 primary 域执行。"
        }
    }

# ── 辅助函数（供 coordinate 调用）────────────────────────────────────────────

def detect_domains(task: str) -> list[tuple[str, float]]:
    """
    检测任务涉及的领域及置信度。
    复用 hermes_dispatcher 的关键词体系。
    返回 [(domain, confidence), ...]，按置信度降序。
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    # 直接复用 dispatcher 的意图识别逻辑
    try:
        from hermes_dispatcher import classify_intent, detect_cross_domain
        domain, confidence = classify_intent(task)
        # detect_cross_domain 返回命中列表，补充置信度
        hit_domains = detect_cross_domain(task)
        if hit_domains:
            return [(d, confidence) for d in hit_domains]
        return [(domain, confidence)]
    except Exception:
        # Fallback: 简单关键词匹配
        return _detect_domains_fallback(task)

def _detect_domains_fallback(task: str) -> list[tuple[str, float]]:
    """兜底的领域检测（当 dispatcher 不可用时）"""
    DOMAIN_KEYWORDS = {
        "investment": ["股票", "估值", "年报", "现金流", "投资", "持仓", "买入", "A股", "财报", "ETF"],
        "it": ["代码", "API", "数据库", "服务器", "前端", "后端", "Docker", "部署"],
        "life": ["旅游", "美食", "酒店", "健身", "行程", "攻略", "餐厅"],
        "ecommerce": ["电商", "海报", "流量", "发货", "SKU", "直播", "转化率", "shopify", "Shopify", "独立站", "Dawn主题", "Liquid模板"],
        "multimodal": ["PDF", "Word", "PPT", "图片", "视频", "文档", "排版", "分析资料"],
        "construction": ["图纸", "施工", "预算", "结构", "CAD", "BIM", "配筋"],
    }
    task_lower = task.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(0.1 for kw in keywords if kw in task_lower)
        if score > 0:
            scores[domain] = min(score + 0.5, 0.98)
    if not scores:
        return [("it", 0.55)]  # 默认 IT
    return sorted(scores.items(), key=lambda x: -x[1])


def check_explicit_conflict(task: str) -> dict | None:
    """
    检测任务中是否有明确的跨领域指令（如"既要A也要B"）。
    返回 conflict dict 或 None。
    """
    conflict_keywords = ["也要", "同时要", "并且", "兼顾", "同时处理"]
    both_keywords = ["既要", "既要做", "两个都要", "都要"]
    
    has_conflict = any(kw in task for kw in conflict_keywords)
    has_both = any(kw in task for kw in both_keywords)
    
    if not (has_conflict or has_both):
        return None
    
    # 尝试识别冲突的两端
    return {
        "type": "explicit_cross",
        "domains": [],  # 待 detect_domains 填充
        "primary": None,
        "supporting": [],
        "suggestion": "跨领域任务，主责+配合方自动协调",
    }


def check_cross_domain_rules(domains: list[tuple[str, float]], task: str) -> dict | None:
    """
    基于配置文件检测跨领域协同模式。
    从 cross_domain_rules.json 加载规则。
    """
    if len(domains) < 2:
        return None

    domain_names = [d[0] for d in domains]
    rules_obj = _load_rules().get("cross_domain_rules", {})
    if isinstance(rules_obj, dict):
        rules = rules_obj.get("rules", [])
    else:
        rules = []  # 兜底：非 dict 类型

    # 检查是否有规则匹配
    for rule in rules:
        rule_domains = rule.get("domains", [])
        if all(d in domain_names for d in rule_domains):
            result = dict(rule)
            result["domains_detected"] = domain_names
            return result

    return None
