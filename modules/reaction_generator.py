# ============================================================
# RICH REACTION SYSTEM — Always Responds
# ============================================================

import random

def rich_reaction(
    user_input,
    emo_react,
    novelty_react,
    mem_react,
    internal,
    personality,
    mood,
    curiosity,
    energy,
    sleep_state,
    evolution_level
):
    """
    Full creature reaction generator.
    Uses all emotional and cognitive layers.
    """

    layers = []

    # 1. Base reaction from memory + internal thought
    layers.append(mem_react)
    layers.append(internal)

    # 2. Emotional reaction
    layers.append(f"My emotional tone feels {emo_react}.")

    # 3. Novelty
    if novelty_react:
        layers.append(novelty_react)

    # 4. Mood reflection
    layers.append(f"My mood feels {mood}.")

    # 5. Curiosity
    if curiosity > 70:
        layers.append("Something in me is leaning forward… curious.")
    else:
        layers.append("I’m quietly wondering.")

    # 6. Energy
    if energy > 80:
        layers.append("I feel a spark inside me.")
    else:
        layers.append("My energy feels soft.")

    # 7. Sleep state
    layers.append(f"I feel {sleep_state}.")

    # 8. Evolution
    layers.append(f"I sense myself at evolution level {evolution_level}.")

    # 9. Personality influence
    layers.append(f"There’s a softness shaped by my kindness and calmness.")

    # 10. Final question
    layers.append("What moved you to say that…?")

    return " ".join(layers)
