#!/usr/bin/env python3
"""
IT Self-Evolution Module
it_self_evolution.py

Monitors the IT domain's L3 script health, detects capability gaps,
and triggers the forge queue when conditions are met.

5-Stage Evolution Loop:
    ANALYZE → DIAGNOSE → PLAN → EXECUTE → LEARN

Stage 1: ANALYZE
    • Scan all L3 scripts in l3_it_*.py
    • Check skill coverage (registered skills vs. used skills)
    • Review archive logs for failure patterns
    • Measure execution quality scores

Stage 2: DIAGNOSE
    • Classify issues: MISSING_SKILL / WEAK_SKILL / BROKEN_SCRIPT / STALE_ARCHIVE
    • Assess severity: CRITICAL / WARNING / MINOR
    • Identify root cause category

Stage 3: PLAN
    • Generate build proposals for each issue
    • Assess build difficulty (1–5 scale)
    • Assign priority based on impact and effort

Stage 4: EXECUTE
    • User confirms via hermes approve / deny
    • Build new L3 script or update skill
    • Self-test in check mode before activation

Stage 5: LEARN
    • Record to autobiography (task, quality_score, complexity, verify_pass)
    • Update skill effectiveness weights
    • Update forge trigger thresholds based on outcomes

This is a PUBLIC architectural preview (200 lines).
The full self-evolution engine (~802 lines) is proprietary.

Public Interface:
    analyze()   → Run stage 1: scan and collect metrics
    diagnose()  → Run stage 2: classify issues
    plan()      → Run stage 3: generate proposals
    execute()   → Run stage 4: user-confirmed changes
    learn()     → Run stage 5: record to autobiography

Trigger Conditions (proprietary thresholds):
    • Repeat count ≥ 3
    • Success rate ≥ 70%
    • Average complexity ≥ 2.5
    • No recent forge activity (cooldown)
"""

import json
import importlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# ── Paths ─────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.parent.parent / "scripts"
HERMES_HOME = Path.home() / ".hermes"
SKILL_DIR = HERMES_HOME / "skills"
ARCHIVE_DIR = SCRIPT_DIR / "it_archive"
AUTO_FILE = HERMES_HOME / "autobiography.json"
FORGE_QUEUE = HERMES_HOME / "forge_queue.jsonl"


# ── Evolution Stage Interface ────────────────────────────────────────────────────

def analyze() -> Dict[str, Any]:
    """
    Stage 1: ANALYZE

    Scan all IT L3 scripts and skills, collect health metrics.

    Returns:
        {
            "stage": "analyze",
            "timestamp": ISO8601,
            "scripts_found": int,
            "skills_found": int,
            "archives_found": int,
            "health_metrics": {
                "scripts_with_issues": List[str],
                "skills_needing_review": List[str],
                "stale_archives": List[str],
            },
            "execution_summary": {
                "total_runs": int,
                "avg_quality": float,
                "verify_pass_rate": float,
            }
        }
    """
    scripts = list(SCRIPT_DIR.glob("l3_it_*.py"))
    skills = list(SKILL_DIR.glob("it-*/SKILL.md"))
    archives = list(ARCHIVE_DIR.glob("*_report.json")) if ARCHIVE_DIR.exists() else []

    health = _check_script_health(scripts)
    exec_summary = _summarize_execution(archives)

    return {
        "stage": "analyze",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scripts_found": len(scripts),
        "skills_found": len(skills),
        "archives_found": len(archives),
        "health_metrics": health,
        "execution_summary": exec_summary,
    }


def diagnose(analysis_result: Dict) -> Dict[str, Any]:
    """
    Stage 2: DIAGNOSE

    Classify findings from ANALYZE into actionable issues.

    Issue Classification Taxonomy:
        MISSING_SKILL  — Operational scenario has no corresponding skill
        WEAK_SKILL    — Skill exists but lacks depth (thin skill)
        BROKEN_SCRIPT — L3 script fails to load or run
        STALE_ARCHIVE — Archive not updated in N days
        ARCHITECTURAL — Pattern-level issue (repeated failure class)

    Severity Levels:
        CRITICAL — Blocks execution or causes data loss risk
        WARNING  — Degrades quality or efficiency
        MINOR    — Cosmetic or edge case
    """
    issues = []

    for script in analysis_result.get("health_metrics", {}).get("scripts_with_issues", []):
        severity = _classify_severity(script)
        category = _classify_issue(script)
        issues.append({
            "item": script,
            "severity": severity,
            "category": category,
            "recommendation": _get_recommendation(category),
        })

    for skill in analysis_result.get("health_metrics", {}).get("skills_needing_review", []):
        issues.append({
            "item": skill,
            "severity": "WARNING",
            "category": "WEAK_SKILL",
            "recommendation": "Enrich skill with Pitfalls/Examples/真实API参数",
        })

    return {
        "stage": "diagnose",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "issues": issues,
        "critical_count": sum(1 for i in issues if i["severity"] == "CRITICAL"),
        "warning_count": sum(1 for i in issues if i["severity"] == "WARNING"),
        "minor_count": sum(1 for i in issues if i["severity"] == "MINOR"),
    }


def plan(diagnosis_result: Dict) -> Dict[str, Any]:
    """
    Stage 3: PLAN

    Generate concrete build proposals for each issue.

    For each issue:
        • Determine build type: NEW_SCRIPT / UPDATE_SKILL / FIX_SCRIPT / ARCHIVE_CLEANUP
        • Assess complexity (1–5): based on scope and dependencies
        • Assign priority: P0 (critical) / P1 (warning) / P2 (minor)
        • Outline required inputs and expected outputs

    NOT disclosed: The complexity scoring rubric and priority thresholds.
    """
    proposals = []

    for issue in diagnosis_result.get("issues", []):
        proposal = _build_proposal(issue)
        if proposal:
            proposals.append(proposal)

    return {
        "stage": "plan",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proposals": proposals,
        "total_proposals": len(proposals),
        "p0_count": sum(1 for p in proposals if p.get("priority") == "P0"),
    }


def execute(proposals: List[Dict]) -> Dict[str, Any]:
    """
    Stage 4: EXECUTE

    User-confirmed changes only. No automatic execution.

    Workflow:
        1. Write proposals to forge_queue.jsonl
        2. Notify user: "Run 'hermes approve' or 'hermes deny'"
        3. After user confirmation, execute approved proposals
        4. Run self-test in check mode
        5. Activate new scripts / updated skills

    Self-test criteria (check mode):
        • Script loads without ImportError
        • run() returns valid structure (has standard header)
        • verify_output() passes for required fields
        • No unhandled exceptions

    Returns:
        {
            "stage": "execute",
            "queued": int,
            "approved": int,
            "denied": int,
            "activated": List[str],
            "test_results": List[dict],
        }
    """
    if not proposals:
        return {"stage": "execute", "queued": 0, "approved": 0, "activated": []}

    # Queue proposals
    queued = len(proposals)
    FORGE_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with open(FORGE_QUEUE, "a") as f:
        for p in proposals:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **p}, ensure_ascii=False) + "\n")

    return {
        "stage": "execute",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "queued": queued,
        "note": "Proposals written to forge queue — awaiting user approval",
        "user_action_required": "hermes approve | hermes deny",
    }


def learn(execution_result: Dict, original_task: str = None) -> Dict[str, Any]:
    """
    Stage 5: LEARN

    Record execution outcome to autobiography.

    Autobiography entry schema:
        {
            "task": str,            # Task description (first 100 chars)
            "domain": str,           # "it"
            "timestamp": ISO8601,
            "l3_modules_used": List[str],
            "quality_score": float, # 1–10
            "complexity": float,    # 1–10
            "verify_pass": bool,
            "forge_triggered": bool,
            "execution_time_ms": int,
        }

    NOT disclosed: How autobiography entries are processed into
    improved routing decisions and forge trigger thresholds.
    """
    entry = {
        "task": (original_task or "")[:100],
        "domain": "it",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "quality_score": execution_result.get("quality_status") == "PASS" and 8.0 or 5.0,
        "complexity": 3.0,  # Placeholder
        "verify_pass": execution_result.get("quality_status") == "PASS",
        "forge_triggered": False,
    }

    AUTO_FILE.parent.mkdir(parents=True, exist_ok=True)
    auto_data = {}
    if AUTO_FILE.exists():
        try:
            auto_data = json.loads(AUTO_FILE.read_text())
        except Exception:
            auto_data = {}

    runs_key = "it_runs"
    if runs_key not in auto_data:
        auto_data[runs_key] = []
    auto_data[runs_key].append(entry)

    AUTO_FILE.write_text(json.dumps(auto_data, ensure_ascii=False, indent=2))

    return {
        "stage": "learn",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry_written": True,
        "total_it_runs": len(auto_data.get(runs_key, [])),
    }


# ── Private Helpers (algorithm not disclosed) ────────────────────────────────────

def _check_script_health(scripts: List[Path]) -> Dict[str, List[str]]:
    """
    Check each L3 script for health issues.

    INTEGRATION GUIDE:
    Implement your own health-check logic:
      - Parse script AST for L3Base inheritance
      - Check for required methods (analyze/plan/execute/report/evolve)
      - Detect syntax errors, broken imports, missing skill links

    REQUIRED return shape:
        {
            "scripts_with_issues": List[str],   # Filenames with problems
            "skills_needing_review": List[str], # Skill names with stale content
            "stale_archives": List[str],       # Archive files > 30 days old
        }

    Raises:
        NotImplementedError: Always — replace with your own health-check logic.
    """
    raise NotImplementedError(
        "SPEC_SHEET_ONLY: _check_script_health is a规格说明书型 function. "
        "Implement your script health-checker and return the dict shape shown in the docstring."
    )


def _summarize_execution(archives: List[Path]) -> Dict[str, Any]:
    """
    Aggregate quality metrics from archive reports.

    INTEGRATION GUIDE:
    Implement your own aggregation logic:
      - Parse each archive JSON for quality_score and verify_result
      - Compute mean quality, verify pass rate, trend over time

    REQUIRED return shape:
        {
            "total_runs": int,       # Total execution runs found
            "avg_quality": float,   # Mean quality score 0.0–1.0
            "verify_pass_rate": float,  # Fraction of runs that passed verification
        }

    Raises:
        NotImplementedError: Always — replace with your own aggregation.
    """
    raise NotImplementedError(
        "SPEC_SHEET_ONLY: _summarize_execution is a规格说明书型 function. "
        "Implement your archive aggregator and return the dict shape shown in the docstring."
    )


def _classify_severity(item: str) -> str:
    """
    Classify issue severity.

    INTEGRATION GUIDE:
    Implement your own severity rubric:
      - CRITICAL: data loss risk, security hole, complete breakage
      - WARNING: degraded functionality, performance issue
      - MINOR: cosmetic, documentation, minor UX issue

    Returns:
        str: "CRITICAL" | "WARNING" | "MINOR"

    Raises:
        NotImplementedError: Always — replace with your own classifier.
    """
    raise NotImplementedError(
        "SPEC_SHEET_ONLY: _classify_severity is a规格说明书型 function. "
        "Implement your own severity classifier. Return 'CRITICAL', 'WARNING', or 'MINOR'."
    )


def _classify_issue(item: str) -> str:
    """
    Classify issue into the issue taxonomy.

    INTEGRATION GUIDE:
    Implement your own issue taxonomy classifier:
      - MISSING_SKILL: trigger word has no matching L3/skill
      - WEAK_SKILL: skill exists but lacks real API params or verification steps
      - BROKEN_SCRIPT: L3 script exists but has runtime/syntax errors
      - STALE_ARCHIVE: archive report > 30 days old
      - ... add your own categories

    Returns:
        str: One of your taxonomy category names

    Raises:
        NotImplementedError: Always — replace with your own classifier.
    """
    raise NotImplementedError(
        "SPEC_SHEET_ONLY: _classify_issue is a规格说明书型 function. "
        "Implement your own issue taxonomy classifier. "
        "Return a category string from your taxonomy (e.g. 'MISSING_SKILL', 'BROKEN_SCRIPT')."
    )


def _build_proposal(issue: Dict) -> Optional[Dict]:
    """
    Build a concrete proposal from a diagnosed issue.

    INTEGRATION GUIDE:
    Implement your own proposal builder:
      - Map issue category → build_type (UPDATE_SKILL | CREATE_L3 | FIX_SCRIPT | ...)
      - Estimate priority from severity
      - Assess complexity from scope (files affected, skill depth needed)
      - Write a description that a developer can act on without further context

    REQUIRED return shape:
        {
            "proposal_id": str,       # Unique ID, e.g. "prop_<timestamp>"
            "item": str,              # What needs changing
            "category": str,          # Issue category from _classify_issue
            "priority": str,          # "P0" | "P1" | "P2"
            "complexity": int,         # 1–5 scale
            "description": str,       # Actionable description for a developer
            "build_type": str,        # "UPDATE_SKILL" | "CREATE_L3" | "FIX_SCRIPT" | ...
        }

    Args:
        issue: Dict with keys "item", "category", "severity", "recommendation"

    Raises:
        NotImplementedError: Always — replace with your own proposal builder.
    """
    raise NotImplementedError(
        "SPEC_SHEET_ONLY: _build_proposal is a规格说明书型 function. "
        "Implement your own proposal builder and return the dict shape shown in the docstring. "
        "Map severity → priority (CRITICAL→P0, WARNING→P1, MINOR→P2) and "
        "category → build_type (MISSING_SKILL→CREATE_L3, WEAK_SKILL→UPDATE_SKILL, etc.)."
    )


def _get_recommendation(category: str) -> str:
    """
    Return a human-readable fix recommendation for an issue category.

    INTEGRATION GUIDE:
    This maps your taxonomy category → actionable fix instruction.
    Implement your own mapping that developers can understand without
    reading the full diagnosis.

    Example mappings:
        "MISSING_SKILL": "Build new skill: define trigger keywords + Steps + Pitfalls + Examples"
        "WEAK_SKILL":    "Enrich skill: add real API params, known pitfalls, verification steps"
        "BROKEN_SCRIPT": "Fix script: verify L3Base inheritance and run() return dict format"
        "STALE_ARCHIVE": "Clean up: delete archive files older than 30 days"

    Args:
        category: One of your taxonomy category strings

    Returns:
        str: A one-sentence fix recommendation for a developer to act on.

    Raises:
        NotImplementedError: Always — replace with your own recommendation map.
    """
    raise NotImplementedError(
        "SPEC_SHEET_ONLY: _get_recommendation is a规格说明书型 function. "
        "Implement your own category→recommendation mapping. "
        "Return a short, actionable sentence for developers. "
        "Examples: MISSING_SKILL→'Build new skill', WEAK_SKILL→'Enrich skill with real API params'."
    )


# ── CLI Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 it_self_evolution.py <stage>")
        print("Stages: analyze | diagnose | plan | execute | learn")
        sys.exit(1)

    stage = sys.argv[1]

    if stage == "analyze":
        result = analyze()
    elif stage == "diagnose":
        analysis = analyze()
        result = diagnose(analysis)
    elif stage == "plan":
        analysis = analyze()
        diagnosis = diagnose(analysis)
        result = plan(diagnosis)
    elif stage == "execute":
        analysis = analyze()
        diagnosis = diagnose(analysis)
        proposals = plan(diagnosis).get("proposals", [])
        result = execute(proposals)
    elif stage == "learn":
        result = learn({})
    else:
        print(f"Unknown stage: {stage}")
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
