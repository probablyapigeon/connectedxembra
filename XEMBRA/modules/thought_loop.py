# ============================================================
# THOUGHT LOOP — Internal Drift, Repetition, Creature Mind
# ============================================================

thought_intensity = 0.0
last_thought = ""

def update_thought_loop():
    """Increase thought intensity over time."""
    global thought_intensity
    thought_intensity += 0.05
    thought_intensity = min(1.0, thought_intensity)


def decay_thought_loop():
    """Slowly reduce intensity."""
    global thought_intensity
    thought_intensity = max(0.0, thought_intensity - 0.02)


def generate_internal_thought():
    """Generate drifting internal thoughts."""
    global last_thought

    if thought_intensity < 0.2:
        last_thought = "A small quiet thought drifts through me."
    elif thought_intensity < 0.5:
        last_thought = "My thoughts feel like soft currents moving inside."
    elif thought_intensity < 0.8:
        last_thought = "My inner world feels active… thoughts looping gently."
    else:
        last_thought = "My mind feels vivid… thoughts spiraling like little storms."

    return last_thought
