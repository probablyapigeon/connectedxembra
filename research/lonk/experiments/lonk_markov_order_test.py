import random
import math
from collections import Counter, defaultdict

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

# Laplace/Dirichlet smoothing prevents zero-probability
# events from producing infinite held-out log loss.
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
        repaired = min(REPAIR_RATE, damage)

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

    states = [
        classify(energy, damage, alive)
    ]

    for resource, shock in env:
        energy, damage, alive = metabolic_step(
            energy,
            damage,
            resource,
            shock,
        )

        state = classify(
            energy,
            damage,
            alive,
        )

        states.append(state)

        if not alive:
            remaining = TICKS - len(states) + 1

            if remaining > 0:
                states.extend(
                    ["D"] * remaining
                )

            break

    return states


# Completely disjoint seeds.
train = [
    trajectory(SEED + i)
    for i in range(TRAIN_TRIALS)
]

test = [
    trajectory(SEED + 1_000_000 + i)
    for i in range(TEST_TRIALS)
]

print("=" * 76)
print("LONK MARKOV ORDER TEST")
print("=" * 76)
print(f"Gain          : {GAIN}")
print(f"Train trials  : {TRAIN_TRIALS}")
print(f"Test trials   : {TEST_TRIALS}")
print(f"Ticks/trial   : {TICKS}")
print(f"Smoothing     : {ALPHA}")
print()

# ---------------------------------------------------------
# TRAIN FIRST-ORDER MODEL
# P(next | current)
# ---------------------------------------------------------

first_counts = Counter()
first_context = Counter()

for states in train:
    for current, nxt in zip(
        states[:-1],
        states[1:],
    ):
        first_counts[(current, nxt)] += 1
        first_context[current] += 1


def p_first(current, nxt):
    numerator = (
        first_counts[(current, nxt)]
        + ALPHA
    )

    denominator = (
        first_context[current]
        + ALPHA * len(STATES)
    )

    return numerator / denominator


# ---------------------------------------------------------
# TRAIN SECOND-ORDER MODEL
# P(next | previous, current)
# ---------------------------------------------------------

second_counts = Counter()
second_context = Counter()

for states in train:
    for previous, current, nxt in zip(
        states[:-2],
        states[1:-1],
        states[2:],
    ):
        context = (previous, current)

        second_counts[
            (previous, current, nxt)
        ] += 1

        second_context[context] += 1


def p_second(previous, current, nxt):
    context = (previous, current)

    numerator = (
        second_counts[
            (previous, current, nxt)
        ]
        + ALPHA
    )

    denominator = (
        second_context[context]
        + ALPHA * len(STATES)
    )

    return numerator / denominator


# ---------------------------------------------------------
# HELD-OUT SCORING
# ---------------------------------------------------------

trajectory_results = []

total_loss_1 = 0.0
total_loss_2 = 0.0
total_predictions = 0

for states in test:
    loss_1 = 0.0
    loss_2 = 0.0
    n = 0

    # Start at t=1 so both models predict
    # exactly the same target positions.
    for previous, current, nxt in zip(
        states[:-2],
        states[1:-1],
        states[2:],
    ):
        q1 = p_first(current, nxt)
        q2 = p_second(
            previous,
            current,
            nxt,
        )

        loss_1 -= math.log(q1)
        loss_2 -= math.log(q2)

        n += 1

    if n:
        mean_1 = loss_1 / n
        mean_2 = loss_2 / n

        trajectory_results.append(
            (mean_1, mean_2, mean_1 - mean_2)
        )

        total_loss_1 += loss_1
        total_loss_2 += loss_2
        total_predictions += n


pooled_1 = total_loss_1 / total_predictions
pooled_2 = total_loss_2 / total_predictions

delta = pooled_1 - pooled_2

pp1 = math.exp(pooled_1)
pp2 = math.exp(pooled_2)


# ---------------------------------------------------------
# TRAJECTORY-LEVEL UNCERTAINTY
# ---------------------------------------------------------

diffs = [
    row[2]
    for row in trajectory_results
]

mean_diff = sum(diffs) / len(diffs)

variance = sum(
    (x - mean_diff) ** 2
    for x in diffs
) / (len(diffs) - 1)

sd = math.sqrt(variance)
se = sd / math.sqrt(len(diffs))
ci = 1.96 * se

second_wins = sum(
    d > 0
    for d in diffs
)

first_wins = sum(
    d < 0
    for d in diffs
)

ties = sum(
    d == 0
    for d in diffs
)


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

print("=" * 76)
print("HELD-OUT PREDICTIVE RESULTS")
print("=" * 76)

print(
    f"Predictions scored : "
    f"{total_predictions:,}"
)

print()
print(
    f"First-order log loss  : "
    f"{pooled_1:.9f}"
)

print(
    f"Second-order log loss : "
    f"{pooled_2:.9f}"
)

print(
    f"Improvement L1-L2     : "
    f"{delta:+.9f}"
)

print()
print(
    f"First-order perplexity  : "
    f"{pp1:.9f}"
)

print(
    f"Second-order perplexity : "
    f"{pp2:.9f}"
)

print()
print(
    "Trajectory mean improvement: "
    f"{mean_diff:+.9f}"
)

print(
    "95% CI: "
    f"[{mean_diff-ci:+.9f}, "
    f"{mean_diff+ci:+.9f}]"
)

print()
print(
    f"Second-order wins : "
    f"{second_wins}/{len(diffs)}"
)

print(
    f"First-order wins  : "
    f"{first_wins}/{len(diffs)}"
)

print(
    f"Ties              : "
    f"{ties}/{len(diffs)}"
)


# ---------------------------------------------------------
# CONTEXT INSPECTION
# ---------------------------------------------------------

print()
print("=" * 76)
print("SECOND-ORDER CONTEXTS")
print("=" * 76)

for previous in STATES:
    for current in STATES:

        n = second_context[
            (previous, current)
        ]

        if n == 0:
            continue

        probs = [
            p_second(
                previous,
                current,
                nxt,
            )
            for nxt in STATES
        ]

        print(
            f"{previous}->{current} "
            f"n={n:9d}  "
            + " ".join(
                f"{state}:{prob:.4f}"
                for state, prob
                in zip(STATES, probs)
            )
        )


print()
print("=" * 76)
print("VERDICT RULE")
print("=" * 76)

if delta > 0 and mean_diff - ci > 0:
    print(
        "SECOND ORDER HAS HELD-OUT "
        "PREDICTIVE ADVANTAGE."
    )
    print(
        "The four-state representation fails "
        "this first-order sufficiency test."
    )

elif delta < 0 and mean_diff + ci < 0:
    print(
        "FIRST ORDER PREDICTS BETTER "
        "ON HELD-OUT TRAJECTORIES."
    )

else:
    print(
        "NO CLEAR HELD-OUT ORDER ADVANTAGE."
    )

print()
print(
    "A second-order advantage does NOT by itself "
    "establish memory."
)

print(
    "It may arise because coarse H/S/C/D states "
    "discard relevant present-state information."
)
