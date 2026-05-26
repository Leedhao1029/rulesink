"""
矩墨RulesInk — Core Framework
MIT License

Public modules:
    dispatcher  — L1 intent routing and domain classification
    soul_arbiter — Constitutional constraint layer (interface only)
    l3_base     — L3 script base class and standard interfaces
    base_orchestrator — L2 orchestrator interface contract
"""

from .dispatcher import (
    detect_content_domain,
    classify_domain,
    dispatch,
    write_event,
    L2_NAMES,
)

from .l3_base import L3Base
from .soul_arbiter import SOULArbiter, Verdict, AuditResult

__version__ = "2.0"
__all__ = [
    "L3Base",
    "SOULArbiter",
    "Verdict",
    "AuditResult",
    "detect_content_domain",
    "classify_domain",
    "dispatch",
    "write_event",
    "L2_NAMES",
]
