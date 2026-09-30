import random
import statistics
import math

SEED = 260930
TRIALS = 1000
TICKS = 1000

MAINTENANCE = 0.010

GAINS = [
    0.0500, 0.0505, 0.0510, 0.0515, 0.0520,
    0.0525, 0.0530, 0.0535, 0.0540, 0.0545,
    0.0550, 0.0555, 0.0560, 0.0565, 0.0570,
    0.0575, 0.0580, 0.0585, 0.0590, 0.0595,
    0.0600,
]

INITIAL_ENERGY = 0.65
INITIAL_DAMAGE = 0.05

REPAIR_COST = 0.012
REPAIR_RATE = 0.025
DAMAGE_RATE = 0.010


def clamp(x):
    return max(0.0, min(1.0, x))


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


def step(energy, damage, resource, shock, gain):
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

    alive = energy > 0.0 and damage < 1.0

    return energy, damage, alive


def run_trial(env, gain):
    energy = INITIAL_ENERGY
    damage = INITIAL_DAMAGE

    for tick, (resource, shock) in enumerate(env):
        energy, damage, alive = step(
            energy,
            damage,
            resource,
            shock,
            gain,
        )

        if not alive:
            cause = (
                "energy"
                if energy <= 0.0
                else "damage"
            )

            return 0, tick + 1, cause

    return 1, TICKS, "survived"

# Pre-generate identical environments for every gain.
environments = [
    make_environment(SEED + i)
    for i in range(TRIALS)
]

results = []

print("=" * 76)
print("LONK FINE VIABILITY-BOUNDARY SWEEP")
print("=" * 76)
print(f"Maintenance : {MAINTENANCE}")
print(f"Trials/gain : {TRIALS}")
print(f"Ticks/trial : {TICKS}")
print(f"Gain values : {len(GAINS)}")
print()

for gain in GAINS:
    rows = [
        run_trial(env, gain)
        for env in environments
    ]

    survived = sum(row[0] for row in rows)
    survival = survived / TRIALS

    mean_lifespan = statistics.mean(
        row[1] for row in rows
    )

    energy_deaths = sum(
        row[2] == "energy"
        for row in rows
    )

    damage_deaths = sum(
        row[2] == "damage"
        for row in rows
    )

    se = math.sqrt(
        survival * (1.0 - survival) / TRIALS
    )
    ci = 1.96 * se

    result = {
        "gain": gain,
        "survival": survival,
        "lifespan": mean_lifespan,
        "energy_deaths": energy_deaths,
        "damage_deaths": damage_deaths,
        "ci": ci,
    }

    results.append(result)

    print(
        f"gain={gain:.4f}  "
        f"survival={survival:.3f}  "
        f"95%CI=[{max(0.0, survival-ci):.3f}, "
        f"{min(1.0, survival+ci):.3f}]  "
        f"life={mean_lifespan:.2f}  "
        f"E={energy_deaths:4d}  "
        f"D={damage_deaths:4d}"
    )


print()
print("=" * 76)
print("TARGET REGIMES")
print("=" * 76)

selected = {}

for target in (0.10, 0.50, 0.90):
    best = min(
        results,
        key=lambda r: abs(
            r["survival"] - target
        ),
    )

    selected[target] = best

    print(
        f"target={target:.2f}  "
        f"gain={best['gain']:.4f}  "
        f"observed={best['survival']:.3f}  "
        f"mean_life={best['lifespan']:.2f}"
    )


print()
print("=" * 76)
print("LOCAL TRANSITION SLOPES")
print("=" * 76)

for left, right in zip(results[:-1], results[1:]):
    ds = right["survival"] - left["survival"]
    dg = right["gain"] - left["gain"]

    slope = ds / dg

    print(
        f"{left['gain']:.4f} -> {right['gain']:.4f}  "
        f"delta_survival={ds:+.3f}  "
        f"slope={slope:+.1f}/gain"
    )


steepest_left, steepest_right = max(
    zip(results[:-1], results[1:]),
    key=lambda pair: abs(
        (
            pair[1]["survival"]
            - pair[0]["survival"]
        )
        /
        (
            pair[1]["gain"]
            - pair[0]["gain"]
        )
    ),
)

print()
print("=" * 76)
print("STEEPEST OBSERVED TRANSITION")
print("=" * 76)
print(
    f"{steepest_left['gain']:.4f} "
    f"(S={steepest_left['survival']:.3f})"
)
print("        ↓")
print(
    f"{steepest_right['gain']:.4f} "
    f"(S={steepest_right['survival']:.3f})"
)

print()
print("These are finite-horizon simulation survival rates.")
print("They are not evidence of a biological phase transition.")
