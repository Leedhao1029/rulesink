#!/usr/bin/env python3
"""
Minimal Demo: Four-Advisor Concurrent Consultation
===================================================
This demo showcases 矩墨RulesInk's L1-L2-L3 governance
by running a concurrent consultation with four board-level advisors.

Run with: python3 examples/minimal_demo.py
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class Stance(Enum):
    SUPPORTIVE = "supportive"
    OPPOSED = "opposed"
    NEUTRAL = "neutral"
    ABSTAIN = "abstain"


@dataclass
class SkillResult:
    success: bool
    output: dict
    metrics: dict
    errors: List[str] = field(default_factory=list)


@dataclass
class Deliberation:
    advisor: str
    role: str
    domain: str
    stance: Stance
    reasoning: str
    confidence: float
    skills_used: List[str] = field(default_factory=list)


@dataclass
class DelegationResult:
    consensus: bool
    decision: str
    confidence: float
    deliberations: List[Deliberation]
    execution_time_ms: float


# =============================================================================
# L3: SKILL AGENTS
# =============================================================================

class Skill:
    """Base class for L3 Skill Agents"""
    name = "base_skill"
    version = "1.0.0"
    
    async def execute(self, context: dict) -> SkillResult:
        raise NotImplementedError
    
    def describe(self) -> str:
        return f"Skill: {self.name}"


class AnalyzeSkill(Skill):
    """L3 Skill: Analysis capability"""
    name = "analyze"
    
    async def execute(self, context: dict) -> SkillResult:
        task = context.get("task", "")
        start = time.time()
        
        # Simulate analysis work
        keywords = self._extract_keywords(task)
        analysis = {
            "keywords": keywords,
            "complexity": "medium" if len(task.split()) > 10 else "low",
            "sentiment": "positive" if any(w in task.lower() for w in ["good", "great", "benefit"]) else "neutral"
        }
        
        return SkillResult(
            success=True,
            output=analysis,
            metrics={"duration_ms": (time.time() - start) * 1000}
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        common = ["strategy", "technology", "finance", "market", "product", "growth", "risk", "cost"]
        return [w for w in common if w in text.lower()]


class ResearchSkill(Skill):
    """L3 Skill: Research capability"""
    name = "research"
    
    async def execute(self, context: dict) -> SkillResult:
        start = time.time()
        
        # Simulate research findings
        findings = {
            "data_points": 42,
            "sources": 5,
            "relevance_score": 0.87,
            "key_insights": [
                "Industry trend shows 15% growth",
                "Competitor analysis indicates opportunity",
                "Risk factors are manageable"
            ]
        }
        
        return SkillResult(
            success=True,
            output=findings,
            metrics={"duration_ms": (time.time() - start) * 1000}
        )


class WriteSkill(Skill):
    """L3 Skill: Writing capability"""
    name = "write"
    
    async def execute(self, context: dict) -> SkillResult:
        start = time.time()
        
        analysis = context.get("analysis", {})
        recommendation = context.get("recommendation", "proceed")
        
        report = f"""
EXECUTIVE BRIEF: {recommendation.upper()}
{'=' * 50}
Complexity: {analysis.get('complexity', 'unknown')}
Sentiment: {analysis.get('sentiment', 'neutral')}
Keywords: {', '.join(analysis.get('keywords', []))}

RECOMMENDATION: {recommendation}
"""
        
        return SkillResult(
            success=True,
            output={"report": report},
            metrics={"duration_ms": (time.time() - start) * 1000}
        )


class ExecuteSkill(Skill):
    """L3 Skill: Execution capability"""
    name = "execute"
    
    async def execute(self, context: dict) -> SkillResult:
        start = time.time()
        
        action = context.get("action", "noop")
        
        return SkillResult(
            success=True,
            output={
                "action_taken": action,
                "status": "completed",
                "next_steps": ["monitor", "evaluate", "iterate"]
            },
            metrics={"duration_ms": (time.time() - start) * 1000}
        )


# =============================================================================
# L2: DOMAIN ADVISORS
# =============================================================================

class DomainAdvisor:
    """L2 Domain Advisor with self-evolution capability"""
    
    def __init__(self, name: str, role: str, domain: str, skills: List[Skill]):
        self.name = name
        self.role = role
        self.domain = domain
        self.skills = {s.name: s for s in skills}
        self.feedback_history = []
    
    async def consult(self, situation: str) -> dict:
        """Consult the advisor on a situation"""
        # Invoke relevant skills
        analysis_skill = self.skills.get("analyze")
        research_skill = self.skills.get("research")
        
        analysis_result = await analysis_skill.execute({"task": situation})
        research_result = await research_skill.execute({"task": situation})
        
        # Generate domain-specific stance
        stance = self._determine_stance(situation, analysis_result.output)
        
        return {
            "advisor": self.name,
            "role": self.role,
            "domain": self.domain,
            "stance": stance,
            "reasoning": self._generate_reasoning(situation, analysis_result, research_result),
            "confidence": 0.85,
            "analysis": analysis_result.output,
            "research": research_result.output
        }
    
    def _determine_stance(self, situation: str, analysis: dict) -> Stance:
        positive_keywords = ["launch", "growth", "expand", "improve", "invest", "benefit"]
        negative_keywords = ["cut", "reduce", "risk", "danger", "avoid", "stop"]
        
        situation_lower = situation.lower()
        
        if any(k in situation_lower for k in positive_keywords):
            return Stance.SUPPORTIVE
        elif any(k in situation_lower for k in negative_keywords):
            return Stance.OPPOSED
        return Stance.NEUTRAL
    
    def _generate_reasoning(self, situation: str, analysis, research) -> str:
        keywords = analysis.output.get("keywords", [])
        insights = research.output.get("key_insights", [])
        
        reasoning = f"From {self.domain} perspective, analyzing keywords: {', '.join(keywords)}. "
        reasoning += f"Key insight: {insights[0] if insights else 'Standard analysis applied.'}"
        return reasoning
    
    async def evolve(self, feedback: dict) -> None:
        """Self-evolution: learn from feedback"""
        self.feedback_history.append(feedback)
        if len(self.feedback_history) >= 5:
            print(f"  [{self.name}] Self-evolution triggered: optimizing {self.domain} workflows")


# =============================================================================
# L1: ORGANIZATION (BOARD)
# =============================================================================

class Organization:
    """
    L1 Board-level Organization
    Coordinates L2 advisors and aggregates their deliberations
    """
    
    def __init__(self, name: str):
        self.name = name
        self.advisors: List[DomainAdvisor] = []
    
    def add_advisor(self, advisor: DomainAdvisor) -> None:
        """Add a board-level advisor (L2)"""
        self.advisors.append(advisor)
        print(f"  Board: Added {advisor.name} as {advisor.role} ({advisor.domain})")
    
    async def delegate(self, task: str) -> DelegationResult:
        """
        Delegate a task to the organization.
        This triggers L1→L2→L3 governance cascade.
        """
        start_time = time.time()
        print(f"\n{'=' * 60}")
        print(f"DELEGATION: {task}")
        print(f"{'=' * 60}")
        
        # Concurrent consultation with all advisors (L1→L2)
        consultations = [advisor.consult(task) for advisor in self.advisors]
        results = await asyncio.gather(*consultations)
        
        # Convert to Deliberation objects
        deliberations = [
            Deliberation(
                advisor=r["advisor"],
                role=r["role"],
                domain=r["domain"],
                stance=r["stance"],
                reasoning=r["reasoning"],
                confidence=r["confidence"]
            )
            for r in results
        ]
        
        # Aggregate decision (simple majority)
        supportive = sum(1 for d in deliberations if d.stance == Stance.SUPPORTIVE)
        opposed = sum(1 for d in deliberations if d.stance == Stance.OPPOSED)
        
        consensus = supportive > opposed
        decision = "APPROVE" if consensus else "REJECT" if opposed > supportive else "DEFER"
        confidence = sum(d.confidence for d in deliberations) / len(deliberations)
        
        # Trigger self-evolution for all advisors
        for advisor in self.advisors:
            await advisor.evolve({
                "task": task,
                "deliberation": [d for d in deliberations if d.advisor == advisor.name][0]
            })
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return DelegationResult(
            consensus=consensus,
            decision=decision,
            confidence=confidence,
            deliberations=deliberations,
            execution_time_ms=execution_time_ms
        )


# =============================================================================
# MAIN DEMO
# =============================================================================

async def main():
    """Run the minimal demo with four concurrent advisors"""
    
    print("\n" + "=" * 60)
    print("HERMES NATIVE ORGANIZATION - MINIMAL DEMO")
    print("Four-Advisor Concurrent Consultation")
    print("=" * 60)
    
    # Create L3 Skills
    skills_pool = [
        AnalyzeSkill(),
        ResearchSkill(),
        WriteSkill(),
        ExecuteSkill()
    ]
    
    # Create L1 Organization (Board)
    org = Organization(name="TechStartup AI")
    
    # Create L2 Domain Advisors and add to Board
    org.add_advisor(DomainAdvisor(
        name="Alice",
        role="CTO",
        domain="technology",
        skills=skills_pool
    ))
    
    org.add_advisor(DomainAdvisor(
        name="Bob",
        role="CFO",
        domain="finance",
        skills=skills_pool
    ))
    
    org.add_advisor(DomainAdvisor(
        name="Carol",
        role="COO",
        domain="operations",
        skills=skills_pool
    ))
    
    org.add_advisor(DomainAdvisor(
        name="Dave",
        role="CMO",
        domain="marketing",
        skills=skills_pool
    ))
    
    print(f"\nOrganization '{org.name}' initialized with {len(org.advisors)} advisors")
    
    # Delegate a task
    result = await org.delegate("Launch a new AI-powered product line in Q2")
    
    # Display results
    print(f"\n{'=' * 60}")
    print("DELIBERATION RESULTS")
    print(f"{'=' * 60}")
    
    for d in result.deliberations:
        print(f"\n  [{d.role}] {d.advisor} ({d.domain})")
        print(f"    Stance: {d.stance.value}")
        print(f"    Reasoning: {d.reasoning}")
        print(f"    Confidence: {d.confidence:.0%}")
    
    print(f"\n{'=' * 60}")
    print(f"FINAL DECISION: {result.decision}")
    print(f"Consensus: {result.consensus}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Execution Time: {result.execution_time_ms:.1f}ms")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
