import random
import statistics

SEED = 260930
TRIALS = 200
TICKS = 1000

INITIAL_ENERGY = 0.65
INITIAL_DAMAGE = 0.05

REPAIR_COST = 0.012
REPAIR_RATE = 0.025
DAMAGE_RATE = 0.010

# Sweep the two parameters we care about.
RESOURCE_GAINS = [
    0.02, 0.03, 0.04, 0.05, 0.06,
    0.07, 0.08, 0.09, 0.10,
]

MAINTENANCE_COSTS = [
    0.002, 0.004, 0.006,
    0.008, 0.010, 0.012,
]


def clamp(x):
    return max(0.0, min(1.0, x))


def make_environment(seed):
    rng = random.Random(seed)
    env = []

    for t in range(TICKS):
        resource = rng.random()

        # Leave famine OUT initially.
        # We first locate ordinary viability.
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
    resource_gain,
    maintenance,
):
    # Basal maintenance.
    energy -= maintenance

    # Same regulator as previous experiment.
    if energy < 0.30:
        effort = 1.0
    elif energy < 0.55:
        effort = 0.65
    else:
        effort = 0.30

    # Seeking resources has a cost.
    energy -= 0.010 * effort

    # Intake.
    intake = resource_gain * resource * effort
    energy += intake

    # Environmental + ordinary damage.
    damage += shock
    damage += DAMAGE_RATE

    # Repair.
    repaired = 0.0

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

def run_trial(environment, resource_gain, maintenance):
    energy = INITIAL_ENERGY
    damage = INITIAL_DAMAGE

    for tick, (resource, shock) in enumerate(environment):
        energy, damage, alive = metabolic_step(
            energy,
            damage,
            resource,
            shock,
            resource_gain,
            maintenance,
        )

        if not alive:
            return {
                "survived": 0,
                "lifespan": tick + 1,
                "final_energy": energy,
                "final_damage": damage,
            }

    return {
        "survived": 1,
        "lifespan": TICKS,
        "final_energy": energy,
        "final_damage": damage,
    }


# ---------------------------------------------------------
# Pre-generate environments.
# Every parameter regime receives identical worlds.
# ---------------------------------------------------------

environments = [
    make_environment(SEED + trial)
    for trial in range(TRIALS)
]

grid = {}

print("=" * 78)
print("LONK METABOLIC PHASE DIAGRAM")
print("=" * 78)
print(f"Trials/regime : {TRIALS}")
print(f"Ticks/trial   : {TICKS}")
print(f"Grid          : {len(MAINTENANCE_COSTS)} x {len(RESOURCE_GAINS)}")
print()


for maintenance in MAINTENANCE_COSTS:
    for gain in RESOURCE_GAINS:

        rows = [
            run_trial(env, gain, maintenance)
            for env in environments
        ]

        survival = statistics.mean(
            row["survived"] for row in rows
        )

        lifespan = statistics.mean(
            row["lifespan"] for row in rows
        )

        grid[(maintenance, gain)] = {
            "survival": survival,
            "lifespan": lifespan,
        }


# ---------------------------------------------------------
# Numerical survival map
# ---------------------------------------------------------

print("SURVIVAL PROBABILITY")
print()

header = "maint\\gain " + " ".join(
    f"{g:>6.3f}" for g in RESOURCE_GAINS
)

print(header)
print("-" * len(header))

for maintenance in MAINTENANCE_COSTS:
    row = [f"{maintenance:>10.3f}"]

    for gain in RESOURCE_GAINS:
        s = grid[(maintenance, gain)]["survival"]
        row.append(f"{s:6.2f}")

    print(" ".join(row))


# ---------------------------------------------------------
# Visual map
# ---------------------------------------------------------

def symbol(s):
    if s == 0:
        return "💀"
    if s < 0.25:
        return "░"
    if s < 0.50:
        return "▒"
    if s < 0.75:
        return "▓"
    if s < 1.0:
        return "◆"
    return "🧬"


print()
print("VIABILITY MAP")
print("💀=0%  ░=<25%  ▒=<50%  ▓=<75%  ◆=<100%  🧬=100%")
print()

print(
    "maint  "
    + " ".join(f"{g:.2f}" for g in RESOURCE_GAINS)
)

for maintenance in MAINTENANCE_COSTS:
    cells = [
        symbol(grid[(maintenance, gain)]["survival"])
        for gain in RESOURCE_GAINS
    ]

    print(
        f"{maintenance:.3f}  "
        + "  ".join(cells)
    )


# ---------------------------------------------------------
# Find critical regimes
# ---------------------------------------------------------

ranked = sorted(
    (
        (
            abs(values["survival"] - 0.50),
            maintenance,
            gain,
            values["survival"],
            values["lifespan"],
        )
        for (maintenance, gain), values in grid.items()
    ),
    key=lambda x: x[0],
)


print()
print("=" * 78)
print("REGIMES CLOSEST TO 50% SURVIVAL")
print("=" * 78)

for _, maintenance, gain, survival, lifespan in ranked[:10]:
    print(
        f"maintenance={maintenance:.3f} "
        f"gain={gain:.3f} "
        f"survival={survival:.3f} "
        f"mean_lifespan={lifespan:.2f}"
    )


# ---------------------------------------------------------
# Estimate boundary gain at each maintenance level
# ---------------------------------------------------------

print()
print("=" * 78)
print("APPROXIMATE VIABILITY FRONTIER")
print("=" * 78)

for maintenance in MAINTENANCE_COSTS:

    candidates = [
        (
            abs(grid[(maintenance, gain)]["survival"] - 0.50),
            gain,
            grid[(maintenance, gain)]["survival"],
        )
        for gain in RESOURCE_GAINS
    ]

    _, gain, survival = min(candidates)

    print(
        f"maintenance={maintenance:.3f} "
        f"boundary_gain≈{gain:.3f} "
        f"survival={survival:.3f}"
    )
