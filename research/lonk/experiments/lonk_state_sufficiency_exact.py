import random
import math

SEED = 260930
TRIALS = 2000
TICKS = 1000

GAIN = 0.0510
MAINTENANCE = 0.010

INITIAL_ENERGY = 0.65
INITIAL_DAMAGE = 0.05

REPAIR_COST = 0.012
REPAIR_RATE = 0.025
DAMAGE_RATE = 0.010

TOL = 1e-12


def clamp(x):
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------
# NORMAL SIMULATOR
# ---------------------------------------------------------

def simulator_step(
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


# ---------------------------------------------------------
# INDEPENDENT RECONSTRUCTION
# ---------------------------------------------------------

def reconstruct_next(
    E,
    D,
    resource,
    shock,
):
    # Maintenance occurs BEFORE policy selection,
    # exactly as in simulator_step().
    E2 = E - MAINTENANCE

    if E2 < 0.30:
        effort = 1.0
    elif E2 < 0.55:
        effort = 0.65
    else:
        effort = 0.30

    # Resource-seeking cost and intake.
    E2 = (
        E2
        - 0.010 * effort
        + GAIN * resource * effort
    )

    # Damage before repair.
    D2 = (
        D
        + shock
        + DAMAGE_RATE
    )

    # Same repair rule, independently expressed.
    if D2 > 0.0 and E2 > 0.20:
        repair_amount = min(
            REPAIR_RATE,
            D2,
        )

        repair_cost = (
            REPAIR_COST
            * repair_amount
            / REPAIR_RATE
        )

        if E2 >= repair_cost:
            E2 = E2 - repair_cost
            D2 = D2 - repair_amount

    E2 = max(0.0, min(1.0, E2))
    D2 = max(0.0, D2)

    alive2 = (
        E2 > 0.0
        and D2 < 1.0
    )

    return E2, D2, alive2


def make_environment(seed):
    rng = random.Random(seed)

    for _ in range(TICKS):
        resource = rng.random()

        shock = (
            rng.uniform(0.02, 0.08)
            if rng.random() < 0.04
            else 0.0
        )

        yield resource, shock


tested = 0
mismatches = 0

max_energy_error = 0.0
max_damage_error = 0.0

first_failure = None


for trial in range(TRIALS):
    energy = INITIAL_ENERGY
    damage = INITIAL_DAMAGE

    for tick, (resource, shock) in enumerate(
        make_environment(SEED + trial)
    ):
        predicted = reconstruct_next(
            energy,
            damage,
            resource,
            shock,
        )

        observed = simulator_step(
            energy,
            damage,
            resource,
            shock,
        )

        e_error = abs(
            predicted[0] - observed[0]
        )

        d_error = abs(
            predicted[1] - observed[1]
        )

        alive_match = (
            predicted[2] == observed[2]
        )

        max_energy_error = max(
            max_energy_error,
            e_error,
        )

        max_damage_error = max(
            max_damage_error,
            d_error,
        )

        tested += 1

        if (
            e_error > TOL
            or d_error > TOL
            or not alive_match
        ):
            mismatches += 1

            if first_failure is None:
                first_failure = {
                    "trial": trial,
                    "tick": tick,
                    "present": (
                        energy,
                        damage,
                        resource,
                        shock,
                    ),
                    "predicted": predicted,
                    "observed": observed,
                    "errors": (
                        e_error,
                        d_error,
                    ),
                }

        energy, damage, alive = observed

        if not alive:
            break


print("=" * 78)
print("LONK EXACT STATE-SUFFICIENCY AUTOPSY")
print("=" * 78)

print(f"Transitions tested : {tested:,}")
print(f"Tolerance          : {TOL:.1e}")
print()

print(
    f"Max energy error   : "
    f"{max_energy_error:.18e}"
)

print(
    f"Max damage error   : "
    f"{max_damage_error:.18e}"
)

print(
    f"Mismatches         : "
    f"{mismatches}"
)

print()

if first_failure is not None:
    print("FIRST FAILURE")
    print(first_failure)
    print()


if mismatches == 0:
    print("EXACT RECONSTRUCTION PASS")
    print()
    print(
        "For every tested transition, the next "
        "metabolic state was reconstructed from:"
    )
    print()
    print(
        "  present energy"
    )
    print(
        "  present damage"
    )
    print(
        "  current resource input"
    )
    print(
        "  current shock input"
    )
    print()
    print(
        "No additional historical state was "
        "required for this subsystem."
    )

else:
    print("RECONSTRUCTION FAILED")
    print(
        "The declared present state/input set "
        "was not sufficient."
    )


print()
print("=" * 78)
print("INTERPRETATION")
print("=" * 78)

print(
    "This tests computational state sufficiency "
    "for the toy Lonk metabolism only."
)

print(
    "It does not establish a general result "
    "about memory, life, or biological systems."
)
