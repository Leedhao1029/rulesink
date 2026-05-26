#!/usr/bin/env python3
"""
IT Domain Orchestrator — L2 Layer
it_orchestrator.py — IT技术总经理

Five-Step Closed Loop:
    Perceive  → Analyze task complexity
    Plan      → Discover L3 modules + route
    Execute   → Parallel execution
    Verify    → Seven-dimension quality gate
    Memorize  → Archive to it_archive/

This is a PUBLIC architectural preview (~400 lines).
The full IT orchestrator (4,094 lines) is available in the
proprietary Hermes Agent distribution.

Public Architecture Revealed Here:
    • L1 integration points (circuit_breaker, final_reporter, skill_cache)
    • Five-step orchestration loop (Perceive/Plan/Execute/Verify/Memorize)
    • L3 discovery and routing mechanism
    • Seven-dimension quality verification
    • Self-evolution trigger logic
    • Behavior self-check framework

NOT Disclosed (Proprietary):
    • Specific L3 module registry (l3_it_*.py file list)
    • Exact threshold values for quality gates
    • Circuit breaker parameters (turn limits, budget caps)
    • Skill cache eviction policies
    • Autobiography learning algorithm weights
"""

import json
import shutil
import importlib
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

# ── Paths ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
VENV_PY = Path.home() / ".hermes" / "venv" / "bin" / "python3"
HERMES_HOME = Path.home() / ".hermes"
ARCHIVE_DIR = SCRIPT_DIR / "it_archive"
ARCHIVE_DIR.mkdir(exist_ok=True)


# ── L1 Integration Points ──────────────────────────────────────────────────────────

def _load_l1_module(module_name: str):
    """Load a named L1 module by dynamic import."""
    try:
        module_path = SCRIPT_DIR / f"l1_{module_name}.py"
        if not module_path.exists():
            return None
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


# Load L1 modules
_l1_circuit_breaker = _load_l1_module("circuit_breaker")
_l1_final_reporter = _load_l1_module("final_reporter")
_l1_skill_cache = _load_l1_module("skill_cache")


# ── Behavior Self-Check Framework ────────────────────────────────────────────────

BEHAVIOR_SELF_CHECK = {
    "plan": [
        ("架构意识", "是否识别了所需的架构类型（前端/后端/全栈/移动端）？"),
        ("技术选型", "技术栈选择是否在能力圈内？有无过度设计？"),
        ("安全底线", "是否识别了安全敏感操作（认证/加密/权限）？"),
        ("质量目标", "成功标准是否可验证？有没有可测试的检查点？"),
    ],
    "memorize": [
        ("记录价值", "这条记录能帮助下次相似IT任务吗？"),
        ("数据精简", "写入字段是否刚好够用？有没有冗余？"),
        ("执行溯源", "autobiography 条目是否精确到每次独立执行？"),
        ("质量闭环", "这次执行是否达到了预期的架构/代码质量目标？"),
    ],
}


def _run_self_check(phase: str, context: str) -> Dict[str, Any]:
    """
    Run behavior self-check for a given phase.
    All IT tasks must pass through this framework before/after execution.
    """
    checks = BEHAVIOR_SELF_CHECK.get(phase, [])
    flags, notes = [], []
    for label, question in checks:
        flags.append(question)
        notes.append(f"[{phase}] {label}: {question} | context={context[:30]}")
    return {"phase": phase, "passed": True, "flags": flags, "notes": notes}


# ── Self-Evolution Trigger ─────────────────────────────────────────────────────────

def _forge_trigger_check(task: str, domain: str) -> Dict[str, Any]:
    """
    Check if a task should trigger the self-evolution forge queue.

    Trigger conditions (all must be met):
        1. Similar task has run ≥ 3 times in autobiography
        2. Success rate ≥ 70% across those runs
        3. Average complexity ≥ 2.5

    Parameters for these thresholds are proprietary.
    The trigger framework is public; the actual values are not disclosed.

    Returns:
        {
            "should_forge": bool,
            "reason": str,
            "repeat_count": int,
            "avg_quality": float,
        }
    """
    auto_path = HERMES_HOME / "autobiography.json"
    if not auto_path.exists():
        return {"should_forge": False, "reason": "no history", "repeat_count": 0, "avg_quality": 0.0}

    try:
        auto_data = json.loads(auto_path.read_text())
    except Exception:
        return {"should_forge": False, "reason": "autobiography read failed", "repeat_count": 0, "avg_quality": 0.0}

    runs_key = f"{domain}_runs"
    runs = auto_data.get(runs_key, [])
    if len(runs) < 2:
        return {"should_forge": False, "reason": f"insufficient history ({len(runs)} runs)", "repeat_count": len(runs), "avg_quality": 0.0}

    task_prefix = task[:40]
    similar = [r for r in runs if r.get("task", "").startswith(task_prefix)]
    repeat_count = len(similar)

    if repeat_count < 3:
        return {"should_forge": False, "reason": f"similar runs < 3 ({repeat_count})", "repeat_count": repeat_count, "avg_quality": 0.0}

    successful = sum(1 for r in similar if r.get("verify_pass", False))
    success_rate = successful / repeat_count
    avg_quality = sum(r.get("quality_score", 0) for r in similar) / repeat_count

    # Threshold values are proprietary
    if success_rate >= 0.7 and avg_quality >= 2.5:
        return {"should_forge": True, "reason": f"forge conditions met", "repeat_count": repeat_count, "avg_quality": avg_quality}

    return {"should_forge": False, "reason": "thresholds not met", "repeat_count": repeat_count, "avg_quality": avg_quality}


# ── Five-Step Orchestration Loop ───────────────────────────────────────────────────

class VerifyIssue(Exception):
    """Raised when quality verification fails."""
    def __init__(self, issues: List[str], retryable: bool = True):
        self.issues = issues
        self.retryable = retryable


def orchestrate(task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Execute the five-step IT orchestration loop.

    Step 1 — PERCEIVE: Analyze task complexity, determine execution lane
    Step 2 — PLAN:    Discover L3 modules, build execution DAG
    Step 3 — EXECUTE: Run selected L3 modules (parallel or sequential)
    Step 4 — VERIFY:  Seven-dimension quality gate
    Step 5 — MEMORIZE: Archive result, update autobiography

    Args:
        task: Natural language IT task
        context: Optional context dict

    Returns:
        {
            "task": str,
            "steps_executed": List[str],
            "quality_status": "PASS" | "NEEDS_WORK",
            "l3_results": List[dict],
            "verify_issues": List[str],
            "forge_triggered": bool,
            "archive_path": str,
            "behavior_self_check": dict,
        }
    """
    ctx = context or {}
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Step 1: Perceive ──────────────────────────────────────────────────────
    perceived = _perceive(task, ctx)
    lane = perceived["lane"]  # fast / standard / full

    # ── Step 2: Plan ───────────────────────────────────────────────────────────
    planned = _plan(task, ctx, lane)
    selected_l3_modules = planned["modules"]
    execution_order = planned["order"]  # "parallel" | "sequential"

    # ── Step 3: Execute ───────────────────────────────────────────────────────
    executed = _execute(task, ctx, selected_l3_modules, execution_order)
    l3_results = executed["results"]

    # ── Step 4: Verify ─────────────────────────────────────────────────────────
    verified = _verify(l3_results, task)
    verify_issues = verified["issues"]

    # ── Step 5: Memorize ───────────────────────────────────────────────────────
    memorized = _memorize(task, task_id, l3_results, verified, ctx)

    return {
        "task": task,
        "task_id": task_id,
        "lane": lane,
        "steps_executed": ["perceive", "plan", "execute", "verify", "memorize"],
        "l3_modules_used": [m["name"] for m in selected_l3_modules],
        "execution_order": execution_order,
        "quality_status": "PASS" if not verify_issues else "NEEDS_WORK",
        "l3_results": l3_results,
        "verify_issues": verify_issues,
        "forge_triggered": memorized.get("forge_triggered", False),
        "archive_path": str(memorized.get("archive_path", "")),
        "behavior_self_check": memorized.get("behavior_check", {}),
    }


# ── Step 1: Perceive ──────────────────────────────────────────────────────────────

def _perceive(task: str, ctx: Dict) -> Dict[str, Any]:
    """
    Perceive: Analyze task complexity and select execution lane.

    Lanes:
        fast     → Simple query, single L3, no verification
        standard → Normal complexity, standard L3 selection
        full     → Complex multi-step, parallel execution, full verification

    Complexity assessment dimensions:
        - Token length of task
        - Number of technical domains involved
        - Presence of security-sensitive operations
        - Known multi-step patterns
    """
    # Load L1 circuit breaker for complexity assessment
    if _l1_circuit_breaker:
        try:
            complexity = _l1_circuit_breaker.assess_complexity(task)
            lane = complexity.get("lane", "standard")
        except Exception:
            lane = "standard"
    else:
        lane = "standard"

    return {"lane": lane, "task": task}


# ── Step 2: Plan ─────────────────────────────────────────────────────────────────

def _plan(task: str, ctx: Dict, lane: str) -> Dict[str, Any]:
    """
    Plan: Discover relevant L3 modules and determine execution order.

    Discovery mechanism:
        1. Extract keywords from task
        2. Consult L1 skill cache for matching skills
        3. Load matching L3 scripts (l3_it_*.py)
        4. Build execution DAG based on dependencies

    NOT disclosed: The full keyword→skill→L3 module registry mapping
    """
    # Discover L3 modules using skill cache
    if _l1_skill_cache:
        try:
            l3_matches = _l1_skill_cache.find_l3_by_keyword(task)
        except Exception:
            l3_matches = []
    else:
        l3_matches = []

    # Load L3 scripts (names only — full registry not disclosed)
    modules = [
        {"name": name, "path": str(SCRIPT_DIR / f"{name}.py")}
        for name in l3_matches
    ]

    execution_order = "parallel" if lane == "full" else "sequential"

    return {
        "modules": modules,
        "order": execution_order,
        "lane": lane,
    }


# ── Step 3: Execute ───────────────────────────────────────────────────────────────

def _execute(task: str, ctx: Dict, modules: List[Dict], order: str) -> Dict[str, Any]:
    """
    Execute: Run selected L3 modules.

    For "parallel" mode, modules are dispatched concurrently.
    For "sequential" mode, modules run in dependency order.

    NOT disclosed: The specific subprocess invocation pattern,
    venv activation, timeout management, and error propagation logic.
    """
    results = []

    if order == "parallel":
        # Concurrent execution via ThreadPoolExecutor
        # (implementation not disclosed)
        results = [{"name": m["name"], "status": "executed"} for m in modules]
    else:
        # Sequential execution
        # (implementation not disclosed)
        results = [{"name": m["name"], "status": "executed"} for m in modules]

    return {"results": results}


# ── Step 4: Verify ───────────────────────────────────────────────────────────────

VERIFY_DIMENSIONS = [
    "correctness",    # Does the output solve the task?
    "completeness",   # Are all parts of the task addressed?
    "safety",         # Are there security concerns?
    "efficiency",     # Is the solution appropriately complex?
    "maintainability",# Is the code readable and documented?
    "testability",    # Can the output be automatically verified?
    "alignment",      # Does output match the original intent?
]


def _verify(l3_results: List[Dict], task: str) -> Dict[str, Any]:
    """
    Verify: Seven-dimension quality gate.

    Each dimension is scored 0–10.
    Overall PASS threshold: average ≥ 7.0 with no dimension at 0

    The specific scoring rubric and weight table are proprietary.
    The seven dimensions themselves are public.
    """
    issues = []

    # Check for empty results
    if not l3_results:
        issues.append("No L3 results returned — possible execution failure")

    # Check each dimension (rubric not disclosed)
    for dim in VERIFY_DIMENSIONS:
        score = _score_dimension(dim, l3_results, task)
        if score == 0:
            issues.append(f"Dimension '{dim}' scored 0 — requires attention")

    return {"issues": issues, "dimensions": VERIFY_DIMENSIONS}


def _score_dimension(dim: str, results: List[Dict], task: str) -> float:
    """
    Score a single verification dimension.
    The scoring algorithm and per-dimension weight tables are proprietary.
    """
    # Placeholder — actual scoring not disclosed
    return 8.0


# ── Step 5: Memorize ─────────────────────────────────────────────────────────────

def _memorize(task: str, task_id: str, l3_results: List[Dict],
               verified: Dict, ctx: Dict) -> Dict[str, Any]:
    """
    Memorize: Archive execution result and update autobiography.

    Archive path: it_archive/{task_id}_report.json
    Autobiography: ~/.hermes/autobiography.json

    NOT disclosed: The autobiography schema and learning algorithm
    that processes these archives into improved routing decisions.
    """
    archive_file = ARCHIVE_DIR / f"{task_id}_report.json"

    archive_data = {
        "task_id": task_id,
        "task": task,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "l3_results": l3_results,
        "verify_issues": verified.get("issues", []),
        "quality_pass": len(verified.get("issues", [])) == 0,
    }

    archive_file.write_text(json.dumps(archive_data, ensure_ascii=False, indent=2))

    # Trigger forge check
    forge_check = _forge_trigger_check(task, "it")

    return {
        "archive_path": str(archive_file),
        "forge_triggered": forge_check.get("should_forge", False),
        "behavior_check": _run_self_check("memorize", task),
    }


# ── CLI Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        result = orchestrate(task)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python3 it_orchestrator.py <IT task>")
