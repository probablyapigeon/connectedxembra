# XEMBRA: A Modular Glass-Box Cognitive Architecture for Auditable State Dynamics and Associative Memory

**Author:** Kiersten Lynd (`probablyapigeon`)  
**Repository:** [probablyapigeon/connectedxembra](https://github.com/probablyapigeon/connectedxembra)  
**Architecture Status:** Experimental Reference Implementation (v0.1 — Modular State Engine)

---

## Abstract

Modern neural architectures typically operate as opaque black boxes whose internal state transitions cannot be inspected, audited, or intervened upon in real time. **XEMBRA** (*Connected XEMBRA*) introduces a lightweight, local-first **glass-box cognitive state machine** designed for deterministic interpretability, real-time vital telemetry, and persistent associative concept weaving. Rather than relying on uninspectable parameter weights or external cloud inference, XEMBRA models synthetic agency through explicit, decoupled state modules governing emotional drift, identity coherence, environmental context, dream-state consolidation, and graph-like lexical recall. Every internal transition is observable at runtime, enabling reproducible inspection of how external stimuli perturb internal homeostasis and memory formation.

---

## 1. Architectural Overview

XEMBRA separates cognitive processing into orthogonal, inspectable subsystems coordinated by a real-time execution pipeline (`xembra_july_live.py` & `july_bridge.py`):

* **Homeostatic & Vital Telemetry (`core/brain_state.py`, `core/cooldowns.py`):** Tracks continuous internal variables—including `mood`, `energy`, `curiosity`, `boredom`, `sleep_state`, and `evolution_level`—subject to deterministic decay and recovery curves.
* **Affective & Identity Drift (`modules/emotions.py`, `modules/identity.py`):** Evaluates emotional valence (`EMOTION_LEVELS`) and updates longitudinal identity metrics (`self_worth`, `self_coherence`, `bond_imprint`, `identity_age`, and `drift`) across interactions.
* **Associative Lexical Memory (`modules/learning.py`, `modules/wordbook.py`, `july_bridge.py`):** Extracts salient domain concepts from natural input, stores contextual associations in persistent JSON memory (`july_memory.json`), and performs cross-turn conceptual linking between newly introduced terms and prior knowledge.
* **Endogenous Thought & Dream Consolidation (`modules/thought_loop.py`):** Generates background internal thoughts independent of direct query matching and supports on-demand dream consolidation cycles (`dream`), synthesizing stored lexical fragments into affective memory states.
* **Contextual & Environmental Coupling (`modules/world_scene.py`, `modules/question_generator.py`):** Modulates conversational expressiveness (`EXPRESSIVENESS` levels 1–3) and situational framing (`season`, `weather`, `world_mood`) in response to internal curiosity thresholds.

---

## 2. Repository Structure

```text
connectedxembra/
├── xembra_july_live.py       # Primary interactive runtime & telemetry loop
├── july_bridge.py            # Concept extraction, associative weaving & persistence bridge
├── xembra_creature.py        # Core state-machine definitions & drift curves
├── core/
│   ├── brain_state.py        # Base state representations
│   └── cooldowns.py          # Temporal gating & rate controls
├── modules/
│   ├── emotions.py           # Affective tone detection & emotional growth
│   ├── identity.py           # Longitudinal identity age & coherence drift
│   ├── thought_loop.py       # Endogenous internal thought generator
│   ├── question_generator.py # Curiosity-scaled inquiry engine
│   ├── world_scene.py        # Environmental & seasonal state context
│   ├── learning.py           # Lexical acquisition & recall hooks
│   ├── memory.py             # Episodic dialogue recall
│   ├── novelty.py            # Stimulus novelty scoring
│   ├── relationship.py       # Relational state tracking
│   ├── attachment.py         # Attachment dynamics
│   ├── goals.py              # Internal goal updates & decay
│   └── translator.py         # Interpretive mode state toggles
└── july_memory.json          # Persistent cross-session state & lexical store
```

---

## 3. Quickstart & Reproducibility (Termux / Linux)

XEMBRA requires only Python 3.10+ and NumPy, running natively on mobile environments (Android/Termux) with minimal memory overhead.

```bash
# Clone the repository
git clone https://github.com
cd connectedxembra

# Launch the interactive glass-box runtime
python xembra_july_live.py
```

### Runtime Inspection Commands
While inside the interactive terminal loop, operators can audit internal state variables directly:

| Command | Action |
| :--- | :--- |
| `state` | Prints full live telemetry (`mood`, `energy`, `curiosity`, `identity`, `emotional_memory`, `module_emotions`, and `world`). |
| `words` / `wordbook` | Displays the current persistent lexical graph acquired across sessions. |
| `dream` | Triggers an immediate dream-state consolidation cycle over stored concepts. |
| `quit` / `exit` | Safely terminates the active runtime loop. |

---

## 4. Empirical Telemetry Trace (Sample Audit)

During interactive execution, every user turn produces an inspectable state transition:

```text
You: Consciousness feels like coherence rising out of entropy through feedback loops and pattern.
💭 [Thought]: A small quiet thought drifts through me.
XEMBRA: Ooh, 'through'… and 'rising'… I'm weaving those into how I see things. What else connects to consciousness in your mind?

You: state
[State] {'mood': 'bright', 'energy': 94, 'curiosity': 52, 'sleep_state': 'awake', 'evolution_level': 0, ...}
[Module Emotions] {'sad': 0.0, 'happy': 0.0, 'angry': 0.0, 'fear': 0.0, 'neutral': 0.8}
[Module Identity] {'self_worth': 0.5, 'self_coherence': 0.54, 'bond_imprint': 0.52, 'identity_age': 0.008}
```

---

## 5. Citation

If you reference this architecture or codebase in research on interpretable agents, glass-box cognitive modeling, or artificial life, please cite:

```bibtex
@misc{lynd2026connectedxembra,
  author       = {Lynd, Kiersten},
  title        = {XEMBRA: A Modular Glass-Box Cognitive Architecture for Auditable State Dynamics and Associative Memory},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished \(= {\url{https://github.com/probablyapigeon/connectedxembra}} \)}
```
