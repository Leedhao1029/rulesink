"""
Company Capability Development Standard Protocol (CCDSP)

Seven-chapter governance framework establishing:
  1. 总则 — Purpose, scope, five core principles
  2. 自主进化权 — Each L2 owns its self-evolution module
  3. 贡献规范 — 5-step contribution workflow + quality standards
  4. 共享归属 — Shared capabilities belong to company, not one domain
  5. 跨部门协作 — Primary + supporting domain coordination rules
  6. 技术中台 — IT as platform: builds tools, doesn't build-for-others
  7. 附则 — Enforcement, amendment process

Core Principles:
  1. 自主进化权 — 每个L2部门拥有自己的自进化模块
  2. 贡献有价值 — 所有能力贡献必须经过质量门槛
  3. 共享归属公司 — 跨部门复用的能力属于公司，不属于原部门
  4. 透明追溯 — 所有决策和贡献有完整的审计日志
  5. 五步闭环 — Build → Self-test → Propose → Approve → Register → Archive

Five-Step Contribution Workflow:
  Step 1 BUILD    — Domain builds new capability using own self-evolution module
  Step 2 SELF-TEST — Passes through domain check mode
  Step 3 PROPOSE  — Generates contribution proposal (impact analysis)
  Step 4 APPROVE  — Tiered approval (domain-L2 / cross-L2+L1 / all-L2+L1)
  Step 5 REGISTER — Add to L3 script library + skill catalog
  Step 6 ARCHIVE  — Record in autobiography for traceability

Approval Tiers:
  TIER_1 (domain-L2)     — Skill update within same domain
  TIER_2 (cross-L2+L1)  — New skill or cross-domain capability
  TIER_3 (all-L2+L1)   — New L2 domain or fundamental protocol change

Quality Standards (NEW SKILL):
  • name, description, trigger_on keywords in frontmatter
  • Steps / Pitfalls / Examples / Verification chapters
  • Body length ≥ 500 words (no thin skills)
  • Trigger coverage ≥ 3 real operational scenarios

Quality Standards (NEW L3 SCRIPT):
  • Inherits L3Base (standardized: run() / analyze() / finalize())
  • SKILL_NAME unique identifier matching skill catalog
  • Quality Status in every output: PASS | NEEDS_WORK
  • try/except on all external I/O
  • Handoff protocol declared (ready_for / needs_from / constraints)
"""

CCDSP = {
    "name": "Company Capability Development Standard Protocol",
    "abbreviation": "CCDSP",
    "version": "1.0",
    "chapters": 7,
    "workflow_steps": 6,
    "approval_tiers": 3,
    "core_principles": 5,
    "quality_gates": ["L3Base", "SKILL_NAME", "Quality_Status", "Handoff_Protocol"],
}
