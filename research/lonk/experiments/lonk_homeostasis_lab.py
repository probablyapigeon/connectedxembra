import random
import math
import statistics

SEED = 260930
TRIALS = 500
TICKS = 1000

INITIAL = [0.5, 0.5, 0.2, 0.3, 0.1]

CONDITIONS = {
    "FULL": {
        "relaxation": True,
        "clipping": True,
    },
    "NO_RELAXATION": {
        "relaxation": False,
        "clipping": True,
    },
    "NO_CLIPPING": {
        "relaxation": True,
        "clipping": False,
    },
    "NEITHER": {
        "relaxation": False,
        "clipping": False,
    },
}

def clip(x):
    return max(0.0, min(1.0, x))


def environment(seed):
    rng = random.Random(seed)
    out = []

    for t in range(TICKS):
        sensory = rng.random()

        # Ordinary disturbances.
        pain = (
            rng.uniform(0.08, 0.35)
            if rng.random() < 0.06
            else 0.0
        )

        # Occasional larger shock.
        if t % 200 == 100:
            pain += 0.75

        # Pre-generate ALL stochasticity so every
        # condition receives identical noise.
        arousal_noise = rng.random() - 0.5
        psi_noise = rng.random() - 0.5

        out.append(
            (
                sensory,
                pain,
                arousal_noise,
                psi_noise,
            )
        )

    return out


def step(state, inputs, relaxation, clipping):
    Psi, theta, A, V, P = state

    sensory, pain, a_noise, psi_noise = inputs

    # Prediction-error decay is one homeostatic term.
    if relaxation:
        P_new = P + pain - 0.05 * P
    else:
        P_new = P + pain

    # Arousal follows sensory conditions.
    if relaxation:
        A_new = (
            A
            + 0.1 * (sensory - A)
            + 0.2 * a_noise
        )
    else:
        A_new = A + 0.2 * a_noise

    # Original valence rule.
    V_new = V + 0.1 * (1 - P_new) - 0.05 * A_new

    # Psi follows valence when relaxation is enabled.
    if relaxation:
        Psi_new = (
            Psi
            + 0.1 * (V_new - Psi)
            + 0.05 * psi_noise
        )
    else:
        Psi_new = Psi + 0.05 * psi_noise

    # theta follows Psi when relaxation is enabled.
    if relaxation:
        theta_new = theta + 0.05 * (Psi_new - theta)
    else:
        theta_new = theta

    result = [
        Psi_new,
        theta_new,
        A_new,
        V_new,
        P_new,
    ]

    if clipping:
        result = [clip(x) for x in result]

    return result

def distance(a, b):
    return math.sqrt(
        sum((x - y) ** 2 for x, y in zip(a, b))
    )


def magnitude(state):
    return max(abs(x) for x in state)


def run_trial(inputs, config):
    state = INITIAL.copy()

    max_magnitude = magnitude(state)
    boundary_hits = 0
    trajectory = []

    shock_records = []
    active_shock = None

    diverged = False
    divergence_tick = None

    for tick, inp in enumerate(inputs):
        before = state.copy()

        # Known large shocks occur here.
        major_shock = (tick % 200 == 100)

        state = step(
            state,
            inp,
            relaxation=config["relaxation"],
            clipping=config["clipping"],
        )

        trajectory.append(tuple(state))

        current_mag = magnitude(state)
        max_magnitude = max(
            max_magnitude,
            current_mag,
        )

        if config["clipping"]:
            boundary_hits += sum(
                x <= 1e-9 or x >= 1.0 - 1e-9
                for x in state
            )

        # Catastrophic numerical escape.
        if (
            not all(math.isfinite(x) for x in state)
            or current_mag > 1e6
        ):
            diverged = True
            divergence_tick = tick
            break

        # Start measuring response to major shock.
        if major_shock:
            active_shock = {
                "tick": tick,
                "baseline": before,
                "peak": distance(state, before),
                "area": distance(state, before),
            }

        elif active_shock is not None:
            d = distance(
                state,
                active_shock["baseline"],
            )

            active_shock["peak"] = max(
                active_shock["peak"],
                d,
            )

            active_shock["area"] += d

            # Recovery criterion:
            # return within radius 0.20 of pre-shock state.
            if d < 0.20:
                active_shock["recovery"] = (
                    tick - active_shock["tick"]
                )

                shock_records.append(active_shock)
                active_shock = None

            # Give it 100 ticks.
            elif tick - active_shock["tick"] >= 100:
                active_shock["recovery"] = None
                shock_records.append(active_shock)
                active_shock = None

    # Preserve unresolved final shock.
    if active_shock is not None:
        active_shock["recovery"] = None
        shock_records.append(active_shock)

    recovered = [
        s["recovery"]
        for s in shock_records
        if s["recovery"] is not None
    ]

    recovery_fraction = (
        len(recovered) / len(shock_records)
        if shock_records else float("nan")
    )

    mean_recovery = (
        statistics.mean(recovered)
        if recovered else float("nan")
    )

    mean_peak = (
        statistics.mean(
            s["peak"] for s in shock_records
        )
        if shock_records else float("nan")
    )

    mean_deviation_area = (
        statistics.mean(
            s["area"] for s in shock_records
        )
        if shock_records else float("nan")
    )

    # Trajectory variability.
    if len(trajectory) > 1:
        variances = [
            statistics.pvariance(
                [state[i] for state in trajectory]
            )
            for i in range(5)
        ]
        diversity = statistics.mean(variances)
    else:
        diversity = 0.0

    return {
        "diverged": int(diverged),
        "divergence_tick": (
            divergence_tick
            if divergence_tick is not None
            else TICKS
        ),
        "max_magnitude": max_magnitude,
        "boundary_rate": (
            boundary_hits
            / max(1, len(trajectory) * 5)
        ),
        "recovery_fraction": recovery_fraction,
        "mean_recovery": mean_recovery,
        "mean_peak": mean_peak,
        "deviation_area": mean_deviation_area,
        "state_diversity": diversity,
    }

def finite_mean(rows, key):
    vals = [
        r[key]
        for r in rows
        if math.isfinite(r[key])
    ]
    return statistics.mean(vals) if vals else float("nan")


results = {
    name: []
    for name in CONDITIONS
}

for trial in range(TRIALS):
    inputs = environment(SEED + trial)

    for name, config in CONDITIONS.items():
        results[name].append(
            run_trial(inputs, config)
        )


METRICS = [
    "diverged",
    "divergence_tick",
    "max_magnitude",
    "boundary_rate",
    "recovery_fraction",
    "mean_recovery",
    "mean_peak",
    "deviation_area",
    "state_diversity",
]


print("=" * 76)
print("LONK HOMEOSTASIS ABLATION LAB")
print("=" * 76)
print(f"Trials:          {TRIALS}")
print(f"Ticks/trial:     {TICKS}")
print(f"Transitions:     {TRIALS * TICKS * len(CONDITIONS):,}")
print(f"Master seed:     {SEED}")
print()

print("MEAN RESULTS")
print("-" * 76)

for name, rows in results.items():
    print()
    print(name)

    for metric in METRICS:
        value = finite_mean(rows, metric)
        print(f"  {metric:20} {value:.6f}")


print()
print("=" * 76)
print("PAIRED HOMEOSTASIS EFFECTS")
print("=" * 76)

COMPARISONS = [
    ("FULL", "NO_RELAXATION"),
    ("NO_CLIPPING", "NEITHER"),
    ("FULL", "NO_CLIPPING"),
]

for left_name, right_name in COMPARISONS:
    left = results[left_name]
    right = results[right_name]

    print()
    print(f"{left_name} minus {right_name}")

    for metric in METRICS:
        diffs = []

        for a, b in zip(left, right):
            av = a[metric]
            bv = b[metric]

            if math.isfinite(av) and math.isfinite(bv):
                diffs.append(av - bv)

        if diffs:
            mean_diff = statistics.mean(diffs)

            if len(diffs) > 1:
                sd = statistics.stdev(diffs)
                se = sd / math.sqrt(len(diffs))
                ci = 1.96 * se
            else:
                ci = float("nan")

            print(
                f"  {metric:20} "
                f"delta={mean_diff:+.6f} "
                f"95%CI=[{mean_diff-ci:+.6f}, "
                f"{mean_diff+ci:+.6f}]"
            )


print()
print("=" * 76)
print("HOMEOSTASIS QUESTIONS")
print("=" * 76)
print("FULL vs NO_RELAXATION:")
print("  Do restorative feedback terms improve regulation")
print("  when both systems have identical clipping?")
print()
print("NO_CLIPPING vs NEITHER:")
print("  Do restorative feedback terms stabilize the system")
print("  when clipping is completely removed?")
print()
print("FULL vs NO_CLIPPING:")
print("  How much additional boundedness comes from clipping?")
print()
print("Interpret recovery and deviation together.")
print("A system that merely hits a boundary is bounded,")
print("but that alone is not evidence of homeostatic recovery.")
