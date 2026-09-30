import random
import math
from collections import Counter

SEED = 260930
TRIALS = 2000
TICKS = 1000

MAINTENANCE = 0.010

REGIMES = {
    "SUBCRITICAL": 0.0500,
    "BOUNDARY":    0.0510,
    "SUPERCRITICAL": 0.0530,
}

INITIAL_ENERGY = 0.65
INITIAL_DAMAGE = 0.05

REPAIR_COST = 0.012
REPAIR_RATE = 0.025
DAMAGE_RATE = 0.010

STATES = ("H", "S", "C", "D")


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
    gain,
):
    energy -= MAINTENANCE

    if energy < 0.30:
        effort = 1.0
    elif energy < 0.55:
        effort = 0.65
    else:
        effort = 0.30

    energy -= 0.010 * effort
    energy += gain * resource * effort

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


def run_trajectory(environment, gain):
    energy = INITIAL_ENERGY
    damage = INITIAL_DAMAGE
    alive = True

    states = [
        classify(energy, damage, alive)
    ]

    continuous = [
        (energy, damage)
    ]

    for resource, shock in environment:
        energy, damage, alive = metabolic_step(
            energy,
            damage,
            resource,
            shock,
            gain,
        )

        state = classify(
            energy,
            damage,
            alive,
        )

        states.append(state)
        continuous.append((energy, damage))

        if not alive:
            # Dead is absorbing for the remainder.
            remaining = TICKS - len(states) + 1

            if remaining > 0:
                states.extend(["D"] * remaining)
                continuous.extend(
                    [(energy, damage)] * remaining
                )

            break

    return states, continuous


def transition_counts(states):
    counts = Counter()

    for a, b in zip(states[:-1], states[1:]):
        counts[(a, b)] += 1

    return counts


def transition_matrix(counts):
    matrix = {}

    for source in STATES:
        total = sum(
            counts[(source, target)]
            for target in STATES
        )

        for target in STATES:
            matrix[(source, target)] = (
                counts[(source, target)] / total
                if total > 0
                else float("nan")
            )

    return matrix

# Same worlds for every metabolic regime.
environments = [
    make_environment(SEED + i)
    for i in range(TRIALS)
]

results = {}

for regime, gain in REGIMES.items():
    total_counts = Counter()
    occupancy = Counter()
    survival_count = 0

    for env in environments:
        states, continuous = run_trajectory(
            env,
            gain,
        )

        total_counts.update(
            transition_counts(states)
        )

        occupancy.update(states)

        if states[-1] != "D":
            survival_count += 1

    matrix = transition_matrix(total_counts)

    results[regime] = {
        "gain": gain,
        "counts": total_counts,
        "matrix": matrix,
        "occupancy": occupancy,
        "survival": survival_count / TRIALS,
    }


def fmt(x):
    if not math.isfinite(x):
        return "   nan"
    return f"{x:7.4f}"


print("=" * 78)
print("MARKOV LONK — EMPIRICAL METABOLIC TRANSITION MATRICES")
print("=" * 78)
print(f"Trials/regime : {TRIALS}")
print(f"Ticks/trial   : {TICKS}")
print(f"Maintenance   : {MAINTENANCE}")
print()

for regime, result in results.items():
    matrix = result["matrix"]
    occupancy = result["occupancy"]

    print()
    print("=" * 78)
    print(
        f"{regime}  "
        f"gain={result['gain']:.4f}  "
        f"survival={result['survival']:.3f}"
    )
    print("=" * 78)

    print()
    print("TRANSITION MATRIX")
    print("          TO")
    print("FROM        H       S       C       D")

    for source in STATES:
        values = [
            fmt(matrix[(source, target)])
            for target in STATES
        ]

        print(
            f"{source:>4}  "
            + " ".join(values)
        )

    print()
    print("STATE OCCUPANCY")

    total_occ = sum(occupancy.values())

    for state in STATES:
        fraction = (
            occupancy[state] / total_occ
            if total_occ else float("nan")
        )

        print(
            f"  {state}: "
            f"{occupancy[state]:10d} "
            f"({fraction:.4f})"
        )

    print()
    print("KEY FLOWS")

    stressed_recovery = matrix[("S", "H")]

    critical_escape = (
        matrix[("C", "H")]
        + matrix[("C", "S")]
    )

    critical_death = matrix[("C", "D")]

    print(
        f"  S -> H recovery       = "
        f"{stressed_recovery:.6f}"
    )

    print(
        f"  C -> H/S escape       = "
        f"{critical_escape:.6f}"
    )

    print(
        f"  C -> D failure        = "
        f"{critical_death:.6f}"
    )

    print(
        f"  D -> D absorbing      = "
        f"{matrix[('D','D')]:.6f}"
    )


print()
print("=" * 78)
print("CROSS-REGIME KEY-FLOW COMPARISON")
print("=" * 78)

print(
    "regime          survival     S->H      C->H/S     C->D"
)

for regime, result in results.items():
    M = result["matrix"]

    print(
        f"{regime:14} "
        f"{result['survival']:8.3f} "
        f"{M[('S','H')]:9.6f} "
        f"{M[('C','H')] + M[('C','S')]:9.6f} "
        f"{M[('C','D')]:9.6f}"
    )


print()
print("=" * 78)
print("SANITY CHECKS")
print("=" * 78)

for regime, result in results.items():
    M = result["matrix"]

    print()
    print(regime)

    for source in STATES:
        vals = [
            M[(source, target)]
            for target in STATES
            if math.isfinite(
                M[(source, target)]
            )
        ]

        row_sum = sum(vals)

        print(
            f"  row {source} sum = "
            f"{row_sum:.12f}"
        )

    print(
        f"  absorbing death check: "
        f"P(D->D)={M[('D','D')]:.12f}"
    )


print()
print("=" * 78)
print("INTERPRETATION GUARDRAIL")
print("=" * 78)
print("These matrices describe a coarse-grained simulation.")
print("They do NOT yet establish that the coarse state process")
print("is actually first-order Markov.")
print()
print("That assumption must be tested separately.")
