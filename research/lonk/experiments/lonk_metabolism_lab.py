import random
import math
import statistics

SEED = 260930
TRIALS = 1000
TICKS = 2000

INITIAL_ENERGY = 0.65
INITIAL_DAMAGE = 0.05

MAINTENANCE = 0.008
REPAIR_COST = 0.012
REPAIR_RATE = 0.025
DAMAGE_RATE = 0.010

CONDITIONS = {
    "REGULATED": {
        "regulate": True,
        "repair": True,
    },
    "CONSTANT": {
        "regulate": False,
        "repair": True,
    },
    "NO_REPAIR": {
        "regulate": True,
        "repair": False,
    },
}


def clamp(x):
    return max(0.0, min(1.0, x))


def make_environment(seed):
    rng = random.Random(seed)
    env = []

    for t in range(TICKS):

        # Resource availability.
        resource = rng.random()

        # Famine windows deliberately stress regulation.
        famine = (
            500 <= t < 700
            or 1200 <= t < 1400
        )

        if famine:
            resource *= 0.12

        # Environmental damage/stress.
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
    regulate,
    repair,
):

    # Everyone pays basal maintenance.
    energy -= MAINTENANCE

    # Regulation changes resource-seeking effort.
    if regulate:
        if energy < 0.30:
            effort = 1.0
        elif energy < 0.55:
            effort = 0.65
        else:
            effort = 0.30
    else:
        effort = 0.55

    # Effort itself costs energy.
    effort_cost = 0.010 * effort
    energy -= effort_cost

    # Resource acquisition depends on available resource
    # and effort.
    intake = 0.030 * resource * effort
    energy += intake

    # Environmental stress creates damage.
    damage += shock

    # Ordinary wear.
    damage += DAMAGE_RATE

    # Repair requires both damage and available energy.
    repaired = 0.0

    if repair and damage > 0 and energy > 0.20:
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

    return (
        energy,
        damage,
        intake,
        effort,
        repaired,
        alive,
    )

def run_trial(environment, config):
    energy = INITIAL_ENERGY
    damage = INITIAL_DAMAGE

    alive = True
    death_tick = TICKS

    energies = []
    damages = []

    total_intake = 0.0
    total_effort = 0.0
    total_repair = 0.0

    starvation_ticks = 0
    critical_damage_ticks = 0

    # Recovery after each famine.
    famine_recoveries = []
    active_recovery = None

    for tick, (resource, shock) in enumerate(environment):

        # Record pre-famine operating energy.
        if tick in (500, 1200):
            active_recovery = {
                "baseline": energy,
                "famine_end": (
                    700 if tick == 500 else 1400
                ),
                "recovered": None,
            }

        (
            energy,
            damage,
            intake,
            effort,
            repaired,
            alive,
        ) = metabolic_step(
            energy,
            damage,
            resource,
            shock,
            config["regulate"],
            config["repair"],
        )

        energies.append(energy)
        damages.append(damage)

        total_intake += intake
        total_effort += effort
        total_repair += repaired

        if energy < 0.10:
            starvation_ticks += 1

        if damage > 0.80:
            critical_damage_ticks += 1

        # After famine ends, ask how long it takes
        # to regain 90% of pre-famine energy.
        if (
            active_recovery is not None
            and tick >= active_recovery["famine_end"]
            and active_recovery["recovered"] is None
        ):
            target = (
                0.90
                * active_recovery["baseline"]
            )

            if energy >= target:
                active_recovery["recovered"] = (
                    tick
                    - active_recovery["famine_end"]
                )

                famine_recoveries.append(
                    active_recovery["recovered"]
                )

                active_recovery = None

        if not alive:
            death_tick = tick
            break

    lifespan = len(energies)

    mean_energy = (
        statistics.mean(energies)
        if energies else 0.0
    )

    mean_damage = (
        statistics.mean(damages)
        if damages else INITIAL_DAMAGE
    )

    min_energy = (
        min(energies)
        if energies else INITIAL_ENERGY
    )

    max_damage = (
        max(damages)
        if damages else INITIAL_DAMAGE
    )

    recovery_mean = (
        statistics.mean(famine_recoveries)
        if famine_recoveries
        else float("nan")
    )

    return {
        "survived": int(alive),
        "lifespan": lifespan,
        "death_tick": death_tick,
        "mean_energy": mean_energy,
        "min_energy": min_energy,
        "mean_damage": mean_damage,
        "max_damage": max_damage,
        "total_intake": total_intake,
        "total_effort": total_effort,
        "total_repair": total_repair,
        "starvation_ticks": starvation_ticks,
        "critical_damage_ticks": critical_damage_ticks,
        "famine_recovery": recovery_mean,
        "final_energy": energy,
        "final_damage": damage,
    }

def mean(rows, key):
    vals = [
        r[key] for r in rows
        if math.isfinite(r[key])
    ]
    return statistics.mean(vals) if vals else float("nan")


results = {name: [] for name in CONDITIONS}

for trial in range(TRIALS):
    env = make_environment(SEED + trial)

    for name, config in CONDITIONS.items():
        results[name].append(
            run_trial(env, config)
        )


METRICS = [
    "survived",
    "lifespan",
    "mean_energy",
    "min_energy",
    "mean_damage",
    "max_damage",
    "total_intake",
    "total_effort",
    "total_repair",
    "starvation_ticks",
    "critical_damage_ticks",
    "famine_recovery",
]


print("=" * 72)
print("LONK METABOLISM LAB")
print("=" * 72)
print(f"Trials/condition : {TRIALS}")
print(f"Ticks/trial      : {TICKS}")
print(f"Total lives      : {TRIALS * len(CONDITIONS):,}")
print()

for name, rows in results.items():
    print(name)
    print("-" * 72)

    for metric in METRICS:
        print(
            f"{metric:24} "
            f"{mean(rows, metric):.6f}"
        )

    print()


print("=" * 72)
print("REGULATED MINUS CONTROLS")
print("=" * 72)

A = results["REGULATED"]

for control_name in ("CONSTANT", "NO_REPAIR"):
    B = results[control_name]

    print()
    print("REGULATED minus", control_name)

    for metric in METRICS:
        diffs = []

        for a, b in zip(A, B):
            x = a[metric]
            y = b[metric]

            if math.isfinite(x) and math.isfinite(y):
                diffs.append(x - y)

        if diffs:
            d = statistics.mean(diffs)

            if len(diffs) > 1:
                se = (
                    statistics.stdev(diffs)
                    / math.sqrt(len(diffs))
                )
                ci = 1.96 * se
            else:
                ci = float("nan")

            print(
                f"{metric:24} "
                f"delta={d:+.6f} "
                f"95%CI=[{d-ci:+.6f}, {d+ci:+.6f}]"
            )


print()
print("=" * 72)
print("INTERPRETATION GUARDRAIL")
print("=" * 72)
print("This is a toy computational metabolism experiment.")
print("Success means resource regulation improved persistence")
print("under the specified energy/damage rules.")
print("It does not establish biological life.")
