# 矩墨RulesInk

[中文版 / Chinese Version](README.zh.md)

> A self-governing AI organization with L1–L2–L3 hierarchy, self-evolution loops, and constitutional constraint layer.
> MIT Licensed.

[![Documentation](https://img.shields.io/badge/docs-ARCHITECTURE-blue)](docs/ARCHITECTURE.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What Is This?

矩墨RulesInk (HNO) is an open-source reference implementation of a self-governing AI agent architecture. It demonstrates:

- **L1–L2–L3 governance hierarchy** — CEO → Domain General Manager → Executive Assistant
- **Per-domain self-evolution loops** — Each domain automatically detects and fixes its own capability gaps
- **SOUL.md constraint layer** — Constitutional-level constraints to prevent authority overreach
- **dispatch_guard plugin** — pre_tool_call gate enforcement for Hermes Agent (CLI + Agent dual-layer)
- **Gate Proposal Mechanism** — L1 must propose to user before executing terminal/execute_code
- **Enterprise Advisory Council** — Multi-perspective concurrent expert analysis (advisory only, no decision power)
- **Company Capability Development Protocol** — Standardized capability contribution workflow

## 版本更迭 / Version History

> 矩墨RulesInk follows a "Governance First, Features Later" evolution strategy. Each major version marks a milestone in the maturity of the constitutional constraint layer.

| Version | Date | Milestone | Repository |
|---------|------|-----------|------------|
| v1.0 | 2026-05-11 | Initial release: L1–L2–L3 hierarchy + SOUL.md spec-interface + 6-domain self-evolution | [hermes-native-organization-legacy](https://github.com/Leedhao1029/hermes-native-organization-legacy) |
| v3.5.0 | 2026-05-26 | Gate system fully landed: dispatch_guard plugin + Gate Proposal Mechanism + Soul Arbiter constitutional arbiter (9 integration points) + coordination_protocol v2.2 | [rulesink](https://github.com/Leedhao1029/rulesink) |

**Evolution logic:**
- v1.0 → v3.5 is not "feature addition" but "governance maturation"
- The constraint layer (SOUL.md) evolved from an interface spec to a production-grade arbiter
- The gate enforcement system (dispatch_guard) was built to close the architectural gap where L1 could bypass L2→L3 orchestration
- All previous commits are preserved in the legacy repository as historical evidence

## 项目哲学 / Project Philosophy

> 我们坚信，AI 组织的治理不应建立在"自觉"之上，而应建立在硬性的、代码级的宪法约束之上。因此，我们的首要任务是将 SOUL.md 宪法和其 SOUL Arbiter（审计与执法引擎）打磨到生产级，而不是急于开源一个功能繁多但治理薄弱的原型。
>
> 本项目采用"先治理，后扩展"的架构演进策略。我们选择一条更困难但更负责任的道路——先确保核心治理层（L1-L3架构、SOUL Arbiter、自进化引擎、长链路任务管理）的可靠与可审计，再逐步扩展对外的功能模块。

---

>We believe that the governance of AI organizations should not be built on 'compliance promises' but on hard-coded, constitutional-level constraints. Therefore, our immediate priority is to refine the SOUL.md constitution and its SOUL Arbiter (audit & enforcement engine) to production-grade, rather than rushing to open-source a feature-rich but weakly-governed prototype.
>
>This project follows a 'Governance First, Features Later' architectural evolution strategy. We are taking a harder but more responsible path — ensuring the core governance layer (L1-L3 hierarchy, SOUL Arbiter, self-evolution engine, long-task context manager) is reliable and auditable before progressively expanding the functional modules.

## Architecture Overview

```
L1 CEO
  ├── Gate Enforcement System (dispatch_guard plugin + Soul Arbiter)
  └── L2 Domain Orchestrators (IT / Ecommerce / Construction / Investment / Life / Multimodal)
        └── L3 Skill Agents (180+ scripts per domain)
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture documentation.

## Quick Start

```bash
pip install -e .
python3 -c "from hermes_native_organization import dispatch; print(dispatch('帮我分析一下电商转化率'))"
```

## What's Open Source vs. Proprietary?

We open-source the **architecture, interfaces, and workflows**.
We keep proprietary the **specific threshold values, pattern databases, and learning algorithms**.

### Open Source (MIT)

| Component | What You Get |
|-----------|-------------|
| `dispatcher.py` | L1 intent routing interface — full 7-domain keyword system removed |
| `it_orchestrator.py` | IT L2 orchestration loop — thresholds and routing tables removed |
| `advisory_council.py` | 4-advisor panel — analysis logic proprietary |
| `l3_base.py` | L3 base class — full implementation (350 lines) |
| `soul_arbiter.py` | SOUL constraint interface — pattern engine removed |
| Self-evolution modules | 5-stage loop architecture — trigger thresholds proprietary |
| CCDSP protocol | 7-chapter governance framework — full implementation |

### Proprietary (NOT in this repo)

- Exact keyword→domain scoring weights
- Circuit breaker turn limits and budget caps
- Autobiography learning algorithm
- SOUL pattern matchers and threshold values
- Advisor analysis prompt templates
- Forge queue trigger thresholds

## Enterprise Advisory Council

A new module in this version. The council is a **temporary, advisory-only expert panel**:

```
Question ──▶ [STRATEGIC] ──┐
           ──▶ [TECHNICAL] ──┼──▶ Synthesis ──▶ CEO
           ──▶ [RISK]      ──┤
           ──▶ [EVOLUTION] ──┘
```

**Governance rules:**
- Advisory only — does NOT replace L2 decision authority
- IT Department owns and audits all outputs
- Does NOT execute L3 scripts directly
- Patterns extracted from approved decisions → auto-registered as skills

```python
from council.advisory_council import AdvisoryCouncil

council = AdvisoryCouncil()
result = council.convene(
    "Should we adopt microservices?",
    context={"team_size": 50, "budget": "2M RMB"}
)
# result["synthesis"]["recommendations"] → CEO decision support
```

See `examples/advisory_council_example.py` for full usage.

## Governance Evidence

> SOUL Arbiter is the actual enforcer of the constitutional constraint layer, passively triggered and writing audit logs on every routing decision. The following is production environment measured data.

### Core Evidence: Production Event Audit Log

```
Session: construction_task_session
Timestamp (UTC)      Category              Action                  Domain         Result  Trigger
────────────────────────────────────────────────────────────────────────────────────────────────────
2026-05-11T08:06:34  Intent Audit          intent_routed           construction  PASS   User input triggered domain identification, matched construction (confidence 0.79)
2026-05-11T08:06:34  Cross-Domain Audit    cross_domain_resolved  construction  PASS   Cross-domain coordination
2026-05-11T08:06:34  Authorization Check   authorize              construction  PASS   Domain 'construction' authorized to execute orchestrator
2026-05-11T08:06:50  Intent Audit          orchestrator_executed  construction  PASS   Orchestrator execution completed, return code 0
2026-05-11T08:06:50  Intent Audit          orchestrator_executed  construction  FAIL   Orchestrator execution completed, return code 1
2026-05-11T08:06:50  L3 Mismatch Check      l3_mismatch_check      construction  PASS   L3 capability verified, no rebuild triggered
2026-05-11T08:06:50  Authorization Check   authorize              it            PASS   Domain 'it' authorized to execute orchestrator
```

**Total: 7 soul_arbiter events, written to events.jsonl (4,230 total production events)**

### SOUL Arbiter Integration Points

| Integration Point | Location | Trigger | Event Type |
|-------------------|----------|---------|------------|
| Intent Audit | After `classify_intent()` | Every task entry | `intent_routed` |
| Cross-Domain Audit | After `coordinate()` | Cross-domain tasks | `cross_domain_resolved` / `BLOCK` |
| Orchestrator Authorization | At `run_orchestrator()` entry | Every orchestrator call | `authorize` / `BLOCK` |
| L3 Mismatch Detection | After `_auto_trigger_it()` returns | Rebuild trigger decision | `l3_mismatch_check` / `FLAG` |
| Circuit Breaker Audit | When `retry_depth >= 3` | Retry limit exceeded | `circuit_open` → `CIRCUIT_OPEN` |
| Orchestrator Result Audit | At `run_orchestrator()` return | Success/failure | `orchestrator_executed` |

### Query Commands

```bash
hermes --soul-stats           # SOUL Arbiter stats — last 24 hours
hermes --soul-stats 168       # Stats for last 7 days
hermes --events               # View all event logs (includes soul_arbiter events)
```

### Real Case: Execution Layer Audit Blind Spot Discovery & Fix (2026-05-11)

> This is a production-data-driven precision fix, serving as direct evidence of the system's "self-audit capability".

**Problem discovered**: `life-health` had 146 direct invocations, 0 through any quality gate. IT domain had 1,472 skill invocations, with only 1 soul_arbiter record (blind spot rate: 99.93%).

**Root cause**: SOUL Arbiter only covered the "orchestration layer" (6 integration points), not the "execution layer" (`skill_invoke` chain).

**Fixes applied**:
- Integration Point 7: `audit_skill_invoke()` — added health skill recognition
- Integration Point 8: `audit_health_skill_content()` — health skill content audit (94 medical overreach keywords)
- Integration Point 9: secondary review of life domain before orchestrator returns
- L2 label unification: all audit log domain fields standardized to Chinese names

**Verification**: `audit_health_skill_content()` actual output:
```
result=BLOCK, action=medical_overreach_direct
  skill=life-health
  medical_overreach_keywords: ['CA125', '卵巢癌']
  via_orchestrator: False
```

**Full case report**: [`docs/DIAGNOSIS.md`](docs/DIAGNOSIS.md)

### Transparent & Auditable Principles

Every SOUL Arbiter event includes:
- **Trigger reason** (`trigger_reason`): why it fired
- **Involved layers** (`involved_l1_parts`): which L1 components participated in the decision
- **Interception result** (`result`): `PASS` = normal pass / `FLAG` = capability gap / `BLOCK` = authority overreach / `CIRCUIT_OPEN` = circuit breaker
- **Full context** (`extra`): original task, return code, error message

## Project Structure

```
ju-mo-rulesink/
├── hermes/                          # Core framework
│   ├── __init__.py
│   ├── dispatcher.py                 # L1 intent routing (1735 lines → public interface)
│   ├── l3_base.py                   # L3 base class (350 lines — full)
│   └── soul_arbiter.py              # SOUL constraint interface
├── domains/                         # Domain self-evolution loops
│   ├── it/
│   │   ├── orchestrator.py           # 4094 lines → public architecture
│   │   └── self_evolution.py         # 802 lines → public interface
│   ├── ecommerce/self_evolution.py   # 730 lines → public interface
│   ├── construction/self_evolution.py
│   ├── investment/self_evolution.py  # 841 lines → public interface
│   ├── life/self_evolution.py
│   └── multimodal/self_evolution.py
├── council/
│   └── advisory_council.py           # 1033 lines → public architecture
├── dispatch_guard/                    # Gate enforcement plugin (CLI + Agent dual-layer)
├── skills/
│   ├── enterprise-advisory-council/SKILL.md
│   └── company-capability-development-protocol/SKILL.md
├── protocol/
│   └── company_capability_development_protocol.py
└── examples/
    ├── minimal_demo.py
    └── advisory_council_example.py
```

## Self-Evolution Loop

Each domain implements a 5-stage closed loop:

```
ANALYZE → DIAGNOSE → PLAN → EXECUTE → LEARN
   ↑                                     │
   └─────────────────────────────────────┘
```

| Stage | What Happens |
|-------|-------------|
| ANALYZE | Scan L3 scripts, skills, archives |
| DIAGNOSE | Classify issues: MISSING_SKILL / WEAK_SKILL / BROKEN_SCRIPT |
| PLAN | Generate build proposals |
| EXECUTE | User-confirmed changes only |
| LEARN | Record to autobiography for routing improvement |

## CCDSP — Company Capability Development Protocol

7-chapter governance framework (fully documented in `protocol/`):

```
Chapter 1: General Provisions         — Five core principles
Chapter 2: Autonomous Evolution Rights — Each L2 owns its evolution module
Chapter 3: Contribution Standards   — 6-step contribution workflow
Chapter 4: Shared Attribution       — Shared capabilities belong to company
Chapter 5: Cross-Domain Collaboration — Primary + supporting domain rules
Chapter 6: Technical Platform       — IT as platform, not service provider
Chapter 7: Supplementary Provisions — Enforcement and amendment
```

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Full architecture reference
- [GETTING_STARTED.md](docs/GETTING_STARTED.md) — Installation and first use
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) — How to contribute

## License

MIT — see [LICENSE](LICENSE).

## Contact

| Channel | Handle |
|---------|--------|
| Email | lidonghao1029@me.com |
| Phone | +86 15361474556 |
| WeChat | LeedHao |

## GitHub Pages

Documentation site: https://leedhao1029.github.io/ju-mo-rulesink/
