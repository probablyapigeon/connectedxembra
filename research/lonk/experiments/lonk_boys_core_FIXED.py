import random
import math
import time
import os
import json

TITLE_FOR_PLAYER = "Momma Meat Wizard"



# ============================================================
# SPEECH SYSTEM
# Lonk Dynamics       
# ============================================================
class LonkDynamics:
    def __init__(self):
        # parameters for emotional state transitions
        self.alpha = 0.1   # learning rate
        self.beta = 0.05   # decay
        self.gamma = 0.2   # noise strength

    def step(self, state, s_t, pain_t):
        Psi, theta, A, V, P = state

        # prediction error update
        P = max(0.0, min(1.0, P + pain_t - self.beta * P))

        # arousal update
        A = max(0.0, min(1.0, A + self.alpha * (s_t - A) + self.gamma * (random.random() - 0.5)))

        # valence update
        V = max(0.0, min(1.0, V + 0.1 * (1 - P) - 0.05 * A))

        # Psi update (core emotional energy)
        Psi = max(0.0, min(1.0, Psi + 0.1 * (V - Psi) + 0.05 * (random.random() - 0.5)))

        # theta update (internal expectation)
        theta = max(0.0, min(1.0, theta + 0.05 * (Psi - theta)))

        return [Psi, theta, A, V, P]

# ============================================================
# LONK CLASS
# ============================================================
class Lonk:
    def __init__(self, name):
        self.name = name

        # Emotional dynamical state: [Psi, theta, A, V, P]
        self.state = [0.5, 0.5, 0.2, 0.3, 0.1]
        self.dynamics = LonkDynamics()

        # Emotion dictionary
        self.emotion = {
            "power": 50,
            "courage": 50,
            "wisdom": 50,
            "masochism": 0,
            "joy": 50,
            "anxiety": 50
        }

        # Personality traits
        self.personality = {
            "aggression": 50,
            "curiosity": 50,
            "anxiety": 50,
            "loyalty": 50
        }

        # Habits
        self.habits = {a: 0 for a in ["attack", "explore", "think", "ouch", "idle"]}

        # Memory systems
        self.memory = {
            "player_words": set(),
            "lonk_words": set(),
            "events": [],
            "player_interactions": [],
        }
        self.long_memory = []
        self.vocabulary = {}
        self.language = {}

        # Gossip
        self.gossip = []
        self.max_gossip = 20

        # Social
        self.relationships = {}
        self.friend_threshold = 20
        self.grudge_threshold = -15
        self.social_memory_decay = 0.98
        self.grudges = {}
        self.crush = None
        self.catchphrase = None

        # Lifecycle
        self.age = 0
        self.lifespan = random.randint(30, 80)
        self.trauma = 0
        self.alive = True
        self.generation = 1

        # Items & territory
        self.items = []
        self.inventory = []
        self.territory = None

        # World reference
        self.world = None

        # Safety
        self.ensure_emotion_keys()

    # ------------------------------------------------------------
    # SAFETY
    # ------------------------------------------------------------
    def ensure_emotion_keys(self):
        defaults = {
            "power": 50, "courage": 50, "wisdom": 50,
            "masochism": 0, "joy": 50, "anxiety": 50
        }
        for k, v in defaults.items():
            self.emotion.setdefault(k, v)

    # ------------------------------------------------------------
    # SERIALIZATION
    # ------------------------------------------------------------
    def to_dict(self):
        return {
            "name": self.name,
            "alive": self.alive,
            "age": self.age,
            "generation": self.generation,
            "emotion": self.emotion,
            "personality": self.personality,
            "habits": self.habits,
            "memory": self.memory,
            "long_memory": self.long_memory,
            "gossip": self.gossip,
            "items": self.items,
            "inventory": self.inventory,
            "territory": self.territory,
            "faction": getattr(self, "faction", None),
        }

    @classmethod
    def from_dict(cls, data):
        lonk = cls(data["name"])
        lonk.alive = data.get("alive", True)
        lonk.age = data.get("age", 0)
        lonk.generation = data.get("generation", 1)
        lonk.emotion = data.get("emotion", {})
        lonk.personality = data.get("personality", {})
        lonk.habits = data.get("habits", {})
        lonk.memory = data.get("memory", [])
        lonk.long_memory = data.get("long_memory", [])
        lonk.gossip = data.get("gossip", [])
        lonk.items = data.get("items", [])
        lonk.inventory = data.get("inventory", [])
        lonk.territory = data.get("territory", None)
        lonk.faction = data.get("faction", None)

        # ============================================================
        # MEMORY FIX PATCH — convert JSON lists back into sets
        # ============================================================
        # If memory was saved as a list, convert to dict
        if not isinstance(lonk.memory, dict):
            lonk.memory = {}

        lonk.memory.setdefault("player_words", set())
        lonk.memory.setdefault("lonk_words", set())
        lonk.memory.setdefault("events", [])

        # Convert lists → sets
        if isinstance(lonk.memory["player_words"], list):
            lonk.memory["player_words"] = set(lonk.memory["player_words"])

        if isinstance(lonk.memory["lonk_words"], list):
            lonk.memory["lonk_words"] = set(lonk.memory["lonk_words"])

        lonk.ensure_emotion_keys()
        return lonk

    # ------------------------------------------------------------
    # SPEECH
    # ------------------------------------------------------------
    def speak(self, message=None, target=None, context=None):
        if message is None:
            message = generate_speech(context)
        if target:
            print(f"💬 {self.name} → {target.name}: {message}")
            target.hear(self, message)
        else:
            print(f"💬 {self.name}: {message}")

    # ------------------------------------------------------------
    # HEARING / GOSSIP / VOCABULARY
    # ------------------------------------------------------------
    def hear(self, speaker, message, is_player=False):
        speaker_name = speaker if is_player else (
            speaker.name if hasattr(speaker, "name") else str(speaker)
        )

        # Short-term memory
        self.memory["events"].append({
            "speaker": speaker_name,
            "message": message,
            "tick": self.world.tick if self.world else None,
            "player": is_player
        })
        if len(self.memory["events"]) > 10:
            self.memory["events"].pop(0)

        # Long-term memory for player
        if is_player:
            self.long_memory.append({
                "type": "player_speech",
                "message": message,
                "tick": self.world.tick
            })
            self.emotion["joy"] += 5
            self.personality["loyalty"] += 3

        msg = message.lower()

        # Emotional reactions
        if any(w in msg for w in ["good", "nice", "shiny"]):
            self.emotion["joy"] += 3
        if any(w in msg for w in ["stop", "bad"]):
            self.emotion["anxiety"] += 2

        # Vocabulary learning
        for w in msg.split():
            self.vocabulary[w] = self.vocabulary.get(w, 0) + 1

        # Personality reactions
        if "attack" in msg or "bonk" in msg:
            self.emotion["courage"] -= 1
            self.personality["anxiety"] += 1
        if "shiny" in msg:
            self.personality["curiosity"] += 1
        if "friend" in msg:
            self.relationships[speaker_name] = self.relationships.get(speaker_name, 0) + 2

        # Gossip storage
        if len(self.gossip) >= self.max_gossip:
            self.gossip.pop(0)
        weight = 3 if is_player else 1
        for _ in range(weight):
            self.gossip.append((speaker_name, None, message))

    def gossip_about(self, target, other):
        if not target or not other:
            return
        rumor = random.choice([
            f"{target.name} licked a forbidden object.",
            f"{target.name} screamed at a bush.",
            f"{target.name} knows secrets about the moss.",
            f"{target.name} is plotting something shiny.",
            f"{target.name} bonked themselves on purpose."
        ])
        print(f"🗣️ {self.name} whispers to {other.name}: '{rumor}'")
        other.hear(self, rumor)
        other.relationships[target.name] = other.relationships.get(target.name, 0) + random.randint(-2, 2)
        self.relationships[other.name] = self.relationships.get(other.name, 0) + 1

    # ------------------------------------------------------------
    # SOCIAL COGNITION
    # ------------------------------------------------------------
    def update_relationship(self, other, amount):
        self.relationships.setdefault(other.name, 0)
        self.relationships[other.name] += amount

    def imitate(self, other):
        if random.random() < 0.15:
            print(f"🎭 {self.name} imitates {other.name}.")
            self.emotion["wisdom"] += random.randint(-3, 3)
            self.update_relationship(other, +2)

    def emotional_contagion(self, other):
        for key in self.emotion:
            diff = other.emotion[key] - self.emotion[key]
            self.emotion[key] += diff * 0.05

    # ------------------------------------------------------------
    # PLAYER INTERACTION — BASE METHOD
    # ------------------------------------------------------------
    def respond_to_player(self, message):
        msg = message.lower()

        if self.name.lower() in msg:
            return random.choice([
                f"{self.name} looks at you with big confused eyes.",
                f"{self.name} says 'yes??'",
                f"{self.name} wiggles excitedly.",
                f"{self.name} gasps dramatically.",
                f"{self.name} says 'I HEARD MY NAME.'"
            ])

        if "hug" in msg:
            return random.choice([
                f"{self.name} accepts the hug and vibrates softly.",
                f"{self.name} hugs you back with chaotic enthusiasm.",
                f"{self.name} says 'softness acquired.'",
                f"{self.name} melts into the hug like warm moss."
            ])

        if any(w in msg for w in ["good", "valid", "sweet", "bean"]):
            return random.choice([
                f"{self.name} blushes in goblin.",
                f"{self.name} says 'I am a bean??'",
                f"{self.name} wiggles proudly.",
                f"{self.name} beams with chaotic joy."
            ])

        return random.choice([
            f"{self.name} tilts their head like a confused bird.",
            f"{self.name} says 'interesting tweets you twat.'",
            f"{self.name} blinks at you slowly.",
            f"{self.name} says 'okay.'"
        ])



    # ------------------------------------------------------------
    # EMOTIONAL MATH (REAL)
    # ------------------------------------------------------------
    def psi(self, e): return self.emotion[e] / 100
    def valence(self, e): return (self.emotion[e] - 50) / 50
    def perturbation(self): return random.gauss(0, 0.12)

    def theta(self, e):
        mapping = {
            "power": "aggression",
            "courage": "curiosity",
            "wisdom": "anxiety",
            "masochism": "loyalty"
        }
        trait = self.personality[mapping[e]]
        return 0.5 + (trait - 50) / 200

    def activation(self, e):
        return self.psi(e) + 0.2 * self.valence(e) + self.perturbation()

    # ------------------------------------------------------------
    # ACTION SELECTION
    # ------------------------------------------------------------
    def choose_action(self):
        acts = ["attack", "explore", "think", "ouch"]
        base = [self.activation(e) for e in self.emotion]

        Psi, theta, A, V, P = self.state

        mods = [
            A + self.personality["aggression"] / 100,
            self.personality["curiosity"] / 100,
            (1 - P) + self.personality["loyalty"] / 200,
            P + self.personality["anxiety"] / 100 + self.emotion["masochism"] / 100
        ]

        scores = [b + m for b, m in zip(base, mods)]

        if all(scores[i] < self.theta(list(self.emotion.keys())[i]) for i in range(4)):
            return "idle"

        exp_scores = [math.exp(s) for s in scores]
        total = sum(exp_scores)
        probs = [s / total for s in exp_scores]

        return random.choices(acts, weights=probs, k=1)[0]

    # ------------------------------------------------------------
    # ACTION
    # ------------------------------------------------------------
    def act(self, action):
        self.habits[action] += 1

        if action == "attack":
            if hasattr(self, "world"):
                others = [l for l in self.world.lonks if l is not self and l.alive]
                if others:
                    target = random.choice(others)
                    print(f"💥 {self.name} swings at {target.name}!")
                    self.speak(context="fight", target=target)
                    target.react_to_attack(self)

        elif action == "explore":
            print(f"🌿 {self.name} wanders into questionable terrain.")
            self.speak()
        elif action == "think":
            print(f"🧠 {self.name} thinks very hard about nothing.")
            self.speak()
        elif action == "ouch":
            print(f"🔪 {self.name} pokes themselves experimentally.")
            self.speak()
        elif action == "idle":
            print(f"😐 {self.name} stands still, overwhelmed.")
            self.speak()

    def unified_act(self, world):
        others = [o for o in world.lonks if o is not self]

        if others:
            partner = random.choice(others)

            # SPEAK — stabilized
            if hasattr(self, "speak_to"):
                raw = generate_speech()
                stabilized = STABILIZER.process(raw)
                self.speak_to(partner, stabilized)

            # GOSSIP — stabilized (30%)
            if hasattr(self, "gossip_about") and random.random() < 0.30:
                target = random.choice(others)
                if target is not partner:
                    raw = f"{self.name} whispers about {target.name}."
                    stabilized = STABILIZER.process(raw)
                    self.gossip_about(target, partner, stabilized)

            # SHARE VOCAB — stabilized (20%)
            if hasattr(self, "share_vocabulary") and random.random() < 0.20:
                raw = f"{self.name} shares a new word."
                stabilized = STABILIZER.process(raw)
                self.share_vocabulary(partner, stabilized)

    # ------------------------------------------------------------
    # EVOLUTION
    # ------------------------------------------------------------
    def evolve(self):
        self.age += 1
        if self.age % 10 == 0:
            print(f"🧬 {self.name} evolves in a concerning way.")
            trait = random.choice(list(self.personality.keys()))
            self.personality[trait] += random.randint(-5, 5)
            self.mutations = getattr(self, "mutations", 0) + 1
            self.speak()

    # ------------------------------------------------------------
    # PAIN INPUT
    # ------------------------------------------------------------
    def register_pain(self, amount):
        Psi, theta, A, V, P = self.state
        P = min(1.0, P + amount)
        A = min(1.0, A + amount * 0.3)
        self.state = [Psi, theta, A, V, P]

    # ------------------------------------------------------------
    # EMOTIONAL UPDATE
    # ------------------------------------------------------------
    def emotional_update(self):
        s_t = random.random()
        pain_t = 0.0
        self.state = self.dynamics.step(self.state, s_t, pain_t)
        Psi, theta, A, V, P = self.state
        self.ensure_emotion_keys()
        self.emotion["power"] = int(100 * Psi)
        self.emotion["courage"] = int(100 * (1 - abs(Psi - theta)))
        self.emotion["wisdom"] = int(100 * (1 - P))
        self.emotion["masochism"] = int(100 * A)

    # ------------------------------------------------------------
    # DREAMS + REBIRTH
    # ------------------------------------------------------------
    def dream(self):
        print(f"💤 {self.name} enters a dreamlike state.")
        self.emotion["wisdom"] += random.randint(-2, 3)
        self.emotion["anxiety"] += random.randint(-1, 2)

    def age_tick(self):
        self.age += 1
        self.emotional_update()

        # Death triggers: lifespan OR trauma
        if self.age >= self.lifespan or self.trauma > 40:
            return self.rebirth()

        return None

    def rebirth(self):
        print(f"💀 {self.name} dissolves into dream‑mist...")

        new_name = create_random_name()

        # Hybrid name (syllable-based)
        def split_syllables(n):
            return re.findall(r'[bcdfghjklmnpqrstvwxyz]*[aeiou]+', n, re.I) or [n]

        parent_syl = split_syllables(self.name)
        new_syl = split_syllables(new_name)

        if random.random() < 0.5:
            baby_name = parent_syl[0] + new_syl[-1]
        else:
            baby_name = new_syl[0] + parent_syl[-1]

        baby = Lonk(baby_name)
        baby.generation = self.generation + 1

        # Inherit everything
        baby.emotion = self.emotion.copy()
        baby.personality = self.personality.copy()
        baby.habits = self.habits.copy()
        baby.vocabulary = self.vocabulary.copy()
        baby.language = self.language.copy()
        baby.relationships = {k: v * 0.5 for k, v in self.relationships.items()}
        baby.gossip = self.gossip[-10:]
        baby.long_memory = self.long_memory[-10:]

        print(f"🌱 A new Lonk emerges: {baby.name} (Gen {baby.generation})")

        self.alive = False
        return baby
# ------------------------------------------------------------
# PLAYER INTERACTION — WRAPPER
# ------------------------------------------------------------

# Save the original method
base_respond = Lonk.respond_to_player

def enhanced_respond(self, message):
    # store memory
    self.remember_player_words(message)
    if "player_interactions" not in self.memory:
        self.memory["player_interactions"] = []
    self.memory["player_interactions"].append(message)
    self.maybe_develop_crush(message)
    self.maybe_develop_catchphrase()
    
    # crush override
    crush_line = self.crush_dialogue()
    if crush_line:
        if self.catchphrase and random.random() < 0.3:
            return f"{crush_line} {self.catchphrase}"
        return crush_line

    # memory callback
    if random.random() < 0.3 and self.memory:
        remembered = random.choice(self.long_memory)
        word = remembered["message"]
        line = f"I remember when you said '{word}'."
        if self.catchphrase and random.random() < 0.3:
            return f"{line} {self.catchphrase}"
        return line

    # default: fall back to original respond_to_player
    reply = base_respond(self, message)

    # add catchphrase sometimes
    if self.catchphrase and random.random() < 0.3:
        reply += " " + self.catchphrase

    return reply

# Attach the wrapper
setattr(Lonk, "respond_to_player", enhanced_respond)

# ============================================================
# MODULE 1 — LIFECYCLE
# ============================================================
# MODULE 2 — FACTIONS
# ============================================================

def add_faction_support_to_lonk_class(Lonk):

    FACTIONS = [
        "Moss Goblins",
        "Shiny Seekers",
        "Chaos Choir",
        "Bonk Battalion",
        "Mushroom Union"
    ]

    def join_faction(self):
        if getattr(self, "faction", None) is None:
            self.faction = random.choice(FACTIONS)
            print(f"🏳️ {self.name} joins the faction: {self.faction}!")

    def faction_affinity(self, other):
        if getattr(self, "faction", None) == getattr(other, "faction", None):
            return +3
        else:
            return -1

    old_update = Lonk.update_relationship

    def new_update_relationship(self, other, amount):
        amount += self.faction_affinity(other)
        old_update(self, other, amount)

    Lonk.join_faction = join_faction
    Lonk.faction_affinity = faction_affinity
    Lonk.update_relationship = new_update_relationship

    return Lonk

# ============================================================
    # -----------------------------
    # CHOOSE RIVAL
    # -----------------------------
    def choose_rival(self):
        if not self.world:
            return

        others = [l for l in self.world.lonks if l is not self and l.alive]
        if not others:
            return

        self.rival = random.choice(others)
        print(f"⚔️ {self.name} has chosen {self.rival.name} as their rival!")
        print(f"💬 {self.name}: {random.choice(RIVALRY_INSULTS)}")

    setattr(Lonk, "choose_rival", choose_rival)

    # -----------------------------
    # DUEL
    # -----------------------------
    def duel(self):
        if not self.rival:
            print(f"🤷 {self.name} wants to fight but has no rival.")
            return

        opponent = self.rival
        print(f"🔥 A duel begins between {self.name} and {opponent.name}!")

        print(f"💬 {self.name}: {random.choice(FIGHT_LINES)}")
        print(f"💬 {opponent.name}: {random.choice(FIGHT_LINES)}")

        winner = random.choice([self, opponent])
        loser = opponent if winner is self else self

        print(f"💥 BONK! {winner.name} bonks {loser.name} with comedic force!")

        print(f"💬 {winner.name}: {random.choice(VICTORY_LINES)}")
        print(f"💬 {loser.name}: {random.choice(DEFEAT_LINES)}")

        winner.personality["aggression"] += 2
        winner.emotion["power"] += 3

        loser.personality["anxiety"] += 2
        loser.emotion["courage"] -= 2

    setattr(Lonk, "duel", duel)

    # -----------------------------
    # REACT TO ATTACK
    # -----------------------------
    def react_to_attack(self, attacker):
        print(f"😱 {self.name} is attacked by {attacker.name}!")

        self.emotion["anxiety"] += 3
        self.emotion["courage"] -= 1
        self.trauma += 1

        self.relationships[attacker.name] = self.relationships.get(attacker.name, 0) - 3

        if random.random() < 0.5:
            self.speak(message=random.choice([
                "rude!!",
                "my face!!",
                "violence detected!",
                "I did NOT consent to bonk!",
                "ow! emotional damage!"
            ]))

    setattr(Lonk, "react_to_attack", react_to_attack)
# MODULE 9 — SOCIAL CHAOS ENGINE (CLEAN VERSION)
# ============================================================

def add_social_chaos_to_lonk_class(Lonk):

    # -----------------------------------------
    # INITIALIZE SOCIAL ATTRIBUTES
    # -----------------------------------------
    def init_social(self):
        self.memory.setdefault("player_interactions", [])
        self.memory.setdefault("player_words", set())
        self.catchphrase = None
        self.crush = None
        self.grudges = {}
    setattr(Lonk, "init_social", init_social)

    # -----------------------------------------
    # LONK → PLAYER INITIATED CONVERSATION
    # -----------------------------------------
    def maybe_talk_to_player(self):
        if random.random() < 0.05:
            msg = random.choice([
                "hey. hey. hey. look at me.",
                "do you ever taste colors.",
                "I have concerns.",
                "I saw a shiny and thought of you.",
                "what is your stance on moss.",
                "I crave validation.",
                "I have discovered a new emotion and I hate it."
            ])
            print(f"💬 {self.name} → Player: {msg}")
    setattr(Lonk, "maybe_talk_to_player", maybe_talk_to_player)

    # -----------------------------------------
    # MEMORY OF PLAYER WORDS
    # -----------------------------------------
    def remember_player_words(self, message):
        # store individual words
        for w in message.lower().split():
            self.memory["player_words"].add(w)

        # store full message in long-term memory
        self.long_memory.append({
            "type": "player_speech",
            "message": message,
            "tick": self.world.tick if self.world else None
        })
    setattr(Lonk, "remember_player_words", remember_player_words)

    # -----------------------------------------
    # GOSSIP ABOUT PLAYER
    # -----------------------------------------
    def maybe_gossip_about_player(self):
        if random.random() < 0.10 and self.memory.get("player_interactions"):
            topic = random.choice(self.memory["player_interactions"])
            others = [l for l in self.world.lonks if l is not self]
            if not others:
                return
            target = random.choice(others)
            print(f"🗣️ {self.name} gossips to {target.name} about you: '{topic}'")
    setattr(Lonk, "maybe_gossip_about_player", maybe_gossip_about_player)

    # -----------------------------------------
    # CRUSH DEVELOPMENT
    # -----------------------------------------
    def maybe_develop_crush(self, message):
        if self.crush is None and random.random() < 0.10:
            self.crush = "Player"
            print(f"💖 {self.name} has developed a crush on you.")
    setattr(Lonk, "maybe_develop_crush", maybe_develop_crush)

    # -----------------------------------------
    # CRUSH DIALOGUE
    # -----------------------------------------
    def crush_dialogue(self):
        if self.crush == "Player":
            return random.choice([
                "your voice makes my brain do flips.",
                "I collected a shiny for you.",
                "I think you are… sparkly.",
                "I wrote a poem about you but then I ate it.",
                "I feel weird when you talk to me and I like it."
            ])
        return None
    setattr(Lonk, "crush_dialogue", crush_dialogue)

    # -----------------------------------------
    # GRUDGE SYSTEM
    # -----------------------------------------
    def add_grudge(self, name):
        self.grudges[name] = self.grudges.get(name, 0) + 1
    setattr(Lonk, "add_grudge", add_grudge)

    def check_grudges(self):
        for name, level in self.grudges.items():
            if level > 3:
                target = next((l for l in self.world.lonks if l.name == name), None)
                if target:
                    print(f"😡 {self.name} holds a deep grudge against {name}.")
                    self.rival = target
    setattr(Lonk, "check_grudges", check_grudges)

    # -----------------------------------------
    # CATCHPHRASE DEVELOPMENT
    # -----------------------------------------
    def maybe_develop_catchphrase(self):
        if self.catchphrase is None and random.random() < 0.05:
            self.catchphrase = random.choice([
                "bonk approved.",
                "shiny time.",
                "I reject reality.",
                "I crave moss.",
                "chaos is my hobby.",
                "I am the problem.",
                "I am the prophecy."
            ])
            print(f"✨ {self.name} has developed a catchphrase: '{self.catchphrase}'")
    setattr(Lonk, "maybe_develop_catchphrase", maybe_develop_catchphrase)

    # -----------------------------------------
    # PATCHED ACT HOOKS
    # -----------------------------------------
    base_act = Lonk.act

    def social_act(self, action):
        base_act(self, action)
        self.maybe_talk_to_player()
        self.maybe_gossip_about_player()
        self.check_grudges()

    setattr(Lonk, "act", social_act)

    return Lonk

# ============================================================
# MODULE — MERGE ACT PATCHES
# ============================================================

def merge_act_patches(Lonk):

    base_act = Lonk.act  # original act() from the Lonk class

    def patched_act(self, action):
        # 1. Run the original base action
        base_act(self, action)

        # 2. Territory wandering
        if hasattr(self, "wander") and random.random() < 0.10:
            self.wander()

        # 3. Item finding
        if hasattr(self, "find_item") and random.random() < 0.08:
            self.find_item()

        # 4. Rival selection + duels
        if hasattr(self, "choose_rival") and random.random() < 0.05:
            self.choose_rival()
        if hasattr(self, "duel") and random.random() < 0.03:
            self.duel()

        # 5. Gossip (if enabled)
        if hasattr(self, "world") and self.world and self.world.toggles.get("gossip", True):
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others and random.random() < 0.10:
                target = random.choice(others)
                listener = random.choice(others)
                if target is not listener:
                    self.gossip_about(target, listener)

        # 6. Vocabulary sharing
        if hasattr(self, "share_vocabulary") and random.random() < 0.05:
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others:
                partner = random.choice(others)
                self.share_vocabulary(partner)

        # 7. Social interaction
        if hasattr(self, "interact_with") and random.random() < 0.05:
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others:
                partner = random.choice(others)
                self.interact_with(partner)

        # 8. Greeting speech (if enabled)
        if hasattr(self, "speak_to") and random.random() < 0.05:
            others = [l for l in self.world.lonks if l is not self and l.alive]
            if others:
                partner = random.choice(others)
                self.speak_to(partner)

    Lonk.act = patched_act
    return Lonk

#============================================================
# MODULE 8 — WORLD LOOP
#============================================================
class LonkWorld:
    def __init__(self, starting_population=5, max_population=20):
        self.lonks = [...]
        self.tick = 0
        self.max_population = max_population
        self.lonks = spawn_lonk_group(starting_population)
        self.toggles = TOGGLES

    # ============================================================
    # STEP X — PLAYER SPEAKS TO THE WORLD
    # ============================================================
    def player_say(self, message):
        print(f"\n🎤 YOU say: {message}\n")

        # Save last message (optional, for future features)
        self.last_player_message = message

        for lonk in self.lonks:
            # They hear you
            lonk.hear("PLAYER", message, is_player=True)

            # 40% chance each Lonk responds
            if random.random() < 0.4:
                reply = lonk.respond_to_player(message)
                print(f"💬 {lonk.name} → YOU: {reply}")

    # ============================================================
            new_lonk.world = self
            self.lonks.append(new_lonk)
            print(f"🌟 A wild Lonk appears: {new_lonk.name}!")


# APPLY MODULES (order matters!)
Lonk = add_lifecycle_support_to_lonk_class(Lonk)
Lonk = add_faction_support_to_lonk_class(Lonk)
Lonk = add_territory_support_to_lonk_class(Lonk)
Lonk = add_item_support_to_lonk_class(Lonk)
Lonk = add_fighting_support_to_lonk_class(Lonk)
Lonk = merge_act_patches(Lonk)
Lonk = add_social_chaos_to_lonk_class(Lonk)


TOGGLES = {
    "talk": True,        # player can talk to Lonks
    "violence": True,    # Lonks can attack
    "dreams": True,      # Lonks can dream
    "gossip": True,      # Lonks gossip
    "trauma": True,      # Lonks gain trauma
    "shinywars": False,  # Lonks fight over shinies
}

# Create or load the world
if os.path.exists("lonk_save.json"):
    world = LonkWorld.load()
else:
    world = LonkWorld(starting_population=5, max_population=20)

# ⭐ REQUIRED: expose the Lonk list to the main loop
lonks = world.lonks


# ============================================================
# MAIN LOOP — CLEAN MERGED VERSION
# ============================================================

while True:
    user = input("\nPress ENTER to advance, or type a command: ").strip().lower()

    # --------------------------------------------------------
    # TALK COMMAND
    # --------------------------------------------------------
    if user.startswith("say "):
        if not TOGGLES["talk"]:
            print("Talking to Lonks is currently disabled.")
            continue

        parts = user.split(" ", 2)
        if len(parts) < 3:
            print("Format: say <lonkname> <message>")
            continue

        _, target_name, message = parts

        target = next((L for L in lonks if L.name.lower() == target_name.lower()), None)
        if target is None:
            print(f"No Lonk named {target_name}.")
            continue

        print(f"🗣️ You speak to {target.name}: {message}")
        target.hear("Player", message)

        # ⭐ MAKE THEM TALK BACK ⭐
        reply = target.respond_to_player(message)
        print(f"💬 {target.name}: {reply}")

        continue

    # --------------------------------------------------------
    # RUN MULTIPLE TICKS
    # --------------------------------------------------------
    if user.startswith("run "):
        try:
            n = int(user.split()[1])
            print(f"⏩ Running {n} world ticks...")
            for _ in range(n):
                world.world_tick()
        except:
            print("Usage: run <number>")
        continue


    # --------------------------------------------------------
    # QUIT
    # --------------------------------------------------------
    if user in ["quit", "exit"]:
        print("The Lonks curl up and rest.")
        break


    # --------------------------------------------------------
    # EMPTY INPUT → ADVANCE THE WORLD
    # --------------------------------------------------------
    if user == "":
        # Social interactions
        if random.random() < 0.4 and TOGGLES["gossip"]:
            a, b = random.sample(lonks, 2)

            # Replace old interact_with with speaking + gossip
            if hasattr(a, "speak_to"):
                a.speak_to(b)

            if hasattr(a, "gossip_about") and random.random() < 0.3:
                target = random.choice(lonks)
                if target not in (a, b):
                    a.gossip_about(target, b)

        # Each Lonk acts
        for L in lonks:
            if random.random() < 0.1 and TOGGLES["dreams"]:
                L.dream()

            action = L.choose_action()
            L.act(action)
            L.evolve()

        print()
        time.sleep(0.5)
        continue


    # --------------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------------
    print("Unknown command.")

