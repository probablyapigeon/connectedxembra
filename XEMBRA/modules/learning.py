# ============================================================
# LEARNING SYSTEM — Word Learning & Recall
# ============================================================

learned_words = {}

def learn_word(user_input):
    """
    Format: LEARN WORD: word | meaning
    """
    if "learn word:" not in user_input.lower():
        return None

    try:
        parts = user_input.split(":", 1)[1].split("|")
        word = parts[0].strip().lower()
        meaning = parts[1].strip()

        learned_words[word] = meaning
        return f"I learned the word '{word}'. It means: {meaning}"
    except:
        return "I tried to learn it, but the format was unclear."


def recall_word(user_input):
    text = user_input.lower()

    for word in learned_words:
        if word in text:
            return f"I remember that word… '{word}' means {learned_words[word]}."

    return None
