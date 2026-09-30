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

# First rich-present resolution.
N_BINS = 10


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


def rich_state(energy, damage, alive=True):
    if not alive or energy <= 0.0 or damage >= 1.0:
        return ("D",)

    e_bin = min(
        N_BINS - 1,
        int(energy * N_BINS),
    )

    # Damage can technically exceed 1 only at death,
    # already handled above.
    d = max(0.0, min(0.999999999, damage))

    d_bin = min(
        N_BINS - 1,
        int(d * N_BINS),
    )

    return ("A", e_bin, d_bin)


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


def trajectory(seed):
    env = make_environment(seed)

    energy = INITIAL_ENERGY
    damage = INITIAL_DAMAGE
    alive = True

    rows = [
        (
            classify(energy, damage, alive),
            rich_state(energy, damage, alive),
        )
    ]

    for resource, shock in env:
        energy, damage, alive = metabolic_step(
            energy,
            damage,
            resource,
            shock,
        )

        rows.append(
            (
                classify(energy, damage, alive),
                rich_state(energy, damage, alive),
            )
        )

        if not alive:
            remaining = TICKS - len(rows) + 1

            if remaining > 0:
                rows.extend(
                    [
                        ("D", ("D",))
                    ] * remaining
                )

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

print("=" * 76)
print("LONK STATE-ALIASING TEST")
print("=" * 76)
print(f"Gain          : {GAIN}")
print(f"Train trials  : {TRAIN_TRIALS}")
print(f"Test trials   : {TEST_TRIALS}")
print(f"Rich bins     : {N_BINS} x {N_BINS}")
print()

# ---------------------------------------------------------
# MODEL A — COARSE PRESENT
# P(next coarse | current coarse)
# ---------------------------------------------------------

coarse_counts = Counter()
coarse_context = Counter()

# ---------------------------------------------------------
# MODEL B — COARSE HISTORY
# P(next coarse | previous coarse, current coarse)
# ---------------------------------------------------------

history_counts = Counter()
history_context = Counter()

# ---------------------------------------------------------
# MODEL C — RICH PRESENT
# P(next coarse | current energy/damage bin)
# ---------------------------------------------------------

rich_counts = Counter()
rich_context = Counter()


for rows in train:
    for i in range(1, len(rows) - 1):
        previous_coarse = rows[i-1][0]
        current_coarse = rows[i][0]
        current_rich = rows[i][1]
        next_coarse = rows[i+1][0]

        coarse_counts[
            (current_coarse, next_coarse)
        ] += 1
        coarse_context[current_coarse] += 1

        history_counts[
            (
                previous_coarse,
                current_coarse,
                next_coarse,
            )
        ] += 1

        history_context[
            (
                previous_coarse,
                current_coarse,
            )
        ] += 1

        rich_counts[
            (
                current_rich,
                next_coarse,
            )
        ] += 1

        rich_context[current_rich] += 1


def p_coarse(current, nxt):
    return (
        coarse_counts[(current, nxt)] + ALPHA
    ) / (
        coarse_context[current]
        + ALPHA * len(STATES)
    )


def p_history(previous, current, nxt):
    ctx = (previous, current)

    return (
        history_counts[
            (previous, current, nxt)
        ] + ALPHA
    ) / (
        history_context[ctx]
        + ALPHA * len(STATES)
    )


def p_rich(current_rich, nxt):
    return (
        rich_counts[
            (current_rich, nxt)
        ] + ALPHA
    ) / (
        rich_context[current_rich]
        + ALPHA * len(STATES)
    )


# ---------------------------------------------------------
# HELD-OUT TEST
# ---------------------------------------------------------

trajectory_scores = []

total_coarse = 0.0
total_history = 0.0
total_rich = 0.0
total_n = 0

for rows in test:
    loss_coarse = 0.0
    loss_history = 0.0
    loss_rich = 0.0
    n = 0

    for i in range(1, len(rows) - 1):
        previous_coarse = rows[i-1][0]
        current_coarse = rows[i][0]
        current_rich = rows[i][1]
        next_coarse = rows[i+1][0]

        pc = p_coarse(
            current_coarse,
            next_coarse,
        )

        ph = p_history(
            previous_coarse,
            current_coarse,
            next_coarse,
        )

        pr = p_rich(
            current_rich,
            next_coarse,
        )

        loss_coarse -= math.log(pc)
        loss_history -= math.log(ph)
        loss_rich -= math.log(pr)

        n += 1

    if n:
        mc = loss_coarse / n
        mh = loss_history / n
        mr = loss_rich / n

        trajectory_scores.append(
            {
                "coarse": mc,
                "history": mh,
                "rich": mr,
                "history_gain": mc - mh,
                "rich_gain": mc - mr,
                "rich_vs_history": mh - mr,
            }
        )

        total_coarse += loss_coarse
        total_history += loss_history
        total_rich += loss_rich
        total_n += n


LC = total_coarse / total_n
LH = total_history / total_n
LR = total_rich / total_n


def mean_ci(values):
    mean = sum(values) / len(values)

    variance = sum(
        (x - mean) ** 2
        for x in values
    ) / (len(values) - 1)

    se = math.sqrt(variance) / math.sqrt(
        len(values)
    )

    ci = 1.96 * se

    return mean, mean - ci, mean + ci


history_diffs = [
    r["history_gain"]
    for r in trajectory_scores
]

rich_diffs = [
    r["rich_gain"]
    for r in trajectory_scores
]

rich_vs_history = [
    r["rich_vs_history"]
    for r in trajectory_scores
]

H_MEAN, H_LO, H_HI = mean_ci(history_diffs)
R_MEAN, R_LO, R_HI = mean_ci(rich_diffs)
RH_MEAN, RH_LO, RH_HI = mean_ci(rich_vs_history)


print("=" * 76)
print("HELD-OUT MODEL COMPARISON")
print("=" * 76)

print(f"Predictions : {total_n:,}")
print()

print(
    f"COARSE PRESENT log loss : "
    f"{LC:.9f}"
)

print(
    f"COARSE HISTORY log loss : "
    f"{LH:.9f}"
)

print(
    f"RICH PRESENT log loss   : "
    f"{LR:.9f}"
)

print()

print(
    f"COARSE perplexity : "
    f"{math.exp(LC):.9f}"
)

print(
    f"HISTORY perplexity: "
    f"{math.exp(LH):.9f}"
)

print(
    f"RICH perplexity   : "
    f"{math.exp(LR):.9f}"
)


print()
print("=" * 76)
print("IMPROVEMENT OVER COARSE PRESENT")
print("=" * 76)

print(
    f"History gain: {H_MEAN:+.9f} "
    f"95%CI=[{H_LO:+.9f}, {H_HI:+.9f}]"
)

print(
    f"Rich gain:    {R_MEAN:+.9f} "
    f"95%CI=[{R_LO:+.9f}, {R_HI:+.9f}]"
)


print()
print("=" * 76)
print("RICH PRESENT VS HISTORY")
print("=" * 76)

print(
    "history_loss - rich_loss = "
    f"{RH_MEAN:+.9f}"
)

print(
    f"95%CI=[{RH_LO:+.9f}, "
    f"{RH_HI:+.9f}]"
)

rich_wins = sum(
    r["rich"] < r["history"]
    for r in trajectory_scores
)

history_wins = sum(
    r["history"] < r["rich"]
    for r in trajectory_scores
)

ties = len(trajectory_scores) - (
    rich_wins + history_wins
)

print()
print(
    f"Rich-present wins : "
    f"{rich_wins}/{len(trajectory_scores)}"
)

print(
    f"History wins      : "
    f"{history_wins}/{len(trajectory_scores)}"
)

print(
    f"Ties              : "
    f"{ties}/{len(trajectory_scores)}"
)


print()
print("=" * 76)
print("RICH-STATE COVERAGE")
print("=" * 76)

print(
    f"Observed rich contexts in training: "
    f"{len(rich_context)}"
)

test_contexts = set()

for rows in test:
    for i in range(1, len(rows) - 1):
        test_contexts.add(rows[i][1])

unseen = [
    ctx
    for ctx in test_contexts
    if ctx not in rich_context
]

print(
    f"Observed rich contexts in test:     "
    f"{len(test_contexts)}"
)

print(
    f"Unseen test contexts:               "
    f"{len(unseen)}"
)


print()
print("=" * 76)
print("INTERPRETATION")
print("=" * 76)

if RH_MEAN > 0 and RH_LO > 0:
    print(
        "RICH PRESENT OUTPREDICTS "
        "COARSE HISTORY."
    )
    print(
        "State aliasing explains at least "
        "part of the apparent history effect."
    )

elif RH_MEAN < 0 and RH_HI < 0:
    print(
        "COARSE HISTORY STILL OUTPREDICTS "
        "THIS RICH-PRESENT REPRESENTATION."
    )
    print(
        "Increase present-state resolution "
        "before interpreting this as memory."
    )

else:
    print(
        "RICH PRESENT AND COARSE HISTORY "
        "ARE NOT CLEARLY SEPARATED."
    )

print()
print(
    "This test does not establish intrinsic memory."
)
