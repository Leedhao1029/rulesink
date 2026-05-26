#!/usr/bin/env python3
"""
L3 Base — Standard Foundation for All Skill Agents

Every L3 script in the Hermes ecosystem inherits from L3Base,
which enforces a standardized interface, return format, and lifecycle.

Public Interface (L3Base):
    run(params: dict) -> dict
    analyze(task: str) -> dict           # Standard entry point
    verify_output(result, required_fields) -> dict
    finalize(result) -> dict

    remember(key, value, tags) -> bool   # Project memory
    recall(key) -> Optional[Any]          # Project memory recall
    handoff_prepare(to_script, output)   # Cross-script handoff
    get_data(preferred_source, **kwargs) # 3-tier data source

Standard Return Format (enforced by finalize):
    {
        "script_name": str,
        "version": str,
        "timestamp": ISO8601,
        "quality_status": "PASS" | "NEEDS_WORK",
        "handoff": {
            "ready_for": List[str],    # Downstream consumers
            "needs_from": List[str],    # Required inputs
            "pending": List[str],       # Undone work
            "constraints": List[str],   # Constraints for downstream
        },
        "evidence": dict,
        "issues": List[str],
        ... (script-specific fields)
    }

Data Source Priority (get_data):
    1. "api"    — Real API calls
    2. "local"  — Local database / files
    3. "mock"   — Mock data (⚠️ MOCK_MARKER attached)

For the full L3Base implementation (350 lines), see l3_base.py
in the proprietary Hermes Agent distribution.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Constants ─────────────────────────────────────────────────────────────────────────

MEMORY_DIR = Path.home() / ".hermes" / "project_memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

HANDOFF_DIR = Path.home() / ".hermes" / "handoffs"
HANDOFF_DIR.mkdir(parents=True, exist_ok=True)


# ── L3Base Class ──────────────────────────────────────────────────────────────────

class L3Base:
    """
    Standard base class for all L3 skill agents.

    Inheritance requirement:
        Every L3 script in the Hermes ecosystem MUST inherit from L3Base
        and implement: run(params: dict) -> dict
    """

    SCRIPT_NAME: str = "l3-base"
    VERSION: str = "1.0"
    DEFAULT_STATUS: str = "NEEDS_WORK"  # Default: work required before delivery

    def __init__(self, project: str = "default"):
        self.project = project
        self.project_memory_dir = MEMORY_DIR / project
        self.project_memory_dir.mkdir(parents=True, exist_ok=True)
        self.handoff_dir = HANDOFF_DIR / project
        self.handoff_dir.mkdir(parents=True, exist_ok=True)

    # ── Standard Return Format ──────────────────────────────────────────────────

    def standard_header(self, quality_status: str = None) -> dict:
        """Generate standard return header."""
        return {
            "script_name": self.SCRIPT_NAME,
            "version": self.VERSION,
            "timestamp": datetime.now().isoformat(),
            "quality_status": quality_status or self.DEFAULT_STATUS,
            "handoff": {
                "ready_for": [],
                "needs_from": [],
                "pending": [],
                "constraints": [],
            },
            "evidence": {},
            "issues": [],
        }

    def verify_output(self, result: dict, required_fields: List[str]) -> dict:
        """
        Verify that output contains all required fields.
        Returns {"pass": bool, "issues": List[str], "quality_status": str}
        """
        issues = []
        for field in required_fields:
            if field not in result or result[field] is None:
                issues.append(f"Missing required field: {field}")
            elif isinstance(result[field], (list, dict)) and len(result[field]) == 0:
                issues.append(f"Empty required field: {field}")

        quality_status = "PASS" if not issues else "NEEDS_WORK"
        return {"pass": not issues, "issues": issues, "quality_status": quality_status}

    def finalize(self, result: dict, quality_status: str = None) -> dict:
        """
        Finalize result: inject standard header + verify quality status.
        All L3 scripts MUST call finalize() before returning.
        """
        if "_header_injected" in result:
            return result

        header = self.standard_header(quality_status or self.DEFAULT_STATUS)
        header["_header_injected"] = True
        final = {**header, **result}

        if "handoff" in result:
            final["handoff"] = {**header["handoff"], **result["handoff"]}

        if quality_status:
            final["quality_status"] = quality_status
        elif result.get("issues") and len(result.get("issues", [])) > 0:
            final["quality_status"] = "NEEDS_WORK"
        elif result.get("_verified") == True:
            final["quality_status"] = "PASS"

        return final

    # ── Memory Interface ────────────────────────────────────────────────────────

    def remember(self, key: str, value: Any, tags: List[str] = None) -> bool:
        """Store value to project memory."""
        ...

    def recall(self, key: str, tags: List[str] = None) -> Optional[Any]:
        """Recall value from project memory."""
        ...

    def recall_all(self, tags: List[str] = None) -> Dict[str, Any]:
        """Recall all memories matching given tags."""
        ...

    # ── Handoff Protocol ───────────────────────────────────────────────────────

    def handoff_prepare(self, to_script: str, output: dict, pending: List[str] = None) -> dict:
        """
        Prepare handoff document for downstream script.
        All cross-script calls MUST use handoff_prepare().
        """
        ...

    def handoff_receive(self, script_prefix: str = None) -> List[dict]:
        """Receive handoffs from other scripts."""
        ...

    # ── Data Source Interface ───────────────────────────────────────────────────

    def get_data(self, preferred_source: str = "api", **kwargs) -> Dict:
        """
        Three-tier data source:
            1. "api"    — Real API calls
            2. "local"  — Local DB / files
            3. "mock"   — Mock data (⚠️ MOCK_MARKER attached)

        Usage:
            data = self.get_data("api",
                endpoint="/api/v1/stock/quote",
                fallback_local="data/quotes.json",
                mock_return={"price": 0})
        """
        source_priority = ["api", "local", "mock"] if preferred_source == "api" else [preferred_source]
        errors = []

        for source in source_priority:
            if source == "api":
                result = self._fetch_api(**kwargs)
                if result is not None:
                    result["_data_source"] = "api"
                    return result
                errors.append(f"API failed: {kwargs.get('endpoint', 'unknown')}")

            elif source == "local":
                result = self._read_local(**kwargs)
                if result is not None:
                    result["_data_source"] = "local"
                    return result
                errors.append(f"Local read failed: {kwargs.get('local_path', 'unknown')}")

            elif source == "mock":
                result = self._mock_data(**kwargs)
                result["_data_source"] = "mock"
                result["_warning"] = "⚠️ MOCK_DATA — replace with real API"
                return result

        return {"_data_source": "none", "_errors": errors, "_warning": "⚠️ ALL DATA SOURCES FAILED"}

    def _fetch_api(self, **kwargs) -> Optional[Dict]:
        """Override in subclass: real API call."""
        return None

    def _read_local(self, **kwargs) -> Optional[Dict]:
        """Override in subclass: local file / DB read."""
        return None

    def _mock_data(self, **kwargs) -> Dict:
        """Override in subclass: mock data for testing."""
        return kwargs.get("mock_return", {"mock": True})

    # ── Standard Entry Point ────────────────────────────────────────────────────

    def run(self, params: dict) -> dict:
        """
        Main execution method. MUST be implemented by subclass.
        All L3 scripts implement run(params) -> dict.
        """
        raise NotImplementedError(f"{self.SCRIPT_NAME} must implement run(params)")


# ── Module Entry Point ─────────────────────────────────────────────────────────────────

def analyze(task: str, script_class, required_fields: List[str] = None) -> dict:
    """
    Standard module entry point for all L3 scripts.

    Usage:
        from l3__base import L3Base, l3_analyze

        def analyze(task: str) -> dict:
            return l3_analyze(task, MyScriptClass, required_fields=["result", "data"])

    This is the contract that the L2 orchestrator discovery mechanism
    uses to find and execute L3 modules.
    """
    try:
        params = json.loads(task) if task.strip().startswith("{") else {"_raw_task": task}
    except Exception:
        params = {"_raw_task": task}

    script = script_class()

    # Execute
    result = script.run(params)

    # Verify required fields
    if required_fields:
        v = script.verify_output(result, required_fields)
        result["_verified"] = v["pass"]
        result["_verification_issues"] = v["issues"]

    # Finalize
    final = script.finalize(result)
    return final
