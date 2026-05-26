#!/usr/bin/env python3
"""
Enterprise Advisory Council — Example Usage
advisory_council_example.py

Demonstrates how to convene the advisory council for a complex CEO decision.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from council.advisory_council import AdvisoryCouncil, ADVISOR_NAMES


def main():
    # Initialize the council
    council = AdvisoryCouncil()

    # Example question from CEO
    question = (
        "Should we adopt a microservices architecture for our e-commerce platform, "
        "or continue with our current monolithic architecture?"
    )

    context = {
        "company_stage": "growth",
        "team_size": 50,
        "annual_revenue": "50M RMB",
        "current_architecture": "monolithic Django",
        "decision_timeline": "Q3 2026",
        "budget_constraint": "2M RMB",
        "asking_department": "IT",
    }

    print(f"Question: {question}")
    print(f"Context: {json.dumps(context, indent=2, ensure_ascii=False)}")
    print("\nConvening advisory council...")
    print("(Running 4 advisors in parallel: strategic, technical, risk, evolution)\n")

    result = council.convene(question, context)

    # Print synthesis
    print("=" * 60)
    print("ADVISORY COUNCIL RESULT")
    print("=" * 60)
    print(f"Convened at: {result['convened_at']}")
    print(f"Decision ID: {result['convene_id']}")
    print(f"\nHandoff status: {result['handoff_status']}")
    print(f"IT Audit passed: {result['audit']['passed']}")

    if result['audit']['flags']:
        print(f"IT Audit flags: {result['audit']['flags']}")

    print(f"\nSynthesis confidence: {result['synthesis']['confidence']}")
    print(f"\nKey insights:")
    for insight in result['synthesis']['key_insights']:
        print(f"  • {insight}")

    print(f"\nRecommendations:")
    for rec in result['synthesis']['recommendations']:
        print(f"  → {rec}")

    if result['synthesis']['dissent_noted']:
        print(f"\nDissent noted:")
        for dissent in result['synthesis']['dissent_noted']:
            print(f"  ⚠ {dissent}")

    # Print advisor verdicts
    print("\n" + "=" * 60)
    print("ADVISOR VERDICTS")
    print("=" * 60)
    for advisor_type, response in result['advisor_responses'].items():
        print(f"\n[{ADVISOR_NAMES[advisor_type]}]")
        print(f"  Verdict: {response['verdict']}")
        print(f"  Confidence: {response['confidence']}")
        print(f"  Key points:")
        for point in response['key_points']:
            print(f"    • {point}")

    # Print extracted patterns
    if result['patterns']:
        print("\n" + "=" * 60)
        print(f"EXTRACTED PATTERNS ({len(result['patterns'])})")
        print("=" * 60)
        for pattern in result['patterns']:
            print(f"\n[{pattern['pattern_type']}] {pattern['description'][:80]}")
            print(f"  Quality: {pattern['quality_score']} | Status: {pattern['approval_status']}")

    print("\n" + "=" * 60)
    print("⚠️  ADVISORY ONLY — L2 retains full decision authority")
    print("⚠️  All outputs audited by IT Department before delivery")
    print("=" * 60)


if __name__ == "__main__":
    main()
