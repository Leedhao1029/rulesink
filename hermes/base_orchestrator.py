#!/usr/bin/env python3
"""
Base L2 Orchestrator Interface
base_orchestrator.py

Abstract base class defining the standard interface for all L2 orchestrators.
All domain orchestrators (IT, Ecommerce, Construction, etc.) inherit from
this base class and implement the abstract methods.

Public Interface:
    discover_l3_modules()  → List[L3Module]
    plan(task, context)    → OrchestrationPlan
    execute(plan)         → ExecutionResult
    report(result)        → str

Standard L2 Attributes:
    SCRIPT_DIR  — Path to L3 scripts
    SKILL_DIR   — Path to skills
    domain      — Domain name (e.g. "it", "ecommerce")
    VENV_PY     — Python venv path

Standard L3 Discovery:
    All L3 scripts are auto-discovered by naming convention:
        l3_{domain}_{name}.py  →  domain="...", name="..."
    The orchestrator finds all matching scripts without hardcoding.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional


class L3Module:
    """Represents a discovered L3 module."""
    def __init__(self, name: str, path: Path, skill_name: str = None):
        self.name = name           # e.g. "l3_it_code_review"
        self.path = path           # Absolute path to .py file
        self.skill_name = skill_name or name


class OrchestrationPlan:
    """Plan produced by L2.plan()."""
    def __init__(self, task: str, lane: str, modules: List[L3Module],
                 order: str, context: dict):
        self.task = task
        self.lane = lane          # "fast" | "standard" | "full"
        self.modules = modules
        self.order = order         # "sequential" | "parallel"
        self.context = context


class ExecutionResult:
    """Result from L2.execute()."""
    def __init__(self, plan: OrchestrationPlan, l3_outputs: List[dict],
                 errors: List[str], quality_status: str):
        self.plan = plan
        self.l3_outputs = l3_outputs
        self.errors = errors
        self.quality_status = quality_status  # "PASS" | "NEEDS_WORK"


class BaseOrchestrator(ABC):
    """
    Abstract base class for all L2 domain orchestrators.

    All domain orchestrators MUST:
        1. Inherit from BaseOrchestrator
        2. Implement: discover_l3_modules(), plan(), execute(), report()
        3. Use the standard five-step loop (Perceive/Plan/Execute/Verify/Memorize)
        4. Log all dispatches to events.jsonl via write_event()
        5. Run SOUL arbiter on all outputs before delivery
    """

    SCRIPT_DIR: Path = None  # Set in subclass
    SKILL_DIR: Path = None   # Set in subclass
    domain: str = "base"

    def __init__(self):
        if not self.SCRIPT_DIR:
            hermes_home = Path.home() / ".hermes"
            self.SCRIPT_DIR = hermes_home / "scripts"
            self.SKILL_DIR = hermes_home / "skills"
        self.archive_dir = self.SCRIPT_DIR / f"{self.domain}_archive"
        self.archive_dir.mkdir(exist_ok=True)

    @abstractmethod
    def discover_l3_modules(self) -> List[L3Module]:
        """
        Auto-discover all L3 scripts for this domain.

        Discovery rule:
            Pattern: l3_{domain}_*.py
            Each script is loaded to extract SKILL_NAME

        Returns:
            List of L3Module objects, sorted by skill_name
        """
        ...

    @abstractmethod
    def plan(self, task: str, context: Optional[dict] = None) -> OrchestrationPlan:
        """
        Classify task → select L3 skills → build execution DAG.

        Steps:
            1. Extract keywords from task
            2. Match against L3 module skill_names
            3. Assess complexity → determine lane (fast/standard/full)
            4. Build execution order (sequential or parallel)
            5. Return OrchestrationPlan

        Returns:
            OrchestrationPlan with selected modules and execution order
        """
        ...

    @abstractmethod
    def execute(self, plan: OrchestrationPlan) -> ExecutionResult:
        """
        Run selected L3 modules according to plan.

        For "parallel" order: modules run concurrently (ThreadPoolExecutor)
        For "sequential" order: modules run in dependency order

        Each module is run in a subprocess with the task as input.
        Results are collected and returned as ExecutionResult.

        Returns:
            ExecutionResult with l3_outputs, errors, quality_status
        """
        ...

    @abstractmethod
    def report(self, result: ExecutionResult) -> str:
        """
        Synthesize L3 outputs into domain-specific human-readable report.

        Returns:
            Markdown-formatted string suitable for delivery to user
        """
        ...

    # ── Standard Helper Methods ─────────────────────────────────────────────────

    def find_l3_by_skill(self, skill_name: str) -> Optional[L3Module]:
        """Find a specific L3 module by skill name."""
        modules = self.discover_l3_modules()
        for m in modules:
            if m.skill_name == skill_name:
                return m
        return None

    def find_l3_by_keyword(self, keyword: str) -> List[L3Module]:
        """Find all L3 modules whose skill_name contains the keyword."""
        modules = self.discover_l3_modules()
        return [m for m in modules if keyword.lower() in m.skill_name.lower()]
