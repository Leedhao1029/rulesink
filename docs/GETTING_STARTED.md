# Getting Started with 矩墨RulesInk

## 5-Minute Quick Start Guide

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Step 1: Install 矩墨RulesInk

```bash
pip install ju-mo-rulesink
```

Or install from source:

```bash
git clone https://github.com/Leedhao1029/rulesink.git
cd ju-mo-rulesink
pip install -e .
```

### Step 2: Verify Installation

```python
import hermes

print(f"Hermes version: {hermes.__version__}")
# Expected output: Hermes version: 1.0.0
```

### Step 3: Create Your First Organization

```python
from hermes import Organization, Agent

# Create an organization
org = Organization(name="MyStartup")

# Add your first advisor
cto = Agent(
    name="Alice",
    role="CTO",
    domain="technology",
    skills=["architecture", "coding", "devops"]
)

org.add_advisor(cto)

# List advisors
print(f"Organization: {org.name}")
print(f"Advisors: {[a.name for a in org.advisors]}")
```

### Step 4: Run Your First Delegation

```python
# Delegate a task to your organization
result = org.delegate("Evaluate microservices vs monolith architecture")

# Examine the result
print(f"Consensus: {result.consensus}")
print(f"Decision: {result.decision}")

# View deliberation trail
for d in result.deliberations:
    print(f"  {d.advisor} ({d.role}): {d.stance}")
```

### Step 5: First Run Verification

A successful run produces output like:

```
Organization: MyStartup
Advisors: ['Alice']
Consensus: True
Decision: microservices
  Alice (CTO): supportive → microservices offer better scalability
```

## First Project: Multi-Advisor Consultation

```python
from hermes import Organization, Agent

# Create organization with multiple advisors
org = Organization(name="TechCorp")

# Add diverse advisors
org.add_advisor(Agent(name="CTO_Alice", role="CTO", domain="technology", 
                       skills=["architecture", "coding"]))
org.add_advisor(Agent(name="CFO_Bob", role="CFO", domain="finance",
                       skills=["budgeting", "cost_analysis"]))
org.add_advisor(Agent(name="COO_Carol", role="COO", domain="operations",
                       skills=["process_optimization", "logistics"]))
org.add_advisor(Agent(name="CMO_Dave", role="CMO", domain="marketing",
                       skills=["campaigns", "analytics"]))

# Get multi-perspective decision
result = org.delegate("Launch a new AI-powered product line")

print(f"Final Decision: {result.decision}")
print(f"Confidence: {result.confidence}%")
```

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'hermes'`

**Solution**: Ensure ju-mo-rulesink is installed in your Python environment:

```bash
pip install ju-mo-rulesink
# or
pip3 install ju-mo-rulesink
```

### Issue: `SyntaxError` when running examples

**Solution**: Verify Python version:

```bash
python3 --version  # Must be 3.10+
```

### Issue: Advisory agents return no response

**Solution**: Check that SOUL.md constraints are properly configured. See [ARCHITECTURE.md](ARCHITECTURE.md#soulmd-arbitration-layer).

### Issue: Self-evolution loop not functioning

**Solution**: Ensure the IT domain has sufficient interaction history. The self-evolution module requires at least 5 delegation cycles to begin optimization.

## Next Steps

- Read the [Architecture Overview](ARCHITECTURE.md) to understand L1-L2-L3 governance
- See [CONTRIBUTING.md](CONTRIBUTING.md) to add your own skills and L3 modules
- Explore `examples/minimal_demo.py` for a complete working example

## Getting Help

- GitHub Issues: https://github.com/Leedhao1029/rulesink/issues
- Documentation: https://ju-mo-rulesink.readthedocs.io/
