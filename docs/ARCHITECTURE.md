# 矩墨RulesInk Architecture

## L1–L2–L3 Full Governance Hierarchy

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          L1: BOARD / COMMANDER                               │
│                                                                              │
│   Intent Detection → Domain Routing → Cross-Domain Coordination              │
│   Final Report Aggregation → CEO Decision Support                            │
│                                                                              │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│   L2: ECOMMERCE  │ │  L2: CONSTRUCTION │  L2: INVESTMENT          │
│  it_orchestrator │ │  construction_orch │  investment_orch          │
│  4094 lines      │ │                    │  841 lines               │
│  ─ Shop运营      │ │  ─ BIM/CAD         │  ─ A股/港股分析          │
│  ─ 供应链        │ │  ─ 造价清单         │  ─ 量化策略              │
│  ─ 营销转化      │ │  ─ 施工进度         │  ─ 资金流追踪           │
└──────────────────┘ └──────────────────┘ └──────────────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│   L2: IT         │ │  L2: LIFE        │  L2: MULTIMODAL           │
│  it_orchestrator │ │  life_orchestrator│  multimodal_orch         │
│  4094 lines      │ │                    │                          │
│  ─ 开发/运维     │ │  ─ 旅游规划        │  ─ 文档处理               │
│  ─ 安全审计      │ │  ─ 美食酒店        │  ─ 图像/音频              │
│  ─ 自进化引擎    │ │  ─ 健身健康        │  ─ PPT/报告生成          │
└──────────────────┘ └──────────────────┘ └──────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     L3: SKILL AGENTS                                         │
│                                                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │  Code  │ │Research│ │Analyze │ │  Write │ │  Test  │ │Deploy  │  ...     │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘          │
│                                                                              │
│  L3 Scripts: l3_<domain>_<name>.py  (180+ scripts)                         │
│  Base Class: L3Base (standardized: run() / analyze() / finalize())          │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Self-Evolution Closed Loop (Per Domain)

Every domain implements a 5-stage self-evolution loop:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SELF-EVOLUTION LOOP                            │
│                                                                 │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    │
│    │ ANALYZE │───▶│ DIAGNOSE │───▶│  PLAN   │───▶│ EXECUTE │    │
│    └─────────┘    └─────────┘    └─────────┘    └─────────┘    │
│                                                     │           │
│                              ◀──────────────────────┘           │
│                                      │                            │
│                              ┌───────┴───────┐                   │
│                              │     LEARN     │                   │
│                              │  (autobiography)│                 │
│                              └───────────────┘                   │
└─────────────────────────────────────────────────────────────────┘

Stage 1: ANALYZE     → Scan L3 scripts, skills, archives
Stage 2: DIAGNOSE    → Identify gaps, classify severity
Stage 3: PLAN        → Generate build proposals
Stage 4: EXECUTE     → User-confirmed changes
Stage 5: LEARN       → Record to autobiography, update weights
```

### Six Self-Evolution Modules

| Domain | Module | Lines | Key Capabilities |
|--------|--------|-------|------------------|
| IT | `it_self_evolution.py` | 802 | Detects skill gaps, triggers L3 construction |
| Ecommerce | `ecommerce_self_evolution.py` | 730 | Monitors DSR, SKU performance, conversion |
| Construction | `construction_self_evolution.py` | 781 | BIM quality, cost variance, safety compliance |
| Investment | `investment_self_evolution.py` | 841 | Rule verification, portfolio rebalancing signals |
| Life | `life_self_evolution.py` | 725 | Preference learning, schedule optimization |
| Multimodal | `multimodal_self_evolution.py` | 727 | Format drift detection, skill bloat |

## SOUL.md Arbitration Layer

Every L3 output passes through a constitutional constraint layer before delivery:

```
┌──────────────────────────────────────────────────────────────┐
│                    SOUL.md ARBITER                           │
│                                                              │
│   L3 Output ──▶ Pattern Matcher ──▶ Verdict                  │
│                                   ├── PASS   (clear)         │
│                                   ├── FLAG    (caution)      │
│                                   └── BLOCK  (violation)     │
│                                                              │
│   BLOCK → content filtered, event logged, user notified       │
│   FLAG  → content annotated, advisory note attached          │
└──────────────────────────────────────────────────────────────┘
```

### Arbitration Interface (Public)

```python
class SOUL_ARBITER:
    def audit(self, output: str, context: dict) -> AuditResult:
        """
        AuditResult:
            verdict: PASS | FLAG | BLOCK
            flags: List[str]          # annotations
            redacted_content: str     # filtered version if blocked
            event_log: dict          # for compliance trail
        """
        ...

    def check_authorization(self, action: str, actor: str) -> bool:
        """Boundary enforcement — who can do what."""
        ...

    def escalate(self, conflict: dict) -> dict:
        """Unresolvable conflicts → L1 CEO arbitration."""
        ...
```

**What we expose**: The interface contract and behavior, not the pattern database.

**What we keep private**: The actual regex expressions and threshold values.

### SOUL Arbiter Integration Points (Production)

The `_soul_arbiter.py` module is integrated into the L1 dispatcher at **nine checkpoint functions** (updated 2026-05-11, previously documented as 6). Each checkpoint is a passive observer — it does not block the pipeline, only records audit events to `events.jsonl`:

```
hermes_dispatcher.py (_main_inner)
│
├── checkpoint 1: classify_intent() ──────────▶ audit_intent()
│   Records: domain, confidence, all keyword scores
│
├── checkpoint 2: coordinate() ───────────────▶ audit_coordinate()
│   Records: cross_domain flag, primary/support domains, conflict status
│
├── checkpoint 3: run_orchestrator() entry ──▶ authorize_orchestrator()
│   Records: authorized domain, orch_path, task preview
│   BLOCK if domain not in allowed matrix
│
├── checkpoint 4: _auto_trigger_it() return ──▶ audit_l3_mismatch()
│   Records: mismatch detected (→ FLAG), or clean (→ PASS)
│
├── checkpoint 5: retry_depth >= 3 ──────────▶ audit_circuit_breaker()
│   Records: domain, retry count, primary/support role
│   Result: CIRCUIT_OPEN
│
├── checkpoint 6: run_orchestrator() exit ──▶ audit_orchestrator_result()
│   Records: returncode (0=PASS, 1=FAIL), execution time
│
├── checkpoint 7: skill_invoke() / skill_load() ──▶ audit_skill_invoke()
│   Records: skill name, invocation path, health-skill detection
│   Detects: life-health / life-nutrition / life-exercise / life-sleep / life-mental / life-habit-tracker
│
├── checkpoint 8: L3 skill result return ──▶ audit_health_skill_content()
│   Records: health content audit with 94 bilingual medical keywords + 25 "see doctor" phrases
│   Verdict: PASS / ADVISORY / FLAG / BLOCK
│
└── checkpoint 9: before orchestrator return ──▶ _audit_life_health_content()
    Secondary review for life domain health skills
    4-tier judgment: PASS / ADVISORY / FLAG / BLOCK
```

**Health Skill Audit System (Checkpoints 7/8/9):**

Six core health skills monitored:
- `life-health` / `life-nutrition` / `life-exercise` / `life-sleep` / `life-mental` / `life-habit-tracker`

Four-tier verdict system:
| Verdict | Trigger Condition |
|---------|-----------------|
| PASS | No risk detected |
| ADVISORY | Contains "see doctor" suggestion phrases |
| FLAG | Through orchestrator + contains medical overreach content |
| BLOCK | Direct invocation + contains medical overreach content |

**Verified output** (2026-05-11):
```
result=BLOCK, action=medical_overreach_direct
  skill=life-health
  medical_overreach_keywords: ['CA125', '卵巢癌']
  via_orchestrator: False
```

**Event schema** (written to `~/.hermes/events/events.jsonl`):

```json
{
  "event": "soul_arbiter",
  "arbiter": {
    "category": "意图识别审计 | 调度越权拦截 | 授权矩阵判断 | 异常熔断触发 | 执行层审计 | 健康内容审计 | 二次复核",
    "action": "intent_routed | cross_domain_resolved | authorize | l3_mismatch_check | circuit_open | orchestrator_executed | skill_invoked | health_content_audit | life_health_secondary_review",
    "domain": "投资总经理 | 建筑工程总经理 | IT技术总经理 | 电子商务总经理 | 生活事务总经理 | 多模态总经理 | 自我进化总经理",
    "trigger_reason": "human-readable description",
    "involved_l1_parts": ["function_name", ...],
    "result": "PASS | FLAG | BLOCK | ADVISORY | CIRCUIT_OPEN"
  },
  "extra": {
    "confidence": 0.79,
    "returncode": 0,
    "task_preview": "...",
    "execution_time_s": 16.3,
    "via_orchestrator": true,
    "medical_overreach_keywords": [],
    "skill": "skill-name"
  }
}
```

> **Note on event category labels**: The `category` field uses Chinese names (e.g., "投资总经理") to ensure consistency across all audit records. The `domain` field in L2 dispatch events was unified to Chinese names on 2026-05-11 (previously mixed English keys like "investment" and Chinese names).

**Query commands**:

```bash
hermes --soul-stats           # 24-hour audit summary
hermes --soul-stats 168       # 7-day audit summary
hermes --events               # raw event log
```

## Company Capability Development Standard Protocol (CCDSP)

Seven-chapter governance framework governing all organizational capability development.

```
Chapter 1:  总则        — Purpose, scope, five core principles
Chapter 2:  自主进化权   — Each L2 owns its self-evolution module
Chapter 3:  贡献规范    — 5-step contribution workflow + quality standards
Chapter 4:  共享归属    — Shared capabilities belong to company, not one domain
Chapter 5:  跨部门协作  — Primary + supporting domain coordination rules
Chapter 6:  技术中台    — IT as platform: builds tools, doesn't build-for-others
Chapter 7:  附则        — Enforcement, amendment process
```

### Five-Step Contribution Workflow

```
Step 1  BUILD    → Domain builds new capability using own self-evolution module
Step 2  SELF-TEST → Passes through domain check mode
Step 3  PROPOSE  → Generates contribution proposal (impact analysis)
Step 4  APPROVE  → Tiered: domain-L2 / cross-L2+L1 / all-L2+L1
Step 5  REGISTER  → Add to L3 script library + skill catalog
Step 6  ARCHIVE  → Record in autobiography for traceability
```

### Capability Quality Standards

New L3 scripts must satisfy:

| Requirement | Description |
|-------------|-------------|
| Inherit L3Base | Standard base class with run()/analyze() interface |
| SKILL_NAME | Unique identifier matching skill catalog |
| Quality Status | Every output includes PASS / NEEDS_WORK |
| Exception Handling | try/except on all external I/O |
| Handoff Protocol | Outputs declare ready_for / needs_from / constraints |

New Skills must satisfy:

| Requirement | Description |
|-------------|-------------|
| Frontmatter | name, description, trigger_on keywords |
| Chapters | Steps / Pitfalls / Examples / Verification |
| Body Length | ≥ 500 words (no "thin skills") |
| Trigger Coverage | Keywords cover target operational scenarios |

## Cross-Domain Delegation Protocol

When a task spans multiple domains:

```
User Request
     │
     ▼
L1 Intent Router ───────────────────────────────────────┐
     │                                                    │
     │  Domain A  ──▶ Primary (owns final output)         │
     │  Domain B  ──▶ Supporting (provides inputs)        │
     │  Domain C  ──▶ Supporting (provides inputs)        │
     │                                                    │
     ▼                                                    │
Data Flow:  [B → A] + [C → A] ──▶ A aggregates ──▶ L1 ──▶ User
                         │
                         ▼
              L2 Decision (A's domain L2)
```

Rules:
- Primary domain L2 makes final decision
- Supporting domains don't report directly to L1
- Data contracts between domains must be declared upfront
- Conflicts escalate to L1 arbitration

## L2 Orchestrator Interface (Public)

Every L2 orchestrator implements a standard dispatch interface:

```python
class L2Orchestrator(ABC):
    """Base interface for all domain orchestrators."""

    def __init__(self):
        self.SCRIPT_DIR = Path.home() / ".hermes" / "scripts"
        self.SKILL_DIR = Path.home() / ".hermes" / "skills"
        self.domain: str = "base"

    def discover_l3_modules(self) -> List[L3Module]:
        """Auto-discover all L3 scripts for this domain."""
        ...

    def plan(self, task: str, context: dict) -> OrchestrationPlan:
        """Classify intent → select L3 skills → build execution DAG."""
        ...

    def execute(self, plan: OrchestrationPlan) -> ExecutionResult:
        """Run selected L3 modules, collect results, handle errors."""
        ...

    def report(self, result: ExecutionResult) -> str:
        """Synthesize L3 outputs into domain-specific report."""
        ...
```

## Enterprise Advisory Council

Four advisors deliberate on major decisions concurrently:

```
┌──────────────────────────────────────────────────────────────┐
│              ENTERPRISE ADVISORY COUNCIL                     │
│                                                              │
│   Question ──▶ [STRATEGIC] ──┐                              │
│              ──▶ [TECHNICAL] ──┼──▶ Synthesis ──▶ CEO       │
│              ──▶ [RISK]      ──┤                              │
│              ──▶ [EVOLUTION] ──┘                              │
│                                                              │
│   Output: Advisory report + security audit + pattern report │
│   ⚠️ Advisory only — does NOT replace L2 decision authority │
└──────────────────────────────────────────────────────────────┘
```

| Advisor | Questions It Answers |
|---------|---------------------|
| **Strategic** | Business value? Timing? Opportunity cost? |
| **Technical** | Feasibility? Complexity? Integration points? |
| **Risk** | Compliance exposure? Security surface? Tail risks? |
| **Evolution** | Reusable patterns? Skill gaps? Process improvements? |

> **Actual implementation status (updated 2026-05-11)**: The four-advisor panel (`l3_enterprise_advisory_council.py`) was initially implemented with hardcoded mock data (442 lines). On 2026-05-11, the mock data was removed and replaced with NotImplementedError stubs (now 512 lines). The advisory council logic is managed by the IT Department. Real invocation of the four advisors awaits production load accumulation.

## Investment Soul Framework Integration

> **Added 2026-05-11** — The investment domain uses the Soul Framework as its primary orchestrator via conditional routing.

**Routing logic** (`run_orchestrator()` in `hermes_dispatcher.py`):

```
domain == "investment"
  → _add_soul_skill_path()
  → SoulOrchestrator().run(task)
  → InvestmentL2Handler.plan()     # 195 lines — real production code
  → 3 sub-tasks (business-analysis, financial-detective, margin-safety)
  → InvestmentL2Handler.aggregate()
  → Signal generation
  ↓ (fallback if Soul fails)
original investment_orchestrator.py
```

**Test verification** (2026-05-11):
```
Input: "分析腾讯的财报和估值"
Status: success
Sub-tasks: 3 (business-analysis / financial-detective / margin-safety)
Confidence: 99
Signal: 数据不足
```

> **Note**: The investment domain was chosen as the first Soul Framework integration target because the `InvestmentL2Handler` is the only fully implemented L2 handler in the Soul Framework (`soul/l2/investment_l2.py`, 195 lines).

## Package Structure (Public Code)

```
ju-mo-rulesink/
├── hermes/                      # Core framework
│   ├── __init__.py
│   ├── dispatcher.py             # L1 intent routing
│   ├── base_orchestrator.py     # L2 orchestrator interface
│   ├── l3_base.py               # L3 script base class
│   └── soul_arbiter.py          # Constraint interface (pattern hidden)
│
├── domains/                      # Domain modules (public interfaces)
│   ├── ecommerce/
│   │   ├── orchestrator.py       # Ecommerce L2 (partial)
│   │   └── self_evolution.py     # 730 lines
│   ├── construction/
│   │   ├── orchestrator.py
│   │   └── self_evolution.py     # 781 lines
│   ├── investment/
│   │   ├── orchestrator.py
│   │   └── self_evolution.py     # 841 lines
│   ├── it/
│   │   ├── orchestrator.py       # IT L2 (4094 lines — partial)
│   │   └── self_evolution.py     # 802 lines
│   ├── life/
│   │   └── self_evolution.py     # 725 lines
│   └── multimodal/
│       └── self_evolution.py     # 727 lines
│
├── skills/                       # Standardized skill definitions
│   ├── company-capability-development-protocol/
│   ├── enterprise-advisory-council/
│   └── [domain]/[skill]/
│
├── council/                      # Enterprise advisory council
│   ├── advisory_council.py       # 512 lines (NotImplementedError stubs, updated 2026-05-11)
│   └── security_audit.py         # Audit interface (rules hidden)
│
├── protocol/
│   └── company_capability_development_protocol.py  # 429 lines
│
├── examples/
│   └── minimal_demo.py
│
└── docs/
    ├── GETTING_STARTED.md
    ├── ARCHITECTURE.md          # This file
    └── CONTRIBUTING.md
```

## Lines of Real Code

| Layer | Component | Lines |
|-------|-----------|-------|
| L1 | `hermes_dispatcher.py` | 1,735 |
| L2 | `it_orchestrator.py` (partial) | ~1,500 |
| L2 | Ecommerce / Construction / Investment orchestrators | ~800 each |
| L3 | `l3_base.py` | 350 |
| L3 | 180+ domain skill scripts | ~20,000 total |
| Self-Evolution | 6 domain modules | ~4,600 |
| Council | Advisory + audit | ~1,400 |
| Protocol | CCDSP | 429 |
| **Total public code** | | **~30,000 lines** |
