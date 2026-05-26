"""
Enterprise Advisory Council — Skill Definition

Trigger Keywords:
    专家顾问团、advisory council、顾问团、多角度分析、专家小组、临时召集

Trigger Conditions:
    • CEO或L2遇到棘手问题，需要多角度并发分析
    • 跨部门冲突需要无偏见的外部仲裁视角
    • 重大决策需要外部专家视角输入

Advisor Types:
    1. Strategic Advisor   — 商业价值、时机、战略对齐
    2. Technical Advisor   — 技术可行性、架构、集成风险
    3. Risk Advisor        — 合规、安全、尾风险
    4. Evolution Advisor    — 模式提炼、技能缺口、流程改进

Output Format:
    {
        convene_id: str,
        advisor_responses: {strategic, technical, risk, evolution},
        synthesis: {summary, key_insights, recommendations, dissent_noted},
        audit: {passed, flags, it_auditor},
        patterns: [extracted pattern objects],
        handoff_status: "ready_for_ceo" | "blocked_by_audit"
    }

Governance Rules:
    ✓ 顾问团只是顾问 — 不替代任何L2的决策权
    ✓ 不直接指挥任何L3助理执行任务
    ✓ 所有输出必须经过IT部门审计
    ✓ 顾问团归IT部门管辖（建造、维护、审计）
    ✓ 通过的决策定期提炼模式，自动注册为Skill或进化提案

Integration:
    from council.advisory_council import AdvisoryCouncil
    council = AdvisoryCouncil()
    result = council.convene("Should we adopt microservices?")
"""

ADVISORY_COUNCIL = {
    "name": "Enterprise Advisory Council",
    "domain": "governance",
    "trigger_keywords": ["专家顾问团", "advisory council", "多角度分析", "专家意见", "临时召集"],
    "advisor_count": 4,
    "advisor_types": ["strategic", "technical", "risk", "evolution"],
    "it_audit_required": True,
    "decision_authority": "NONE (advisory only)",
}
