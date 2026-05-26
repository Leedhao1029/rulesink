# Changelog

All notable changes to this project will be documented in this file.

## [v3.5.0] — 2026-05-26

### Gate Enforcement System (门禁系统完整落地)

- **dispatch_guard plugin** — Full pre_tool_call gate enforcement for Hermes Agent (CLI + Agent dual-layer routing)
  - Signature verification, hook registration, CLI freeze fix (P0.5)
  - Three-gate pipeline: L1→L2 / L2→L3 / L1 tool call
  - Soul Arbiter integration for BLOCK enforcement
  - Diagnostic bypass channel for read-only commands
  - Persona ACL (xiaoli role restriction)

- **Gate Proposal Mechanism** — L1 must propose to user before executing terminal/execute_code
  - Complexity-based timeouts: <3 → 10s / 3-6 → 30s / ≥7 → no timeout
  - Circuit breaker takes priority over proposal (fuse trip → no proposal output)
  - Timeout events recorded to events.jsonl

- **Soul Arbiter** — Upgraded from spec-interface NotImplementedError stubs to complete constitutional arbiter
  - 9 integration points (was 6 in v1.0)
  - Audit results: PASS / FLAG / BLOCK / ADVISORY
  - L3 script audit (py_audit) + SKILL.md P0 audit (skill_audit)
  - Health skill content scan (94 medical overreach keywords)
  - execution_layer blind spot eliminated

### L1 Override Prevention (L1越级防治)

- UI/HTML/CSS/JS changes must go through L2 orchestration pipeline
- L1 direct tool calls require four hard checks
- skill_view/execute_code/write_file/delegate_task in AUDITED_TOOLS

### Global Skill Routing (全域Skill路由)

- skill_routing_rules: 295 rules covering 11 L2 domains
- CLI layer and Agent layer routing separation (architecture gap identified in system diagnosis)

### Cross-Domain Coordination (跨域协调协议)

- Updated to v2.2
- L1 final arbitration authority (unconditional, no time limit)
- IT department repositioned as builder + auditor (not coordinator)
- P1-B domain onboarding mechanism (l2_domain_arbiter.py + applications/ persistence)

### Self-Evolution & Memorize (自进化与记忆)

- Memorize P1+P2+P3 fully implemented: three-state matrix / five-layer security / source_fact_id tracing
- Memorize three-phase reflection: micro / meso / macro layers
- Environment constraints knowledge base (environment_constraints.json)
- Portfolio cross-session recovery for long-chain tasks

### Documentation

- Gate Proposal Protocol: `docs/gate_proposal.md`
- Architecture: three-gate defense diagram added
- coordination_protocol.md → v2.2

---

## [v1.0] — 2026-05-11 (Initial Release)

- L1–L2–L3 governance hierarchy (CEO → Domain GM → Executive Assistant)
- Per-domain self-evolution loops (5-stage: ANALYZE → DIAGNOSE → PLAN → EXECUTE → LEARN)
- SOUL.md constitutional constraint layer (spec-interface)
- Enterprise Advisory Council (4-advisor panel, advisory only)
- Company Capability Development Protocol (CCDSP, 7 chapters)
- Layered open-source: architecture public, thresholds proprietary