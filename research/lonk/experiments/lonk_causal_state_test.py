import random
import math
from collections import Counter

SEED = 260930
TRAIN_TRIALS = 3000
TEST_TRIALS = 1000
TICKS = 1000

GAIN = 0.0510
MAINTENANCE = 0.010

INITIAL_ENERGY = 0.65
INITIAL_DAMAGE = 0.05

REPAIR_COST = 0.012
REPAIR_RATE = 0.025
DAMAGE_RATE = 0.010

STATES = ("H", "S", "C", "D")
ALPHA = 1.0


def clamp(x):
    return max(0.0, min(1.0, x))


def classify(energy, damage, alive=True):
    if not alive or energy <= 0.0 or damage >= 1.0:
        return "D"

    if energy >= 0.55 and damage < 0.35:
        return "H"

    if energy >= 0.25 and damage < 0.70:
        return "S"

    return "C"


def make_environment(seed):
    rng = random.Random(seed)
    env = []

    for _ in range(TICKS):
        resource = rng.random()

        shock = (
            rng.uniform(0.02, 0.08)
            if rng.random() < 0.04
            else 0.0
        )

        env.append((resource, shock))

    return env


def metabolic_step(
    energy,
    damage,
    resource,
    shock,
):
    energy -= MAINTENANCE

    if energy < 0.30:
        effort = 1.0
    elif energy < 0.55:
        effort = 0.65
    else:
        effort = 0.30

    energy -= 0.010 * effort
    energy += GAIN * resource * effort

    damage += shock + DAMAGE_RATE

    if damage > 0 and energy > 0.20:
        repaired = min(
            REPAIR_RATE,
            damage,
        )

        repair_energy = (
            REPAIR_COST
            * (repaired / REPAIR_RATE)
        )

        if energy >= repair_energy:
            energy -= repair_energy
            damage -= repaired

    energy = clamp(energy)
    damage = max(0.0, damage)

    alive = (
        energy > 0.0
        and damage < 1.0
    )

    return energy, damage, alive


def bin01(x, bins):
    x = max(0.0, min(0.999999999, x))
    return min(
        bins - 1,
        int(x * bins),
    )


def signed_bin(x, width=0.025, limit=8):
    # Quantize changes while retaining direction.
    q = int(round(x / width))
    return max(-limit, min(limit, q))


def trajectory(seed):
    env = make_environment(seed)

    energy = INITIAL_ENERGY
    damage = INITIAL_DAMAGE
    alive = True

    previous_energy = energy
    previous_damage = damage
    previous_coarse = classify(
        energy,
        damage,
        alive,
    )

    rows = []

    for resource, shock in env:
        current_coarse = classify(
            energy,
            damage,
            alive,
        )

        delta_energy = (
            energy - previous_energy
        )

        delta_damage = (
            damage - previous_damage
        )

        # Save the PRESENT plus the environmental
        # input that will generate the next state.
        present = {
            "coarse": current_coarse,
            "previous_coarse": previous_coarse,
            "energy": energy,
            "damage": damage,
            "dE": delta_energy,
            "dD": delta_damage,
            "resource": resource,
            "shock": shock,
        }

        new_energy, new_damage, new_alive = (
            metabolic_step(
                energy,
                damage,
                resource,
                shock,
            )
        )

        next_coarse = classify(
            new_energy,
            new_damage,
            new_alive,
        )

        present["next"] = next_coarse
        rows.append(present)

        previous_energy = energy
        previous_damage = damage
        previous_coarse = current_coarse

        energy = new_energy
        damage = new_damage
        alive = new_alive

        if not alive:
            break

    return rows


train = [
    trajectory(SEED + i)
    for i in range(TRAIN_TRIALS)
]

test = [
    trajectory(SEED + 1_000_000 + i)
    for i in range(TEST_TRIALS)
]

print("=" * 78)
print("LONK CAUSAL-STATE SUFFICIENCY TEST")
print("=" * 78)
print(f"Gain         : {GAIN}")
print(f"Train worlds : {TRAIN_TRIALS}")
print(f"Test worlds  : {TEST_TRIALS}")
print()

# ---------------------------------------------------------
# REPRESENTATIONS
# ---------------------------------------------------------

def history_key(row):
    return (
        row["previous_coarse"],
        row["coarse"],
    )


def present20_key(row):
    return (
        bin01(row["energy"], 20),
        bin01(row["damage"], 20),
    )


def trend_key(row):
    return (
        bin01(row["energy"], 20),
        bin01(row["damage"], 20),
        signed_bin(row["dE"]),
        signed_bin(row["dD"]),
    )


def causal_key(row):
    # Present metabolic state + incoming environment.
    #
    # Resource: 10 bins.
    # Shock: distinguish no shock from positive shocks,
    # then quantize positive magnitude.
    if row["shock"] <= 0.0:
        shock_bin = 0
    else:
        shock_bin = 1 + min(
            4,
            int(row["shock"] / 0.02),
        )

    return (
        bin01(row["energy"], 20),
        bin01(row["damage"], 20),
        bin01(row["resource"], 10),
        shock_bin,
    )


MODELS = {
    "HISTORY": history_key,
    "PRESENT20": present20_key,
    "TREND": trend_key,
    "CAUSAL": causal_key,
}


# ---------------------------------------------------------
# TRAIN GENERIC CONDITIONAL MODELS
# ---------------------------------------------------------

counts = {
    name: Counter()
    for name in MODELS
}

contexts = {
    name: Counter()
    for name in MODELS
}

for rows in train:
    for row in rows:
        target = row["next"]

        for name, key_fn in MODELS.items():
            key = key_fn(row)

            counts[name][
                (key, target)
            ] += 1

            contexts[name][key] += 1


def probability(model_name, key, target):
    return (
        counts[model_name][(key, target)]
        + ALPHA
    ) / (
        contexts[model_name][key]
        + ALPHA * len(STATES)
    )


# ---------------------------------------------------------
# HELD-OUT SCORING
# ---------------------------------------------------------

trajectory_losses = {
    name: []
    for name in MODELS
}

pooled_loss = {
    name: 0.0
    for name in MODELS
}

pooled_n = 0

test_context_sets = {
    name: set()
    for name in MODELS
}

for rows in test:
    local = {
        name: 0.0
        for name in MODELS
    }

    n = 0

    for row in rows:
        target = row["next"]

        for name, key_fn in MODELS.items():
            key = key_fn(row)
            test_context_sets[name].add(key)

            p = probability(
                name,
                key,
                target,
            )

            local[name] -= math.log(p)

        n += 1

    if n:
        for name in MODELS:
            mean_loss = local[name] / n

            trajectory_losses[name].append(
                mean_loss
            )

            pooled_loss[name] += local[name]

        pooled_n += n


for name in MODELS:
    pooled_loss[name] /= pooled_n


def paired_ci(a, b):
    # Positive means model B has LOWER loss
    # than model A.
    diffs = [
        x - y
        for x, y in zip(a, b)
    ]

    mean = sum(diffs) / len(diffs)

    variance = sum(
        (d - mean) ** 2
        for d in diffs
    ) / (len(diffs) - 1)

    se = math.sqrt(variance) / math.sqrt(
        len(diffs)
    )

    ci = 1.96 * se

    return (
        mean,
        mean - ci,
        mean + ci,
    )


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

print("=" * 78)
print("HELD-OUT REPRESENTATION COMPARISON")
print("=" * 78)

print(
    f"Predictions scored: {pooled_n:,}"
)

print()

for name in MODELS:
    loss = pooled_loss[name]

    print(
        f"{name:10} "
        f"log_loss={loss:.9f}  "
        f"perplexity={math.exp(loss):.9f}"
    )


print()
print("=" * 78)
print("PAIRWISE AGAINST HISTORY")
print("=" * 78)

for challenger in (
    "PRESENT20",
    "TREND",
    "CAUSAL",
):
    mean, lo, hi = paired_ci(
        trajectory_losses["HISTORY"],
        trajectory_losses[challenger],
    )

    challenger_wins = sum(
        b < a
        for a, b in zip(
            trajectory_losses["HISTORY"],
            trajectory_losses[challenger],
        )
    )

    history_wins = sum(
        a < b
        for a, b in zip(
            trajectory_losses["HISTORY"],
            trajectory_losses[challenger],
        )
    )

    print()
    print(
        f"HISTORY loss - {challenger} loss"
    )

    print(
        f"  mean={mean:+.9f}"
    )

    print(
        f"  95%CI=[{lo:+.9f}, {hi:+.9f}]"
    )

    print(
        f"  {challenger} wins="
        f"{challenger_wins}/{len(trajectory_losses['HISTORY'])}"
    )

    print(
        f"  HISTORY wins="
        f"{history_wins}/{len(trajectory_losses['HISTORY'])}"
    )


print()
print("=" * 78)
print("CONTEXT COVERAGE")
print("=" * 78)

for name in MODELS:
    train_contexts = set(
        contexts[name].keys()
    )

    test_contexts = test_context_sets[name]

    unseen = (
        test_contexts - train_contexts
    )

    print(
        f"{name:10} "
        f"train={len(train_contexts):5d} "
        f"test={len(test_contexts):5d} "
        f"unseen={len(unseen):4d}"
    )


print()
print("=" * 78)
print("INTERPRETATION GUARDRAIL")
print("=" * 78)

best = min(
    MODELS,
    key=lambda name: pooled_loss[name],
)

print(
    f"Best held-out representation: {best}"
)

print()

if best == "CAUSAL":
    print(
        "Present state + current environment "
        "outpredicts coarse history."
    )
    print(
        "This supports partial observability / "
        "state aliasing as an explanation."
    )

elif best == "TREND":
    print(
        "Present state + local direction of motion "
        "outpredicts coarse history."
    )
    print(
        "History may have been acting as a proxy "
        "for trajectory direction."
    )

elif best == "HISTORY":
    print(
        "Coarse history still predicts best."
    )
    print(
        "Do NOT call this intrinsic memory yet."
    )
    print(
        "Quantization and model sparsity remain "
        "alternative explanations."
    )

else:
    print(
        "Fine present state predicts best without "
        "explicit history."
    )

print()
print(
    "All conclusions apply only to this simulated "
    "metabolic model."
)
