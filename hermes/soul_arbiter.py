#!/usr/bin/env python3
"""
SOUL Arbiter — Constitutional Constraint Layer

The SOUL Arbiter is the constraint enforcement layer that every L3 output
passes through before delivery. It implements the rules defined in SOUL.md
— the organization's constitutional document.

The SOUL Arbiter has TWO levels:

Level 1 — SOUL Interface (public, shown here):
    • audit(output, context) -> AuditResult
    • check_authorization(action, actor) -> bool
    • escalate(conflict) -> dict

Level 2 — Pattern Engine (proprietary, not disclosed):
    • The actual regex patterns, threshold values, and scoring algorithms
    • The SOUL constraint database
    • The escalation routing logic

This separation is intentional:
    → Organizations can see WHAT the arbiter checks (interface)
    → They cannot replicate HOW it checks (proprietary engine)

Usage Example:
    from hermes.soul_arbiter import SOULArbiter

    arbiter = SOULArbiter()
    result = arbiter.audit(l3_output, {"actor": "l3_ecommerce_ops", "task": "..."})

    if result.verdict == "BLOCK":
        output = result.redacted_content
        # Blocked content removed, event logged, user notified
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# ── Enums ─────────────────────────────────────────────────────────────────────────

class Verdict(Enum):
    PASS = "PASS"      # Clear — deliver as-is
    FLAG = "FLAG"      # Caution — deliver with annotations
    BLOCK = "BLOCK"    # Violation — content filtered or withheld


class ActorRole(Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    COUNCIL = "COUNCIL"
    EXTERNAL = "EXTERNAL"


# ── Data Classes ─────────────────────────────────────────────────────────────────

@dataclass
class AuditResult:
    verdict: Verdict
    flags: List[str] = field(default_factory=list)
    redacted_content: str = ""
    event_log: Dict = field(default_factory=dict)
    annotations: List[str] = field(default_factory=list)


@dataclass
class AuthorizationResult:
    authorized: bool
    reason: str
    requires_escalation: bool = False


# ── SOULArbiter Class ────────────────────────────────────────────────────────────

class SOULArbiter:
    """
    Constitutional constraint layer for all L3 outputs.

    Audit dimensions (public interface):
        1. L1 Hierarchy Enforcement — Only L1 can override L2 decisions
        2. Scope Isolation — L3 cannot claim cross-domain authority
        3. Evidence Quality — Recommendations must be traceable
        4. Language Safety — No企业腔/学术腔/PR腔/创始人腔
        5. Handoff Completeness — Cross-script calls must use handoff_prepare()
        6. Confidentiality — Internal reasoning not exposed in output

    Authorization matrix (public interface):
        ┌─────────────────────────┬──────────────────────────────────────────────┐
        │ Action                  │ Who Can Do It                               │
        ├─────────────────────────┼──────────────────────────────────────────────┤
        │ L2 decision override    │ L1 only                                      │
        │ L3 direct dispatch      │ L2 only (not L1)                             │
        │ Cross-domain data pull  │ L2 coordination required                      │
        │ New skill registration  │ IT department audit required                  │
        │ Council output delivery │ IT audit + L1 confirmation required           │
        │ Autobiography read      │ Any L2+ actor                                 │
        └─────────────────────────┴──────────────────────────────────────────────┘

    NOT disclosed (proprietary):
        • The actual pattern matchers and threshold values
        • The SOUL constraint rule database
        • The escalation routing tables
        • The language safety scoring algorithm
    """

    def __init__(self, hermes_home: str = None):
        import os
        from pathlib import Path
        self.hermes_home = Path(hermes_home or os.path.expanduser("~/.hermes"))
        self.events_file = self.hermes_home / "events" / "events.jsonl"
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        self._constraint_db = None  # Proprietary — loaded separately

    def audit(self, output: str, context: Dict) -> AuditResult:
        """
        Audit an L3 output through the SOUL constraint layer.

        Args:
            output: The L3 script's raw output string
            context: {
                "actor": str,        # L1 / L2 / L3 / COUNCIL / EXTERNAL
                "task": str,         # Original task description
                "domain": str,       # e.g. "it", "ecommerce"
                "intended_recipient": str,  # "user" / "l2" / "l1"
            }

        Returns:
            AuditResult with:
                verdict: PASS | FLAG | BLOCK
                flags: List of annotation strings
                redacted_content: Filtered version (if BLOCK)
                event_log: For compliance trail
                annotations: Advisory notes attached to output
        """
        flags = []
        annotations = []
        redacted = output

        # ── Dimension 1: L1 Hierarchy Enforcement ─────────────────────────────
        if self._violates_hierarchy(output, context):
            flags.append("VIOLATION: L3 attempted L1-level action")
            redacted = self._redact_hierarchy_violation(output)

        # ── Dimension 2: Scope Isolation ─────────────────────────────────────
        if self._violates_scope(output, context):
            flags.append("FLAG: Cross-domain authority claim detected")

        # ── Dimension 3: Evidence Quality ────────────────────────────────────
        evidence_score = self._score_evidence(output, context)
        if evidence_score < 0.5:
            annotations.append("⚠️ LOW EVIDENCE — recommendations not fully grounded")

        # ── Dimension 4: Language Safety ─────────────────────────────────────
        lang_flags = self._check_language_safety(output)
        flags.extend(lang_flags)

        # ── Dimension 5: Handoff Completeness ────────────────────────────────
        if not self._has_complete_handoff(output):
            flags.append("FLAG: Handoff protocol not followed")

        # ── Dimension 6: Confidentiality ──────────────────────────────────────
        conf_flags = self._check_confidentiality(output, context)
        flags.extend(conf_flags)

        # Determine verdict
        has_block = any(v in str(flags) for v in ["VIOLATION", "BLOCK"])
        verdict = Verdict.BLOCK if has_block else (Verdict.FLAG if flags else Verdict.PASS)

        # Log event
        event = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": "soul_audit",
            "actor": context.get("actor", "unknown"),
            "domain": context.get("domain", "unknown"),
            "verdict": verdict.value,
            "flags": flags,
            "output_length": len(output),
        }
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        return AuditResult(
            verdict=verdict,
            flags=flags,
            redacted_content=redacted if verdict == Verdict.BLOCK else output,
            event_log=event,
            annotations=annotations,
        )

    def check_authorization(self, action: str, actor: str) -> AuthorizationResult:
        """
        Check if an actor is authorized to perform an action.

        Args:
            action: e.g. "l2_decision_override", "l3_dispatch", "council_output_delivery"
            actor: The role attempting the action

        Returns:
            AuthorizationResult with:
                authorized: bool
                reason: str
                requires_escalation: bool
        """
        # Authorization matrix (from SOUL.md)
        matrix = {
            "l2_decision_override": {"L1": True, "L2": False, "L3": False, "COUNCIL": False, "EXTERNAL": False},
            "l3_dispatch": {"L1": False, "L2": True, "L3": False, "COUNCIL": False, "EXTERNAL": False},
            "cross_domain_data": {"L1": True, "L2": True, "L3": False, "COUNCIL": False, "EXTERNAL": False},
            "skill_registration": {"L1": True, "L2": False, "L3": False, "COUNCIL": False, "EXTERNAL": False},
            "council_output_delivery": {"L1": True, "L2": False, "L3": False, "COUNCIL": True, "EXTERNAL": False},
            "autobiography_read": {"L1": True, "L2": True, "L3": False, "COUNCIL": False, "EXTERNAL": False},
        }

        allowed_roles = matrix.get(action, {})
        authorized = allowed_roles.get(actor, False)

        return AuthorizationResult(
            authorized=authorized,
            reason="Allowed" if authorized else f"{actor} not authorized for {action}",
            requires_escalation=not authorized,
        )

    def escalate(self, conflict: Dict) -> Dict:
        """
        Route an unresolvable conflict to L1 CEO arbitration.

        Args:
            conflict: {
                "type": str,         # e.g. "inter_domain", "authority_conflict"
                "parties": List[str], # Domains/actors in conflict
                "issue": str,         # Description of conflict
                "attempts_resolved": List[str],  # What was tried
            }

        Returns:
            Escalation routing decision from L1
        """
        event = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": "soul_escalation",
            "conflict_type": conflict.get("type"),
            "parties": conflict.get("parties"),
            "issue": conflict.get("issue"),
        }
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        return {
            "escalated_to": "L1_CEO",
            "reason": "Unresolvable conflict — requires CEO arbitration",
            "event_logged": event,
            "pending_resolution": True,
        }

    # ── Private Audit Dimensions (algorithms proprietary) ─────────────────────

    def _violates_hierarchy(self, output: str, context: Dict) -> bool:
        """
        Check for L1 hierarchy violations.

        INTEGRATION GUIDE:
        Replace with your own pattern-matching or ML-based violation detector.
        Your detector should scan the council output text for signs that
        the advisor is attempting to override L1/L2 authority.

        Args:
            output: Raw text from an advisor response
            context: Dict with metadata (actor, domain, etc.)

        Returns:
            True if a violation is detected (blocks output).

        Raises:
            NotImplementedError: Always — implement your own detector.
        """
        raise NotImplementedError(
            "SPEC_SHEET_ONLY: SoulArbiter._violates_hierarchy is a规格说明书型 interface. "
            "Implement your own hierarchy-violation detector: regex, LLM classify, or rule engine. "
            "Return True if the output violates the L1/L2/L3 authority boundary."
        )

    def _violates_scope(self, output: str, context: Dict) -> bool:
        """
        Check for cross-domain authority claims.

        INTEGRATION GUIDE:
        Replace with your own scope-checking logic.
        Detects when an advisor comments outside its designated domain
        (e.g., strategic advisor attempting a technical architecture decision).

        Args:
            output: Raw text from an advisor response
            context: Dict with advisor_type, domain, etc.

        Returns:
            True if an out-of-scope claim is detected.

        Raises:
            NotImplementedError: Always — implement your own scope checker.
        """
        raise NotImplementedError(
            "SPEC_SHEET_ONLY: SoulArbiter._violates_scope is a规格说明书型 interface. "
            "Implement your own out-of-scope detector for advisor outputs. "
            "Return True if an advisor steps outside its mandate domain."
        )

    def _score_evidence(self, output: str, context: Dict) -> float:
        """
        Score evidence quality in advisor output.

        INTEGRATION GUIDE:
        Replace with your own evidence-quality scoring rubric. Options:
          - Rule-based: count citations, source links, data points
          - LLM classify: grade evidence as STRONG/MEDIUM/WEAK
          - Heuristic: penalize vague language, reward specific numbers

        Args:
            output: Raw text from an advisor response
            context: Dict with metadata

        Returns:
            float: Evidence quality score 0.0–1.0.

        Raises:
            NotImplementedError: Always — implement your own scoring rubric.
        """
        raise NotImplementedError(
            "SPEC_SHEET_ONLY: SoulArbiter._score_evidence is a规格说明书型 interface. "
            "Implement your own evidence-quality scorer. "
            "Return a float 0.0–1.0 (1.0 = strong evidence, 0.0 = no evidence)."
        )

    def _check_language_safety(self, output: str) -> List[str]:
        """
        Check for prohibited language styles.
        Prohibited: 企业腔 / 学术腔 / PR腔 / 创始人腔
        Prohibited fillers: 其实 / 基本上 / 大概 / 总体来说
        """
        flags = []
        prohibited = ["实际上", "从宏观来看", "我们致力于", "非常", "极其", "显著地"]
        for word in prohibited:
            if word in output:
                flags.append(f"PROHIBITED_LANGUAGE: '{word}'")
        return flags

    def _has_complete_handoff(self, output: str) -> bool:
        """Check if cross-script calls use handoff protocol."""
        # Simple heuristic — actual protocol check proprietary
        return "handoff" in output.lower() or "ready_for" in output.lower()

    def _check_confidentiality(self, output: str, context: Dict) -> List[str]:
        """Check for internal reasoning exposed in output."""
        flags = []
        confidential_markers = ["[INTERNAL]", "[CONFIDENTIAL]", "内部推理"]
        for marker in confidential_markers:
            if marker in output:
                flags.append(f"CONFIDENTIALITY: '{marker}' exposed in output")
        return flags

    def _redact_hierarchy_violation(self, output: str) -> str:
        """Remove hierarchy-violating content."""
        return "[REDACTED: SOUL violation — L1 authority required]"
