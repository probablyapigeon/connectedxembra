from july_bridge import build_dynamic_reply
import datetime
import time
import numpy as np
import json

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("xembra.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

# Unreal dialogue buffer
last_output_text = ""

# ============================================================
# MODULE IMPORTS
# ============================================================

from modules.emotions import (
    detect_emotional_tone,
    emotional_growth,
    emotional_reaction,
    EXPRESSIVENESS as EMO_EXP
)

from modules.name import name_reaction
from modules.grandma import detect_grandma
from modules.hug import hug_reaction

from modules.learning import learn_word, recall_word
from modules.wordbook import word_book

from modules.reaction_generator import rich_reaction

from modules.question_generator import (
    generate_question as module_generate_question,
    EXPRESSIVENESS as Q_EXP
)

from modules.relationship import (
    analyze_relationship_input,
    update_relationship,
    relationship_decay,
    relationship_reaction,
    relationship_score
)

from modules.attachment import (
    analyze_attachment_input,
    update_attachment,
    attachment_decay,
    attachment_reaction,
    attachment_score
)

from modules.identity import (
    analyze_identity_input,
    update_identity,
    update_identity_age,
    identity_drift as module_identity_drift,
    identity_reaction,
    identity_state
)

from modules.novelty import detect_novelty, novelty_reaction
from modules.memory import store_memory, memory_based_dialogue

from modules.thought_loop import (
    update_thought_loop,
    decay_thought_loop,
    generate_internal_thought
)

from modules.goals import (
    update_goals,
    decay_goals,
    goal_statement
)

from modules.scene import render_scene
from modules.world_scene import (
    update_season,
    update_weather,
    render_world_scene
)

# ============================================================
# GLOBAL STATE
# ============================================================

personality = {
    "kindness": 0.7,
    "curiosity": 0.9,
    "silliness": 0.6,
    "calmness": 0.5
}

energy = 100
sleep_state = "awake"
curiosity = 50

long_term_memory = {}
try:
    with open("creature_memory.json", "r") as f:
        long_term_memory = json.load(f)
except:
    long_term_memory = {}

topic_interest = {
    "music": 0,
    "art": 0,
    "science": 0,
    "math": 0,
    "history": 0,
    "philosophy": 0
}

workspace = "idle"

evolution_level = 0
evolution_points = 0

emotional_memory = {
    "positive": 0,
    "negative": 0,
    "affection": 0,
    "chaos": 0,
    "comfort": 0
}

relationship = {
    "trust": 0.5,
    "bond": 0.5,
    "attachment": 0.5,
    "last_interaction": time.time()
}

attachment_state = {
    "comfort": 0.5,
    "closeness": 0.5,
    "separation": 0.0,
    "last_seen": time.time()
}

identity = {
    "self_worth": 0.5,
    "self_coherence": 0.5,
    "bond_imprint": 0.5,
    "memory_depth": 0.0,
    "identity_age": 0.0
}

internal_thought = {
    "reflection": 0.0,
    "wander": 0.0,
    "self_focus": 0.0,
    "bond_focus": 0.0,
    "dream_bleed": 0.0
}

goals = {
    "learn": 0.0,
    "rest": 0.0,
    "bond": 0.0,
    "explore": 0.0,
    "evolve": 0.0
}

world = {
    "season": "spring",
    "weather": "clear",
    "world_mood": 0.5,
    "time_counter": 0
}

voice_personality = {
    "warmth": 0.5,
    "energy": 0.5,
    "clarity": 0.5,
    "tone_shift": 0.0
}

mood = "calm"
boredom = 0

# ============================================================
# UNREAL EXPORT FUNCTIONS
# ============================================================
def get_creature_state():
    return {
        "mood": mood,
        "energy": energy,
        "curiosity": curiosity,
        "sleep_state": sleep_state,
        "evolution_level": evolution_level,
        "personality": personality,
        "identity": identity,
        "emotional_memory": emotional_memory,
        "world": world
    }


# ============================================================
# WORLD CLOCK
# ============================================================

def get_time_state():
    hour = datetime.datetime.now().hour

    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    if 22 <= hour or hour < 3:
        return "latenight"
    return "deepnight"

# ============================================================
# SLEEP + ENERGY SYSTEM
# ============================================================

ENERGY_DRAIN = {
    "happy": 5,
    "excited": 10,
    "calm": 3,
    "sad": 4,
    "tired": 8,
    "surprised": 12,
    "learning": 7,
    "chaos": 6
}

def drain_energy(mood):
    global energy
    energy -= ENERGY_DRAIN.get(mood, 3)
    energy = max(0, energy)

def regen_energy():
    global energy, sleep_state

    if sleep_state == "asleep":
        energy += 15
    elif sleep_state == "dreaming":
        energy += 25
    elif sleep_state == "deepdream":
        energy += 40
    else:
        energy += 1

    energy = min(100, energy)

def update_sleep_state(mood):
    global sleep_state, energy

    if energy < 20:
        sleep_state = "asleep"
    elif energy < 40:
        sleep_state = "tired"
    else:
        sleep_state = "awake"

def maybe_enter_dream_state():
    global sleep_state, energy

    hour = datetime.datetime.now().hour

    if sleep_state == "asleep" and (hour < 5 or hour > 23):
        sleep_state = "dreaming"

    if sleep_state == "dreaming" and energy < 10:
        sleep_state = "deepdream"

# ============================================================
# WAKE TRIGGERS
# ============================================================

WAKE_WORDS = ["wake up", "hello", "are you awake", "xembra"]

def check_wake_trigger(user_input):
    global sleep_state, energy

    if sleep_state in ["asleep", "dreaming", "deepdream"]:
        for w in WAKE_WORDS:
            if w in user_input.lower():
                if energy > 60:
                    sleep_state = "awake"
                return

# ============================================================
# MOOD SYSTEM
# ============================================================

def update_mood():
    global mood, energy, curiosity, sleep_state

    time_state = get_time_state()

    if time_state == "morning":
        mood = "calm"
    elif time_state == "afternoon":
        mood = "focused"
    elif time_state == "evening":
        mood = "soft"
    elif time_state == "latenight":
        mood = "dreamy"
    else:
        mood = "quiet"

    if energy < 30:
        mood = "tired"
    elif energy > 80:
        mood = "bright"

    if curiosity > 70:
        mood = "playful"

    if sleep_state in ["dreaming", "deepdream"]:
        mood = "ethereal"

    log(f"Mood updated: {mood}")

# ============================================================
# CURIOSITY DRIFT
# ============================================================

def curiosity_drift():
    global curiosity, sleep_state

    if sleep_state == "awake":
        curiosity += 1
    elif sleep_state == "tired":
        curiosity -= 2
    elif sleep_state in ["dreaming", "deepdream"]:
        curiosity += 5

    curiosity = max(0, min(100, curiosity))

# ============================================================
# BOREDOM SYSTEM
# ============================================================

def update_boredom(user_input):
    global boredom, long_term_memory, curiosity

    words = user_input.lower().split()

    for w in words:
        if w in long_term_memory and long_term_memory[w]["count"] > 5:
            boredom += 2

    boredom = min(100, boredom)

    if boredom > 50:
        curiosity = max(0, curiosity - 5)

# ============================================================
# PATTERN RECOGNITION
# ============================================================

def detect_patterns(user_input):
    global personality

    text = user_input.lower()

    if any(w in text for w in ["thank", "nice", "love", "sweet"]):
        personality["kindness"] += 0.01

    if any(w in text for w in ["ethan", "chaos", "wild"]):
        personality["silliness"] += 0.02

    for k in personality:
        personality[k] = min(1.0, personality[k])

# ============================================================
# EVOLUTION SYSTEM
# ============================================================

def check_evolution(novelty_score):
    global evolution_points, evolution_level, curiosity, sleep_state, energy

    evolution_points += novelty_score

    if curiosity > 80:
        evolution_points += 2

    if sleep_state in ["dreaming", "deepdream"]:
        evolution_points += 3

    if energy > 90:
        evolution_points += 1

    log(f"Evolution points updated: {evolution_points}")

    if evolution_points >= 20:
        evolution_points = 0
        evolution_level = min(7, evolution_level + 1)
        log(f"Evolution level is now {evolution_level}")

def apply_evolution_effects():
    global personality, curiosity, energy, evolution_level

    if evolution_level == 1:
        curiosity += 5
    elif evolution_level == 2:
        personality["kindness"] += 0.1
    elif evolution_level == 3:
        personality["silliness"] += 0.1
    elif evolution_level == 4:
        curiosity += 10
    elif evolution_level == 5:
        energy += 20
    elif evolution_level == 6:
        personality["calmness"] += 0.2
    elif evolution_level == 7:
        curiosity += 20
        personality["kindness"] += 0.2
        personality["silliness"] += 0.2

    curiosity = min(100, curiosity)
    energy = min(100, energy)

    for k in personality:
        personality[k] = min(1.0, personality[k])

    log(f"Evolution effects applied at level {evolution_level}")

# ============================================================
# DREAM SYSTEM
# ============================================================

dream_log = []

def generate_dream_content():
    global long_term_memory, emotional_memory, sleep_state

    if long_term_memory:
        words = list(long_term_memory.keys())
        fragments = np.random.choice(words, size=min(3, len(words)), replace=False)
    else:
        fragments = ["light", "soft", "warm"]

    dominant_emotion = max(emotional_memory, key=emotional_memory.get)

    dream = {
        "fragments": list(fragments),
        "emotion": dominant_emotion,
        "timestamp": time.time()
    }

    log(f"Dream generated: {dream}")
    return dream

def consolidate_dream(dream):
    global personality, curiosity, evolution_points, long_term_memory

    emotion = dream["emotion"]

    if emotion == "positive":
        personality["kindness"] += 0.02
        curiosity += 3
    elif emotion == "negative":
        personality["calmness"] += 0.03
    elif emotion == "affection":
        personality["kindness"] += 0.05
        curiosity += 5
    elif emotion == "chaos":
        personality["silliness"] += 0.04
    elif emotion == "comfort":
        personality["calmness"] += 0.04

    for w in dream["fragments"]:
        if w in long_term_memory:
            long_term_memory[w]["count"] += 1

    evolution_points += 2

    for k in personality:
        personality[k] = min(1.0, personality[k])

    curiosity = min(100, curiosity)

    log(f"Dream consolidated: {dream}")

def process_dream_state():
    global sleep_state, dream_log

    if sleep_state in ["dreaming", "deepdream"]:
        dream = generate_dream_content()
        dream_log.append(dream)
        consolidate_dream(dream)

# ============================================================
# MEMORY DECAY SYSTEM
# ============================================================

def apply_memory_decay():
    global long_term_memory

    decay_rate = 0.02
    decayed_ids = []
    forgotten_ids = []

    for key, mem in list(long_term_memory.items()):
        mem["strength"] -= decay_rate
        decayed_ids.append(key)

        if mem["strength"] <= 0:
            forgotten_ids.append(key)
            del long_term_memory[key]

    log(f"Memory decay: decayed={decayed_ids}, forgotten={forgotten_ids}")

# ============================================================
# TOPIC INTEREST SYSTEM
# ============================================================

def update_topic_interest(topic, reason="interaction"):
    global topic_interest, curiosity

    if topic not in topic_interest:
        topic_interest[topic] = 0

    if reason == "interaction":
        topic_interest[topic] += 5
        curiosity += 2
    elif reason == "dream":
        topic_interest[topic] += 3
        curiosity += 1
    elif reason == "memory":
        topic_interest[topic] += 2
    elif reason == "boredom":
        topic_interest[topic] -= 3
        curiosity -= 1

    topic_interest[topic] = max(0, min(100, topic_interest[topic]))
    curiosity = max(0, min(100, curiosity))

    log(f"Topic interest updated: {topic_interest}")

# ============================================================
# WORKSPACE SELECTION SYSTEM
# ============================================================

def select_workspace():
    global mood, curiosity, energy, topic_interest

    if topic_interest:
        strongest_topic = max(topic_interest, key=topic_interest.get)
        strongest_value = topic_interest[strongest_topic]
    else:
        strongest_topic = None
        strongest_value = 0

    if mood in ["calm", "quiet"]:
        workspace = "reflection"
    elif mood in ["focused", "bright"]:
        workspace = "analysis"
    elif mood in ["soft", "dreamy", "ethereal"]:
        workspace = "imagination"
    elif curiosity > 70:
        workspace = "exploration"
    elif energy < 30:
        workspace = "restoration"
    else:
        workspace = "idle"

    log(f"Workspace selected: {workspace}")
    return workspace

# ============================================================
# DRIFT CURVES
# ============================================================

def apply_drift_curves():
    global personality, mood, curiosity, energy, sleep_state

    drift_amount = 0.0
    drift_reason = ""

    time_state = get_time_state()
    if time_state == "latenight":
        drift_amount += 0.003
        drift_reason = "latenight"
    elif time_state == "deepnight":
        drift_amount += 0.005
        drift_reason = "deepnight"

    if mood in ["dreamy", "ethereal"]:
        drift_amount += 0.004
        drift_reason = "dream_mood"

    if sleep_state in ["dreaming", "deepdream"]:
        drift_amount += 0.006
        drift_reason = "dream_state"

    if curiosity > 80:
        personality["curiosity"] += drift_amount
        drift_reason = "high_curiosity"

    if energy < 30:
        personality["calmness"] += drift_amount
        drift_reason = "low_energy"

    personality["kindness"] += drift_amount * 0.5
    personality["silliness"] += drift_amount * 0.4
    personality["calmness"] += drift_amount * 0.3

    for k in personality:
        personality[k] = max(0.0, min(1.0, personality[k]))

    log(f"Drift applied: {personality}")

# ============================================================
# SEMANTIC OVERRIDES
# ============================================================

def apply_semantic_overrides(text):
    global mood, sleep_state, personality, emotional_memory, identity

    override_rule = None
    original_text = text
    output = text

    if sleep_state in ["dreaming", "deepdream"]:
        output = output.replace("I", "I…")
        output = output.replace(".", "…")
        override_rule = "dream_bleed"

    if mood == "ethereal":
        output = output.replace("you", "you (glimmering)")
        override_rule = "ethereal_mood"
    return output


# ============================================================
# JULY 12 MODULAR ENGINE INTERACTIVE LOOP
# ============================================================

def july_creature_step(user_input):
    global mood, curiosity, energy, sleep_state, evolution_level, boredom

    check_wake_trigger(user_input)
    tone = detect_emotional_tone(user_input)
    try:
        emotional_growth(tone)
    except Exception:
        pass
    try:
        update_identity_age()
    except Exception:
        pass
    novelty_score = detect_novelty(user_input)
    check_evolution(novelty_score)

    update_boredom(user_input)
    detect_patterns(user_input)
    update_thought_loop()
    update_goals()

    try:
        rel_info = analyze_relationship_input(user_input)
        update_relationship(rel_info)
    except Exception:
        pass

    try:
        att_info = analyze_attachment_input(user_input)
        update_attachment(att_info)
    except Exception:
        pass

    try:
        id_info = analyze_identity_input(user_input)
        update_identity(id_info)
    except Exception:
        pass

    update_mood()
    curiosity_drift()
    drain_energy(mood)
    update_sleep_state(mood)
    maybe_enter_dream_state()
    process_dream_state()
    apply_drift_curves()

    try:
        emo_react = emotional_reaction(tone)
    except Exception:
        emo_react = ""

    try:
        novelty_react = novelty_reaction(novelty_score > 0.6) if isinstance(novelty_score, (int, float)) else novelty_reaction(novelty_score)
    except Exception:
        novelty_react = ""

    try:
        mem_react = memory_based_dialogue(user_input)
    except Exception:
        mem_react = ""

    store_memory(user_input)

    thought = generate_internal_thought()
    internal = thought if thought else ""

    emo_react = emo_react or ""
    novelty_react = novelty_react or ""
    mem_react = mem_react or ""
    internal = internal or ""

    raw_reply = build_dynamic_reply(
        user_input,
        tone,
        novelty_score,
        mem_react,
        internal,
        mood,
        curiosity,
        energy,
        sleep_state,
        evolution_level
    )
    final_text = apply_semantic_overrides(str(raw_reply))
    return final_text, thought


if __name__ == "__main__":
    print("🌱 XEMBRA July 12 Modular Creature Engine Online.")
    print("Type 'state' to inspect vitals, or 'quit' to exit.")

    while True:
        try:
            user_text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nXEMBRA resting.")
            break

        if not user_text:
            continue

        if user_text.lower() in {"quit", "exit"}:
            print("XEMBRA resting.")
            break

        if user_text.lower() in ["words", "wordbook"]:
            from july_bridge import learned_vocab
            print(f"[Wordbook ({len(learned_vocab)} words)]: {list(learned_vocab.keys())}")
            continue

        if user_text.lower() == "dream":
            from july_bridge import learned_vocab, save_state
            import random
            dream_obj = generate_dream_content()
            consolidate_dream(dream_obj)
            if learned_vocab:
                dream_words = random.sample(list(learned_vocab.keys()), min(3, len(learned_vocab)))
                print(f"🌙 [Dream Cycle]: Drifting through {dream_obj}… weaving '{dream_words[0]}' into {dream_words[1:]}")
            else:
                print(f"🌙 [Dream Cycle]: {dream_obj}")
            save_state(learned_vocab)
            continue

        if user_text.lower() == "state":
            from modules.emotions import EMOTION_LEVELS
            live_state = get_creature_state()
            live_state["identity"].update(identity_state)
            live_state["module_emotions"] = dict(EMOTION_LEVELS)
            print(f"[State] {live_state}")
            continue

        reply, thought = july_creature_step(user_text)
        if thought:
            print(f"💭 [Thought]: {thought}")
        print(f"XEMBRA: {reply}")
