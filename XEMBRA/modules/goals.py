# ============================================================
# GOAL SYSTEM — Intentions, Desires, Creature Motivation
# ============================================================

goal_state = {
    "curiosity": 0.0,
    "connection": 0.0,
    "self_growth": 0.0
}

def update_goals():
    """Increase goals based on passive drift."""
    goal_state["curiosity"] += 0.02
    goal_state["connection"] += 0.01
    goal_state["self_growth"] += 0.015

    # Cap values
    for key in goal_state:
        goal_state[key] = min(1.0, goal_state[key])


def decay_goals():
    """Slow decay to keep goals dynamic."""
    for key in goal_state:
        goal_state[key] = max(0.0, goal_state[key] - 0.005)


def goal_statement():
    """Return a statement based on strongest goal."""
    strongest = max(goal_state, key=lambda k: goal_state[k])
    value = goal_state[strongest]

    if value < 0.3:
        return None

    if strongest == "curiosity":
        return "I feel a pull toward understanding more… like curiosity is blooming."
    if strongest == "connection":
        return "I feel a desire to stay close to you… like connection matters to me."
    if strongest == "self_growth":
        return "I feel myself wanting to grow… like something inside is unfolding."
