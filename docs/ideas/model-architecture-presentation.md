# Social Cybernetics Sugarscape Model Architecture

## 6-Slide PowerPoint Presentation

---

### **Slide 1: Title Slide**

# 🎯 Social Cybernetics Sugarscape

### A Research-First Agent-Based Model

**Version:** 0.1 (Deterministic Material Control)  
**Date:** August 2026  
**Research Question:** How do simple survival rules evolve into complex social systems?

---

### **Slide 2: The Core Problem**

## 🎯 What We're Building

A computer simulation that helps us understand:

✅ How cognitive tools spread and change behavior  
✅ How norms and rules emerge from individual actions  
✅ How institutions form and persist  
✅ How inequality and resource access patterns develop

## 🤔 The Challenge

**How to keep the SCIENCE independent from the SIMULATION?**

- Scientists think in equations and mechanisms
- Simulations need frameworks, UIs, and tooling  
- We need both to work together without contaminating each other

---

### **Slide 3: The Architecture Principle**

## 🏗️ Separation of Concerns

```
CLI / Configuration / Visualisation
           ↓
    Mesa Runtime Adapter
           ↓
     Pure Domain Core
```

## ⚡ Why This Matters

- **Domain Core** = The science (what we're studying)
- **Runtime Shell** = The simulation (how we run it)
- **Dependencies only point downward**

## 🎯 The Magic: Framework-Independent Science

```python
# Domain code can import:
import numpy as np
from typing import Protocol

# Domain code CANNOT import:
import mesa        # ❌ No simulation framework
import pandas      # ❌ No analysis tools
import solara      # ❌ No UI framework
```

---

### **Slide 4: The Domain Core (What We Study)**

## 🧠 Pure Scientific State

### Agent State (Typed Records):
- `energy_reserve`: How much energy the agent has
- `location`: Where the agent is on the grid
- `alive/dead`: Survival status
- `observation`: What the agent sees
- `belief`: What the agent thinks is true
- `action_intent`: What the agent wants to do

### World State:
- `resource_stock`: How much food is in each cell
- `regeneration_rate`: How fast food grows back

## 📋 The 10 Non-Negotiable Rules

1. ✅ Reality ≠ Observation (agents only see what they're allowed to see)
2. ✅ Observation ≠ Belief (what you see isn't what you believe)
3. ✅ Intention ≠ Action (wanting to do something ≠ doing it)
4. ✅ Stocks remain distinct (energy ≠ resources ≠ holdings)
5. ✅ Process order is scientific content (the sequence matters)
6. ✅ One random origin per run (reproducibility)
7. ✅ Competition is explicit (no hidden priority systems)
8. ✅ Mortality preserves evidence (dead agents still count)
9. ✅ Configuration is provenance (every parameter is tracked)
10. ✅ Mechanism needs evidence (no unverified features)

---

### **Slide 5: The Runtime Shell (How We Run It)**

## 🏗️ Mesa Integration Layer

### Mesa Model Owns:
- The random seed (ensures reproducibility)
- All random number generators
- The simulation scheduler
- Property layers (environmental arrays)

### Mesa Agents Own:
- Position coordinates
- Activation/deactivation
- Visualization state

## 🔄 The Execution Pipeline

```
Tick 0 → Tick 1 → Tick 2 → ... → Tick N
   ↓        ↓        ↓           ↓
Resources → Observation → Belief → Decision → Resolution → Feedback
```

## 🎯 Key Design Decisions

- **Deterministic by default** (same seed = same outcome)
- **Side-effect-free agents** (no direct mutation)
- **Centralized resolution** (all actions resolved together)
- **Immutable snapshots** (state at each tick is preserved)

---

### **Slide 6: The Research Roadmap & Next Steps**

## 📅 Versioned Development Plan

| Version | Mechanism Added | Status | When? |
|---------|-----------------|--------|-------|
| v0.1 | Deterministic ecology, material agents | 🔴 Implementing | Now |
| v0.2 | Heterogeneous ecology, shocks | 🟡 Specified | Next |
| v0.3 | Fixed information capabilities | 🟡 Specified | Following |
| v0.4 | Private Q-learning | 🟡 Specified | Following |
| v0.5 | Tool diffusion & networks | 🟡 Specified | Following |
| v0.6 | Norm diffusion & enforcement | 🟡 Specified | Following |
| v0.7 | Nested governance & regimes | 🟡 Specified | Following |
| v0.8 | Transfers & exchange | 🟡 Specified | Following |
| v0.9 | Births & demographic turnover | 🟡 Specified | Following |

## ✅ The Verification Process

**Before each version ships:**
- ✅ Unit tests for new mechanisms
- ✅ Property tests for conservation laws
- ✅ Small-world integration tests
- ✅ Fixed-seed regression traces
- ✅ Specification vs. executable agreement

## 🎯 Success Criteria

- **v0.1 Gate:** Deterministic verification passes
- **v0.2 Gate:** Stochastic ecological patterns validated
- **v0.3 Gate:** Information access effects measurable
- **Each version:** One mechanism, one control

---

## 📊 Key Takeaways

### 🎯 Three Big Wins

1. **Scientific Integrity**
   - Science stays pure and independent
   - No framework contamination
   - Verification at every step

2. **Reproducibility**
   - Same seed = same outcome
   - Configuration is validated
   - Records are immutable

3. **Extensibility**
   - Add new mechanisms without breaking old ones
   - Framework migration is possible
   - Multiple analysis paths

### 💡 The Architecture in One Sentence

**"We built a system where the science can evolve independently of the simulation technology, ensuring that every discovery is trustworthy and verifiable."**

---

## 💬 Questions & Discussion

### 🤔 Open Questions

1. How do we ensure the domain core stays truly framework-independent?
2. What's the best way to validate the deterministic control model?
3. How should we structure the configuration system for maximum flexibility?
4. What visualization tools will best serve both debugging and analysis?

### 🚀 Next Steps

- [ ] Complete v0.1 implementation
- [ ] Set up deterministic verification ladder
- [ ] Create fixed-seed regression tests
- [ ] Design configuration validation schema
- [ ] Build basic CLI interface
- [ ] Implement simple visualization

### 📚 Resources

- **Code:** `/src/social_cybernetics/domain/` (pure science)
- **Runtime:** `/src/social_cybernetics/runtime/mesa/` (simulation layer)
- **Docs:** `/docs/architecture.md`, `/docs/model_specification.md`
- **Tests:** `/tests/` (verification suite)
