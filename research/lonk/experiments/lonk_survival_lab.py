import random
import math
import statistics
from copy import deepcopy

SEED = 260930
WORLDS = 200
TICKS = 1500

CONDITIONS = {
    "A_INHERIT_MUTATE": (True, True),
    "B_INHERIT_FROZEN": (True, False),
    "C_RESET_MUTATE": (False, True),
}

DEFAULT_PERSONALITY = {
    "aggression": 50.0,
    "curiosity": 50.0,
    "anxiety": 50.0,
    "loyalty": 50.0,
}

INITIAL_STATE = [0.5, 0.5, 0.2, 0.3, 0.1]

def make_environment(seed):
    rng = random.Random(seed)
    env = []
    for _ in range(TICKS):
        sensory = rng.random()
        pain = rng.uniform(0.08, 0.35) if rng.random() < 0.06 else 0.0
        env.append((sensory, pain))
    return env

def dynamics_step(state, sensory, pain, rng):
    Psi, theta, A, V, P = state

    P = max(0.0, min(1.0, P + pain - 0.05 * P))

    A = max(0.0, min(
        1.0,
        A + 0.1 * (sensory - A)
        + 0.2 * (rng.random() - 0.5)
    ))

    V = max(0.0, min(
        1.0,
        V + 0.1 * (1 - P) - 0.05 * A
    ))

    Psi = max(0.0, min(
        1.0,
        Psi + 0.1 * (V - Psi)
        + 0.05 * (rng.random() - 0.5)
    ))

    theta = max(0.0, min(
        1.0,
        theta + 0.05 * (Psi - theta)
    ))

    return [Psi, theta, A, V, P]

class Lonk:
    def __init__(
        self,
        rng,
        generation=1,
        personality=None,
        inherit=True,
    ):
        self.state = INITIAL_STATE.copy()
        self.age = 0
        self.lifespan = rng.randint(30, 80)
        self.trauma = 0.0
        self.generation = generation

        if inherit and personality is not None:
            self.personality = deepcopy(personality)
        else:
            self.personality = deepcopy(DEFAULT_PERSONALITY)

        self.mutations = 0
        self.active_recovery = None


def mutate(lonk, rng):
    trait = rng.choice(list(lonk.personality))
    lonk.personality[trait] += rng.randint(-5, 5)
    lonk.mutations += 1


def boundary_count(state):
    return sum(
        x <= 1e-9 or x >= 1.0 - 1e-9
        for x in state
    )


def state_distance(a, b):
    return math.sqrt(
        sum((x - y) ** 2 for x, y in zip(a, b))
    )

def run_lineage(environment, seed, inherit, allow_mutation):
    rng = random.Random(seed)
    lonk = Lonk(rng)

    generation_depth = 1
    deaths = 0
    lifespans = []
    death_traumas = []
    total_mutations = 0
    total_boundary_hits = 0
    all_states = []
    recovery_times = []

    for tick, (sensory, pain) in enumerate(environment):
        before = lonk.state.copy()

        lonk.state = dynamics_step(
            lonk.state,
            sensory,
            pain,
            rng,
        )

        lonk.age += 1

        # Reconstruction assumption:
        # environmental pain contributes to historical trauma.
        if pain > 0:
            lonk.trauma += pain * 10.0
            lonk.active_recovery = {
                "tick": tick,
                "baseline": before,
            }

        # Reconstruction assumption:
        # trauma gets a small recovery term.
        lonk.trauma = max(0.0, lonk.trauma - 0.08)

        # Historical evolve() cadence.
        if allow_mutation and lonk.age % 10 == 0:
            mutate(lonk, rng)

        total_boundary_hits += boundary_count(lonk.state)
        all_states.append(tuple(lonk.state))

        # Observational only: does state return near
        # its pre-shock location?
        if lonk.active_recovery is not None:
            baseline = lonk.active_recovery["baseline"]

            if state_distance(lonk.state, baseline) < 0.20:
                recovery_times.append(
                    tick - lonk.active_recovery["tick"]
                )
                lonk.active_recovery = None

        # Historical death conditions.
        if lonk.age >= lonk.lifespan or lonk.trauma > 40:
            deaths += 1
            lifespans.append(lonk.age)
            death_traumas.append(lonk.trauma)
            total_mutations += lonk.mutations

            child_personality = (
                lonk.personality
                if inherit
                else None
            )

            lonk = Lonk(
                rng,
                generation=lonk.generation + 1,
                personality=child_personality,
                inherit=inherit,
            )

            generation_depth = max(
                generation_depth,
                lonk.generation,
            )

    if len(all_states) > 1:
        channel_variances = [
            statistics.pvariance(
                [state[i] for state in all_states]
            )
            for i in range(5)
        ]
        state_diversity = statistics.mean(channel_variances)
    else:
        state_diversity = 0.0

    trait_drift = math.sqrt(
        sum(
            (
                lonk.personality[key]
                - DEFAULT_PERSONALITY[key]
            ) ** 2
            for key in DEFAULT_PERSONALITY
        )
    )

    return {
        "generation_depth": generation_depth,
        "deaths": deaths,
        "mean_lifespan": (
            statistics.mean(lifespans)
            if lifespans else float(TICKS)
        ),
        "mean_death_trauma": (
            statistics.mean(death_traumas)
            if death_traumas else 0.0
        ),
        "boundary_rate": (
            total_boundary_hits / (TICKS * 5)
        ),
        "state_diversity": state_diversity,
        "mean_recovery": (
            statistics.mean(recovery_times)
            if recovery_times else float("nan")
        ),
        "trait_drift": trait_drift,
        "mutations": total_mutations + lonk.mutations,
    }

def mean_metric(rows, key):
    values = [
        row[key]
        for row in rows
        if math.isfinite(row[key])
    ]
    return (
        statistics.mean(values)
        if values
        else float("nan")
    )


METRICS = [
    "generation_depth",
    "deaths",
    "mean_lifespan",
    "mean_death_trauma",
    "boundary_rate",
    "state_diversity",
    "mean_recovery",
    "trait_drift",
    "mutations",
]


print("=" * 72)
print("LONK SURVIVAL LAB")
print("INHERITANCE / MUTATION ABLATION")
print("=" * 72)
print(f"Worlds per condition : {WORLDS}")
print(f"Ticks per world      : {TICKS}")
print(f"Master seed          : {SEED}")
print()

results = {
    name: []
    for name in CONDITIONS
}

for world_id in range(WORLDS):
    environment = make_environment(SEED + world_id)

    for condition_id, (name, config) in enumerate(
        CONDITIONS.items()
    ):
        inherit, mutation = config

        internal_seed = (
            SEED * 100000
            + world_id * 10
            + condition_id
        )

        result = run_lineage(
            environment,
            internal_seed,
            inherit,
            mutation,
        )

        results[name].append(result)


print("MEAN RESULTS")
print("-" * 72)

for name, rows in results.items():
    print()
    print(name)

    for metric in METRICS:
        value = mean_metric(rows, metric)
        print(f"  {metric:20} {value:.6f}")


print()
print("=" * 72)
print("A_INHERIT_MUTATE MINUS CONTROLS")
print("=" * 72)

experimental = results["A_INHERIT_MUTATE"]

for control_name in (
    "B_INHERIT_FROZEN",
    "C_RESET_MUTATE",
):
    control = results[control_name]

    print()
    print("A minus", control_name)

    for metric in METRICS:
        differences = []

        for a, b in zip(experimental, control):
            av = a[metric]
            bv = b[metric]

            if math.isfinite(av) and math.isfinite(bv):
                differences.append(av - bv)

        if differences:
            print(
                f"  {metric:20} "
                f"{statistics.mean(differences):+.6f}"
            )


print()
print("=" * 72)
print("INTERPRETATION GUARDRAIL")
print("=" * 72)
print("This is a reconstruction experiment.")
print("It does NOT prove the broken historical file")
print("executed this complete lifecycle.")
print()
print("Historical mechanisms preserved:")
print("  - five-state Lonk dynamics")
print("  - [0,1] state clipping")
print("  - lifespan 30..80")
print("  - trauma death threshold > 40")
print("  - personality mutation every 10 ages")
print("  - personality inheritance")
print()
print("Reconstruction assumptions:")
print("  - pain adds pain*10 to trauma")
print("  - trauma decays 0.08 per tick")
