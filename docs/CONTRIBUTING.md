# Contributing to 矩墨RulesInk

MIT License — Pull requests welcome.

## Development Setup

```bash
git clone https://github.com/Leedhao1029/rulesink.git
cd ju-mo-rulesink
pip install -e .
```

## Package Structure

```
ju-mo-rulesink/
├── hermes/                          # Core framework (MIT)
│   ├── dispatcher.py                 # L1 intent routing (public interface)
│   ├── l3_base.py                   # L3 base class (full implementation)
│   ├── soul_arbiter.py              # SOUL constraint interface
│   └── base_orchestrator.py          # L2 orchestrator interface
├── domains/                         # Domain modules (MIT)
│   ├── it/                           # IT domain
│   │   ├── orchestrator.py           # IT L2 (public architecture)
│   │   └── self_evolution.py         # Self-evolution loop (public interface)
│   ├── ecommerce/
│   ├── construction/
│   ├── investment/
│   ├── life/
│   └── multimodal/
├── council/                          # Advisory council (MIT)
│   └── advisory_council.py           # 4-advisor panel (public architecture)
├── skills/                           # Skill definitions (MIT)
├── protocol/                          # Governance protocols (MIT)
│   └── company_capability_development_protocol.py
└── examples/
    ├── minimal_demo.py
    └── advisory_council_example.py
```

## Creating a New L3 Script

Every L3 script must:
1. Inherit from `L3Base`
2. Implement `run(params: dict) -> dict`
3. Call `finalize()` before returning
4. Include `SKILL_NAME` constant
5. Follow the handoff protocol

```python
#!/usr/bin/env python3
"""l3_domain_capability.py — My new L3 script"""

import json
from pathlib import Path
from hermes.l3_base import L3Base

SCRIPT_NAME = "l3_domain_capability"
VERSION = "1.0"
SKILL_NAME = "my-capability"

class MyCapability(L3Base):
    def __init__(self):
        super().__init__()
        self.SCRIPT_NAME = SKILL_NAME
        self.VERSION = VERSION

    def run(self, params: dict) -> dict:
        result = {
            "finding": "...",
            "data": [],
            "issues": [],
        }
        verified = self.verify_output(result, ["finding"])
        result["_verified"] = verified["pass"]
        return self.finalize(result, quality_status=verified["quality_status"])

if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:])
    result = MyCapability().run({"_raw_task": task})
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

## Creating a New Skill

Create `skills/my-skill/SKILL.md`:

```markdown
---
name: my-skill
description: One-line description of what this skill does.
trigger_on:
  - keyword1
  - keyword2
  - keyword3
---

# My Skill

## Steps
1. Step one
2. Step two

## Pitfalls
- Common mistake and how to avoid it

## Examples
### Example 1
...

## Verification
How to verify the skill worked correctly.
```

## Import Convention

```python
# Correct — use the public package interface
from hermes_native_organization import dispatch, L3Base, SOULArbiter

# Correct — domain-specific imports
from hermes_native_organization.domains.it.orchestrator import orchestrate

# Wrong — internal paths
from hermes_native_organization.hermes.dispatcher import _infer_domain  # private
```

## Running Tests

```bash
# Verify syntax
python3 -m py_compile hermes/*.py
python3 -m py_compile domains/*/*.py

# Run example
python3 examples/advisory_council_example.py
```

## What NOT to Contribute

- Any code that contains proprietary threshold values
- Any code that exposes internal routing algorithms
- Any code that contains private pattern databases
- Any code that attempts to bypass the SOUL constraint layer

## License

MIT — see LICENSE file.
