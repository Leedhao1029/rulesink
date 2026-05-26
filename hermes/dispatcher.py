#!/usr/bin/env python3
"""
Hermes Dispatcher — L1 Intent Routing Layer
hermes_dispatcher.py — User Natural Language → Domain Classification → L2 Orchestrator Dispatch

This is the public architectural interface.
Full implementation is proprietary and not exposed in this open-source package.

Architecture:
    User Input → Intent Detection → Domain Classification → L2 Dispatch → Result Aggregation

Public Interface:
    detect_content_domain(task: str) -> str
    classify_domain(task: str) -> Dict[str, Any]
    dispatch(task: str, domain: str) -> DispatchResult
    write_event(event_type: str, **kwargs) -> None

For the complete implementation (1,735 lines), see the full hermes-dispatcher
module in the proprietary Hermes Agent distribution.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# ── Public Exceptions ─────────────────────────────────────────────────────────────────

class PendingGitHubApproval(Exception):
    """Raised when GitHub search finds candidate scripts needing user approval."""
    pass

class PendingHumanReview(Exception):
    """Raised after 3 failed build attempts — requires human review of pending JSON."""
    pass

# ── Public Constants ──────────────────────────────────────────────────────────────────

L2_NAMES: Dict[str, str] = {
    "construction": "建筑工程总经理",
    "ecommerce":     "电子商务总经理",
    "investment":    "投资总经理",
    "it":           "IT技术总经理",
    "life":         "生活事务总经理",
    "multimodal":   "多模态总经理",
    "meta":         "自我进化总经理",
}

# ── Public Domain Classification Interface ─────────────────────────────────────────

def classify_domain(task: str) -> Dict[str, Any]:
    """
    Classify a user task into one or more domains.

    Args:
        task: Natural language task description

    Returns:
        {
            "primary_domain": str,          # Most confident domain
            "confidence": float,            # 0.0–1.0
            "all_matches": List[Dict],    # All matched domains with scores
            "is_cross_domain": bool,
            "requires_multi_agent": bool,
        }
    """
    # Scoring: keyword matching + contextual analysis
    # Domain keywords organized in two tiers:
    #   high: strong signal (+0.12 per match, capped)
    #   low:  weak signal (+0.04 per match, capped)
    # Base score: 0.55 (unclassified)
    # Ceiling: 0.98
    #
    # Full keyword database (10,000+ entries) not disclosed in open-source package.
    return {
        "primary_domain": _infer_domain(task),
        "confidence": _score_confidence(task),
        "all_matches": _get_all_matches(task),
        "is_cross_domain": _is_cross_domain(task),
        "requires_multi_agent": _needs_parallel(task),
    }


def detect_content_domain(task: str) -> str:
    """
    Detect content type (not just business domain).
    Used for content-domain routing override.

    Categories:
        trading   → force to investment domain
        code_tech → force to IT domain
        document  → force to multimodal domain
        life_decision → force to life domain
        analysis_report → standard analysis routing
        unknown → use standard domain classification
    """
    return _detect_content_type(task)


def dispatch(task: str, domain: Optional[str] = None) -> Dict[str, Any]:
    """
    Dispatch a task to the appropriate L2 orchestrator.

    Args:
        task: Natural language task
        domain: Optional override — if None, classify_domain() is called first

    Returns:
        {
            "domain": str,
            "l2_orchestrator": str,      # Path to orchestrator script
            "confidence": float,
            "cross_domain": bool,
            "dispatch_event": dict,         # Written to events.jsonl
        }
    """
    if domain is None:
        classified = classify_domain(task)
        domain = classified["primary_domain"]
        confidence = classified["confidence"]
        is_cross = classified["is_cross_domain"]
    else:
        confidence = 1.0
        is_cross = False

    event = write_event(
        "dispatch",
        task=task[:100],
        domain=domain,
        confidence=confidence,
        cross_domain=is_cross,
    )

    return {
        "domain": domain,
        "confidence": confidence,
        "cross_domain": is_cross,
        "dispatch_event": event,
        "note": "L2 orchestration result returned to L1 for final report synthesis",
    }


def write_event(event_type: str, **kwargs) -> Dict[str, Any]:
    """
    Append a structured event to the global event log (events.jsonl).

    This provides the audit trail required by the SOUL.md arbitration layer.
    Every dispatch, execution, and decision is logged with timestamp and session ID.

    Event schema:
        {
            "ts": ISO8601 timestamp (UTC),
            "session": HERMES_SESSION env var,
            "event": event_type,
            ...kwargs (event-specific fields)
        }
    """
    from pathlib import Path as _P
    import os as _os

    HERMES_HOME = Path(__file__).parent.parent
    EVENTS_FILE = HERMES_HOME / "events" / "events.jsonl"
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session": _os.environ.get("HERMES_SESSION", "cli"),
        "event": event_type,
        **kwargs,
    }

    with open(EVENTS_FILE, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


# ── Private Implementation Stubs (not disclosed) ────────────────────────────────────

def _infer_domain(task: str) -> str:
    """Domain inference — keyword scoring algorithm not disclosed."""
    ...

def _score_confidence(task: str) -> float:
    """Confidence scoring — algorithm parameters not disclosed."""
    ...

def _get_all_matches(task: str) -> List[Dict[str, Any]]:
    """Return all domain matches above threshold."""
    ...

def _is_cross_domain(task: str) -> bool:
    """Detect if task requires multiple domain coordination."""
    ...

def _needs_parallel(task: str) -> bool:
    """Detect if task should run in parallel agents."""
    ...

def _detect_content_type(task: str) -> str:
    """Content type detection — parameters not disclosed."""
    ...


if __name__ == "__main__":
    # CLI usage: python3 hermes/dispatcher.py "帮我分析一下电商转化率"
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        result = dispatch(task)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python3 hermes/dispatcher.py <task>")
