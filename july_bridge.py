import os
import json
import random
from modules.name import name_reaction
from modules.grandma import detect_grandma
from modules.hug import hug_reaction
from modules.learning import learn_word, recall_word
import modules.question_generator as qgen
from modules.translator import translator_state
from modules.world_scene import world_state, update_weather
from modules.emotions import EMOTION_LEVELS
from modules.identity import identity_state

MEMORY_FILE = "july_memory.json"

STOPWORDS = {
    "that", "this", "with", "from", "have", "what", "when", "where",
    "which", "their", "there", "about", "would", "could", "should",
    "into", "just", "like", "your", "they", "them", "been", "were",
    "are", "for", "and", "the", "you", "was", "not", "but", "how",
    "okay", "really", "very", "much", "many", "some", "more", "most",
    "seemed", "seems", "seem", "feeling", "feel", "feels", "think",
    "thought", "know", "knew", "want", "wanted", "going", "saying",
    "said", "make", "made", "take", "took", "takes", "come", "came",
    "because", "still", "even", "also", "only", "well", "back", "here",
    "then", "basically", "suggests", "suggest", "step", "hanging",
    "around", "being", "having", "doing", "thats", "youre", "hows",
    "whats", "theres", "im", "ive", "ill", "id", "dont", "cant", "wont",
    "things", "thing", "over", "down", "near", "might", "create", "pull",
    "measures", "spreads", "resting", "slowing", "bends",
    "through", "tell", "rising", "every", "after", "before", "under",
    "above", "between", "during", "without", "within", "along", "across"
}

def load_state():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "emotions" in data:
                    EMOTION_LEVELS.update(data["emotions"])
                if "identity" in data:
                    identity_state.update(data["identity"])
                if "emotional_memory" in data:
                    import xembra_july_live as xjl
                    xjl.emotional_memory.update(data["emotional_memory"])
                return data.get("vocab", {})
        except Exception:
            pass
    return {}

def save_state(vocab):
    try:
        try:
            import xembra_july_live as xjl
            emo_mem = xjl.emotional_memory
        except Exception:
            emo_mem = {}
        payload = {
            "vocab": vocab,
            "emotions": EMOTION_LEVELS,
            "identity": identity_state,
            "emotional_memory": emo_mem
        }
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass

learned_vocab = load_state()

def extract_concepts(text):
    raw_words = [w.strip(".,!?;:\"'()[]") for w in text.split()]
    concepts = []
    for i, w in enumerate(raw_words):
        clean = w.replace("'", "").replace("’", "")
        low = clean.lower()
        if len(low) > 3 and low not in STOPWORDS:
            is_proper = clean[0].isupper() and (i > 0 or low == "einstein")
            concepts.append(clean if is_proper else low)
    unique = list(dict.fromkeys(concepts))
    unique.sort(key=lambda x: (x[0].isupper(), len(x)), reverse=True)
    return unique

def build_dynamic_reply(user_input, tone, novelty_score, mem_react, internal, mood, curiosity, energy, sleep_state, evolution_level):
    parts = []

    for fn in (translator_state, hug_reaction, name_reaction, detect_grandma):
        try:
            res = fn(user_input)
            if res:
                parts.append(str(res))
        except Exception:
            pass

    concepts = extract_concepts(user_input)
    new_concepts = []
    known_concepts = []

    for word in concepts:
        low = word.lower()
        recalled = None
        try:
            recalled = recall_word(low)
        except Exception:
            pass

        if recalled or low in learned_vocab:
            known_concepts.append(word)
        else:
            try:
                learn_word(low, user_input)
            except Exception:
                pass
            learned_vocab[low] = user_input
            new_concepts.append(word)

    save_state(learned_vocab)

    if new_concepts:
        if len(new_concepts) >= 2:
            w1, w2 = new_concepts[0], new_concepts[1]
            weave_templates = [
                f"I'm holding onto '{w1}' and '{w2}' in my thoughts now…",
                f"'{w1}' and '{w2}' feel like new sparks clicking together inside me.",
                f"Ooh, '{w1}'… and '{w2}'… I'm weaving those into how I see things."
            ]
        else:
            w1 = new_concepts[0]
            weave_templates = [
                f"I'm tucking '{w1}' into my wordbook… it feels important.",
                f"'{w1}' has a curious weight to it… I want to understand more.",
                f"Ooh, '{w1}'… a new piece of your world."
            ]
        parts.append(random.choice(weave_templates))

    elif known_concepts:
        recalled_word = known_concepts[0]
        recall_templates = [
            f"Hearing '{recalled_word}' again makes the earlier pattern glow a little brighter.",
            f"Ah, '{recalled_word}'… that connects back to what you shared with me before.",
            f"I remember '{recalled_word}'… it's still drifting through my thoughts."
        ]
        parts.append(random.choice(recall_templates))

    all_learned = [w for w in learned_vocab.keys() if w not in [c.lower() for c in concepts]]
    if all_learned and (new_concepts or known_concepts) and random.random() < 0.55:
        anchor = new_concepts[0] if new_concepts else known_concepts[0]
        old_word = random.choice(all_learned)
        parts.append(f"I wonder how '{anchor}' connects to '{old_word}'…")

    if internal and random.random() < 0.45:
        parts.append(str(internal))

    if random.random() < 0.25:
        update_weather()
        parts.append(f"[{world_state['season'].capitalize()}, {world_state['weather']}]")

    try:
        qgen.EXPRESSIVENESS = 3 if curiosity > 75 else (2 if curiosity > 55 else 1)
        if concepts and random.random() < 0.65:
            focus = concepts[0]
            concept_questions = [
                f"What fascinates you most about {focus}?",
                f"How does {focus} feel to you when you think about it?",
                f"What else connects to {focus} in your mind?"
            ]
            parts.append(random.choice(concept_questions))
        else:
            q = qgen.generate_question(user_input, novelty_score if isinstance(novelty_score, (int, float)) else 0.0)
            if q:
                parts.append(str(q))
    except Exception:
        pass

    if not parts:
        parts.append(f"I'm listening ({mood}, energy {energy})...")

    return " ".join(parts)
