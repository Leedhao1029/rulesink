#!/usr/bin/env python3
"""
Enterprise Advisory Council
advisory_council.py

A temporary, advisory-only expert panel. When the CEO faces a complex decision,
the council is convened to provide concurrent multi-perspective analysis.

Council Structure:
    ┌─────────────────────────────────────────────────────────────┐
    │              ENTERPRISE ADVISORY COUNCIL                   │
    │                                                             │
    │  Question ──▶ [STRATEGIC] ──┐                              │
    │             ──▶ [TECHNICAL] ──┼──▶ Synthesis ──▶ CEO        │
    │             ──▶ [RISK]      ──┤                              │
    │             ──▶ [EVOLUTION] ──┘                              │
    │                                                             │
    │  ⚠️ Advisory only — does NOT replace any L2 decision authority│
    │  ⚠️ Does NOT execute tasks — no L3 dispatch capability       │
    └─────────────────────────────────────────────────────────────┘

Four Advisors (each is an independent analysis agent):

  1. STRATEGIC ADVISOR
     Role: Business value assessment
     Questions answered:
         • What is the business impact?
         • Is this the right time?
         • What are the opportunity costs?
         • How does this align with company strategy?

  2. TECHNICAL ADVISOR
     Role: Feasibility and architecture
     Questions answered:
         • Is this technically achievable?
         • What are the integration risks?
         • What is the complexity estimate?
         • Are there better architectural approaches?

  3. RISK ADVISOR
     Role: Risk and compliance review
     Questions answered:
         • What compliance obligations apply?
         • What is the security surface?
         • What tail risks exist?
         • What mitigation strategies reduce exposure?

  4. EVOLUTION ADVISOR
     Role: Organizational learning
     Questions answered:
         • Can patterns from this be generalized?
         • What skill gaps does this reveal?
         • Should this become a new L3 script?
         • Does this create a process improvement opportunity?

Council Governance:
    • IT Department (L2 IT) is the permanent owner/administrator
    • IT audits all council outputs before delivery to CEO
    • Council outputs are advisory only — L2 retains full decision authority
    • Patterns extracted from approved decisions are auto-registered as skills

This is a PUBLIC architectural preview (~300 lines).
The full council implementation (~1,033 lines) is proprietary.

Public Interface:
    AdvisoryCouncil.convene(question: str, context: dict) -> CouncilResult
    AdvisoryCouncil.get_advisor(name: str) -> Advisor
    AdvisoryCouncil.audit_output(result: dict) -> AuditResult
    AdvisoryCouncil.extract_patterns(result: dict) -> List[Pattern]
"""

import json
import importlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

# ── Advisor Registry ───────────────────────────────────────────────────────────────

class AdvisorType(Enum):
    STRATEGIC = "strategic"
    TECHNICAL = "technical"
    RISK = "risk"
    EVOLUTION = "evolution"


ADVISOR_NAMES = {
    "strategic": "Strategic Advisor",
    "technical": "Technical Advisor",
    "risk": "Risk Advisor",
    "evolution": "Evolution Advisor",
}


# ── Council Result Structure ─────────────────────────────────────────────────────

class CouncilResult:
    """
    Standard return type from AdvisoryCouncil.convene().

    Schema:
        {
            "convene_id": str,              # UUID for this session
            "convened_at": ISO8601,
            "question": str,
            "context": dict,
            "advisor_responses": {
                "strategic": { ... },
                "technical": { ... },
                "risk": { ... },
                "evolution": { ... },
            },
            "synthesis": {
                "summary": str,
                "key_insights": List[str],
                "recommendations": List[str],
                "dissent_noted": List[str],    # Advisor disagreements
                "confidence": float,           # 0–1 overall confidence
            },
            "audit": {
                "passed": bool,
                "flags": List[str],
                "it_auditor": str,
                "audited_at": ISO8601,
            },
            "patterns": List[Pattern],         # Extracted for skill registration
            "handoff_status": str,             # "ready_for_ceo" | "blocked_by_audit"
        }
    """


class AdvisorResponse:
    """
    Standard format for each advisor's response.

    Schema:
        {
            "advisor": str,          # e.g. "Strategic Advisor"
            "analysis": str,         # Full written analysis
            "verdict": str,          # SUPPORT / RESERVE / OPPOSE
            "key_points": List[str], # 3–5 bullet findings
            "evidence": List[str],   # Supporting data/reasoning
            "confidence": float,    # Advisor's own confidence (0–1)
            "limitations": str,     # Known blind spots
        }
    """


class Pattern:
    """
    Extracted pattern from a decision for potential skill registration.

    Schema:
        {
            "pattern_id": str,
            "extracted_from": str,      # convene_id
            "pattern_type": str,        # PROCESS / DECISION_RULE / HEURISTIC
            "description": str,
            "trigger_conditions": List[str],
            "action": str,
            "quality_score": float,
            "approval_status": str,     # PENDING | APPROVED | REJECTED
        }
    """


# ── AdvisoryCouncil Class ─────────────────────────────────────────────────────────

class AdvisoryCouncil:
    """
    Temporary expert panel — convened per-question, no standing membership.

    IT Department responsibilities (owner):
        • Builds and maintains the council infrastructure
        • Provides each advisor with appropriate context
        • Audits all outputs before delivery
        • Extracts and registers patterns from approved decisions

    What council CANNOT do:
        • Cannot replace L2 decision authority
        • Cannot dispatch L3 scripts directly
        • Cannot force implementation of its recommendations
        • Cannot override SOUL.md constraints
    """

    def __init__(self, hermes_home: str = None):
        import os
        from pathlib import Path

        self.hermes_home = Path(hermes_home or os.path.expanduser("~/.hermes"))
        self.council_log = self.hermes_home / "council" / "council_log.jsonl"
        self.patterns_dir = self.hermes_home / "council" / "patterns"
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.council_log.parent.mkdir(parents=True, exist_ok=True)

        # Load IT audit module (proprietary)
        self._audit_module = self._load_audit_module()

    def convene(self, question: str, context: Optional[Dict] = None) -> CouncilResult:
        """
        Convene all four advisors concurrently for a question.

        Each advisor receives:
            • The original question
            • The full context dict
            • The SOUL.md constraint layer reference

        Advisors run in parallel (concurrent execution).
        Each advisor produces an independent analysis.

        After all advisors respond:
            1. Synthesis agent produces overall summary
            2. IT audit runs on all outputs
            3. Patterns are extracted
            4. Final result is assembled and logged
        """
        import uuid

        convene_id = str(uuid.uuid4())[:8]
        ctx = context or {}

        # Parallel advisor analysis
        advisor_responses = self._run_advisors_parallel(question, ctx)

        # Synthesis
        synthesis = self._synthesize(advisor_responses, question)

        # IT Audit (mandatory — council output cannot reach CEO without audit)
        audit = self._audit_council_output(advisor_responses, synthesis)

        # Extract patterns
        patterns = self._extract_patterns(advisor_responses, synthesis, convene_id)

        result = {
            "convene_id": convene_id,
            "convened_at": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "context": ctx,
            "advisor_responses": advisor_responses,
            "synthesis": synthesis,
            "audit": audit,
            "patterns": patterns,
            "handoff_status": "ready_for_ceo" if audit["passed"] else "blocked_by_audit",
        }

        # Log
        with open(self.council_log, "a") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

        return result

    def get_advisor(self, name: str) -> Dict:
        """Return a specific advisor by name (strategic/technical/risk/evolution)."""
        return {
            "name": ADVISOR_NAMES.get(name.lower()),
            "type": name.lower(),
            "questions_answered": self._advisor_questions(name.lower()),
        }

    def audit_output(self, result: Dict) -> Dict:
        """
        IT Department audit of council output.

        Audit dimensions:
            • Factual accuracy of claims
            • No unauthorized L3 dispatch attempts
            • No SOUL.md constraint violations
            • Pattern quality sufficient for registration
            • No recommendation exceeds council mandate
        """
        return self._audit_council_output(
            result.get("advisor_responses", {}),
            result.get("synthesis", {}),
        )

    # ── Private Methods ──────────────────────────────────────────────────────

    def _run_advisors_parallel(self, question: str, context: Dict) -> Dict[str, AdvisorResponse]:
        """
        Run all four advisors concurrently.
        Each advisor is an independent analysis agent.

        The advisor implementations (prompts, model calls) are proprietary.
        This method shows the orchestration contract.
        """
        # Placeholder — actual advisor agents are proprietary
        return {
            "strategic": self._advisor_response("strategic", question, context),
            "technical": self._advisor_response("technical", question, context),
            "risk": self._advisor_response("risk", question, context),
            "evolution": self._advisor_response("evolution", question, context),
        }

    def _advisor_response(self, advisor_type: str, question: str, context: Dict) -> Dict:
        """
        Generate a single advisor's response.

        ADVISOR INTEGRATION GUIDE (for external developers):
        ─────────────────────────────────────────────────
        This method is the adapter point for each advisor's analysis engine.
        Replace the body with your own logic: prompt engineering, model calls, etc.

        Required return dict shape (all fields mandatory for synthesis + audit):
            {
                "advisor": str,           # Display name, e.g. "Strategic Advisor"
                "analysis": str,          # Full analysis text
                "verdict": str,           # "ADOPT" | "REJECT" | "REFER" | "RESERVE"
                "key_points": List[str], # 2-5 concrete findings
                "evidence": List[str],   # Citations, data sources, reasoning traces
                "confidence": float,     # 0.0–1.0 (0.9+ requires non-empty evidence)
                "limitations": str,       # Known blind spots or data gaps
            }

        Args:
            advisor_type: One of "strategic" | "technical" | "risk" | "evolution"
            question: The CEO's convened question
            context: Dict with relevant background data (domain, history, constraints)

        Raises:
            NotImplementedError: Always — this is a spec sheet, not an implementation.
                                 Replace with your advisor logic before use.
        """
        raise NotImplementedError(
            "SPEC_SHEET_ONLY: advisory_council._advisor_response is a规格说明书型 "
            "interface — replace with your own analysis engine. "
            "Your engine must return the structured dict described in the docstring above. "
            "The {advisor_type} advisor slot is ready for injection."
        )

    def _synthesize(self, responses: Dict, question: str) -> Dict:
        """
        Synthesize four advisor responses into a coherent summary.

        SYNTHESIS INTEGRATION GUIDE (for external developers):
        ─────────────────────────────────────────────────────────
        This method receives the four advisor response dicts and must produce
        a unified synthesis. Replace the body with your own merging logic:
        conflict resolution, priority ranking, recommendation aggregation, etc.

        Required return dict shape:
            {
                "summary": str,              # 2-3 sentence executive synthesis
                "key_insights": List[str],  # Top cross-advisor insights
                "recommendations": List[str], # Actionable recommendations
                "dissent_noted": List[str], # Minority opinions worth noting
                "confidence": float,        # Synthesis confidence 0.0–1.0
            }

        Args:
            responses: Dict keyed by advisor type ("strategic", "technical", "risk", "evolution")
            question: The original CEO question

        Raises:
            NotImplementedError: Always — this is a规格说明书型 interface.
                                 Replace with your own synthesis algorithm.
        """
        raise NotImplementedError(
            "SPEC_SHEET_ONLY: advisory_council._synthesize is a规格说明书型 interface. "
            "Your synthesis algorithm should receive 4 advisor response dicts and return "
            "the structured synthesis dict described in the docstring above."
        )

    def _audit_council_output(self, responses: Dict, synthesis: Dict) -> Dict:
        """
        IT Department mandatory audit of council outputs.

        This is the IT Department's gate — no council output reaches the CEO
        without passing through this audit.

        Audit checks (replace the boolean logic below with your own rule engine):
            1. Factual accuracy — no hallucinated claims
            2. Mandate compliance — no L3 dispatch or L2 override attempts
            3. SOUL compliance — no constraint violations
            4. Pattern quality — extracted patterns meet registration bar
            5. Evidence level — recommendations traceable to evidence

        REQUIRED return dict shape:
            {
                "passed": bool,           # True = deliver to CEO; False = block
                "flags": List[str],       # List of violation descriptions
                "it_auditor": str,        # "IT Department (advisory_council.py)"
                "audited_at": str,        # ISO timestamp
            }

        NOT disclosed: The specific audit rule engine and threshold values.
        Replace the flag-checking logic below with your own rule engine.

        Args:
            responses: Dict of all 4 advisor responses
            synthesis: Dict returned by _synthesize()

        Raises:
            NotImplementedError: Always — the rule engine is proprietary.
                                 Implement your own audit logic before use.
        """
        raise NotImplementedError(
            "SPEC_SHEET_ONLY: advisory_council._audit_council_output is a规格说明书型 interface. "
            "Your audit rule engine should receive all advisor responses + synthesis, "
            "return the structured audit dict shown in the docstring above. "
            "The audit logic (flag detection, threshold checks) is your implementation."
        )

    def _extract_patterns(self, responses: Dict, synthesis: Dict, convene_id: str) -> List[Dict]:
        """
        Extract reusable patterns from approved council decisions.

        Pattern types:
            PROCESS          — Repeating workflow or procedure
            DECISION_RULE    — If-then decision logic
            HEURISTIC        — Practitioner rule-of-thumb

        Extraction criteria (replace with your own scoring thresholds):
            • Quality score ≥ your_threshold
            • Evidence level sufficient
            • Trigger conditions clearly definable
            • Not already in skill registry

        REQUIRED return dict shape for each pattern:
            {
                "pattern_id": str,           # e.g. "pat_<convene_id>_<n>"
                "extracted_from": str,       # convene_id
                "pattern_type": str,         # "PROCESS" | "DECISION_RULE" | "HEURISTIC"
                "description": str,           # Human-readable description
                "trigger_conditions": List[str],
                "action": str,                # The recommended action
                "quality_score": float,      # Your quality assessment
                "approval_status": str,      # Always "PENDING" — requires human approval
            }

        Args:
            responses: Dict of 4 advisor responses
            synthesis: Dict returned by _synthesize()
            convene_id: Unique ID of this council convening

        Raises:
            NotImplementedError: Always — the extraction algorithm is proprietary.
                                 Implement your own pattern detection before use.
        """
        raise NotImplementedError(
            "SPEC_SHEET_ONLY: advisory_council._extract_patterns is a规格说明书型 interface. "
            "Your extraction algorithm should analyze advisor responses + synthesis "
            "and return the structured pattern list described in the docstring above. "
            "Set approval_status='PENDING' for all extracted patterns — "
            "only L1/IT can promote them to the skill registry."
        )

    def _load_audit_module(self):
        """
        Load the IT audit module for council output verification.

        ADVISOR INTEGRATION GUIDE:
        This is where you wire in your external audit service, e.g.:
          - A separate hermes-audit package
          - A REST API call to your compliance service
          - A local rule-engine module you own

        Returns:
            Your audit module instance, or None if not wired yet.

        Raises:
            NotImplementedError: Always — implement your own audit module loader.
        """
        raise NotImplementedError(
            "SPEC_SHEET_ONLY: advisory_council._load_audit_module is a规格说明书型 interface. "
            "Wire in your own IT audit module here (class or API endpoint). "
            "Return the module instance — or None if audit is not yet wired."
        )

    def _advisor_questions(self, advisor_type: str) -> List[str]:
        """Return the questions each advisor type is designed to answer."""
        questions = {
            "strategic": [
                "What is the business value?",
                "Is this the right timing?",
                "What are the opportunity costs?",
                "How does this align with company strategy?",
            ],
            "technical": [
                "Is this technically achievable?",
                "What are the integration risks?",
                "What is the complexity estimate?",
                "Are there better architectural approaches?",
            ],
            "risk": [
                "What compliance obligations apply?",
                "What is the security surface?",
                "What tail risks exist?",
                "What mitigation strategies reduce exposure?",
            ],
            "evolution": [
                "Can patterns from this be generalized?",
                "What skill gaps does this reveal?",
                "Should this become a new L3 script?",
                "Does this create a process improvement opportunity?",
            ],
        }
        return questions.get(advisor_type, [])


# ── CLI Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        council = AdvisoryCouncil()
        result = council.convene(question)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python3 advisory_council.py <question>")
        print("Example: python3 advisory_council.py 'Should we adopt a microservices architecture?'")
