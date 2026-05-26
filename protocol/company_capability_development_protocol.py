#!/usr/bin/env python3
"""
Company Capability Development Standard Protocol (CCDSP)
Chapter-level implementation

This is the public governance framework for all organizational capability
development in the 矩墨RulesInk.

Full 7-chapter text available in:
    skills/company-capability-development-protocol/SKILL.md

This file provides the machine-readable protocol constants and class definitions.
The full narrative text (what each chapter means and how to apply it) is
in the SKILL.md file.
"""

from enum import Enum
from typing import List, Dict
from dataclasses import dataclass


# ── Core Principles ───────────────────────────────────────────────────────────────

CORE_PRINCIPLES = [
    "自主进化权",    # Each L2 owns its self-evolution module
    "贡献有价值",    # All contributions must pass quality bar
    "共享归属公司",  # Cross-domain capabilities belong to company
    "透明追溯",      # All decisions have audit trail
    "五步闭环",      # Build → Self-test → Propose → Approve → Register → Archive
]


# ── Approval Tiers ──────────────────────────────────────────────────────────────

class ApprovalTier(Enum):
    TIER_1_DOMAIN = 1  # Domain-L2 only — skill update within same domain
    TIER_2_CROSS = 2   # Cross-L2 + L1 — new skill or cross-domain capability
    TIER_3_GLOBAL = 3  # All-L2 + L1 — new L2 domain or fundamental protocol change


APPROVAL_REQUIREMENTS = {
    ApprovalTier.TIER_1_DOMAIN: ["domain_L2_approval"],
    ApprovalTier.TIER_2_CROSS: ["domain_L2_approval", "L1_approval"],
    ApprovalTier.TIER_3_GLOBAL: ["all_L2_approval", "L1_approval"],
}


# ── Contribution Workflow ───────────────────────────────────────────────────────

WORKFLOW_STEPS = [
    "BUILD",       # Domain builds new capability via self-evolution module
    "SELF_TEST",   # Passes through domain check mode
    "PROPOSE",     # Generates contribution proposal with impact analysis
    "APPROVE",     # Tiered approval (see ApprovalTier)
    "REGISTER",    # Add to L3 script library + skill catalog
    "ARCHIVE",     # Record in autobiography for traceability
]


# ── Quality Standards ────────────────────────────────────────────────────────────

class SkillQualityStandard:
    """Standards for new skill registration."""
    MIN_WORDS = 500
    REQUIRED_CHAPTERS = ["Steps", "Pitfalls", "Examples", "Verification"]
    REQUIRED_FRONTMATTER = ["name", "description", "trigger_on"]


class L3ScriptQualityStandard:
    """Standards for new L3 script registration."""
    REQUIRED_BASE = "L3Base"
    REQUIRED_METHOD = "run"
    REQUIRED_FIELDS = ["quality_status", "handoff", "evidence", "issues"]
    PROTOCOL_FIELDS = ["ready_for", "needs_from", "constraints"]


# ── Issue Classification ─────────────────────────────────────────────────────────

ISSUE_CATEGORIES = [
    "MISSING_SKILL",      # Operational scenario with no skill
    "WEAK_SKILL",         # Skill exists but lacks depth
    "BROKEN_SCRIPT",       # L3 script fails to load or run
    "STALE_ARCHIVE",       # Archive not updated in N days
    "ARCHITECTURAL",       # Pattern-level failure
]

ISSUE_SEVERITY = [
    "CRITICAL",  # Blocks execution or data loss risk
    "WARNING",   # Degrades quality or efficiency
    "MINOR",     # Cosmetic or edge case
]


# ── Cross-Domain Rules ───────────────────────────────────────────────────────────

@dataclass
class CrossDomainCoordination:
    """Rules for cross-domain task coordination."""
    primary_domain: str
    supporting_domains: List[str]
    data_contract_required: bool
    escalation_path: str  # "L1_CEO"


# ── IT Department Role ───────────────────────────────────────────────────────────

IT_DEPARTMENT_MANDATES = [
    "Build and maintain L2 orchestrator infrastructure",
    "Own the self-evolution framework across all domains",
    "Audit all council outputs before CEO delivery",
    "Maintain the skill registry and quality standards",
    "Operate the forge queue and approval workflow",
    "NOT build domain-specific capabilities FOR other domains",
    "Platform role: build tools, not deliver services",
]
