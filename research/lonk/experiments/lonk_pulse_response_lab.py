import random
import math
import statistics

SEED = 260930
TRIALS = 1000

WARMUP = 300
RECOVERY = 300

INITIAL = [0.5, 0.5, 0.2, 0.3, 0.1]

CONDITIONS = {
    "FULL": (True, True),
    "NO_RELAXATION": (False, True),
    "NO_CLIPPING": (True, False),
    "NEITHER": (False, False),
}


def clip(x):
    return max(0.0, min(1.0, x))


def dist(a, b):
    return math.sqrt(
        sum((x-y)**2 for x, y in zip(a, b))
    )


def make_trial(seed):
    rng = random.Random(seed)

    # Constant environment lets us establish an operating point.
    sensory = 0.50

    noise = [
        (
            rng.random() - 0.5,
            rng.random() - 0.5,
        )
        for _ in range(WARMUP + RECOVERY + 1)
    ]

    return sensory, noise


def step(state, sensory, pain, noises,
         relaxation=True, clipping=True):

    Psi, theta, A, V, P = state
    a_noise, psi_noise = noises

    if relaxation:
        P2 = P + pain - 0.05 * P
        A2 = A + 0.1 * (sensory - A) + 0.2 * a_noise
    else:
        P2 = P + pain
        A2 = A + 0.2 * a_noise

    V2 = V + 0.1 * (1 - P2) - 0.05 * A2

    if relaxation:
        Psi2 = Psi + 0.1 * (V2 - Psi) + 0.05 * psi_noise
        theta2 = theta + 0.05 * (Psi2 - theta)
    else:
        Psi2 = Psi + 0.05 * psi_noise
        theta2 = theta

    out = [Psi2, theta2, A2, V2, P2]

    if clipping:
        out = [clip(x) for x in out]

    return out

def run_trial(seed, condition):
    relaxation, clipping = condition
    sensory, noise = make_trial(seed)

    state = INITIAL.copy()

    # ---------------------------------------------
    # Warmup to operating state
    # ---------------------------------------------
    for t in range(WARMUP):
        state = step(
            state,
            sensory,
            0.0,
            noise[t],
            relaxation,
            clipping,
        )

    baseline = state.copy()

    # ---------------------------------------------
    # Counterfactual twins
    # ---------------------------------------------
    shocked = baseline.copy()
    control = baseline.copy()

    shock_noise = noise[WARMUP]

    # Control receives no pain.
    control = step(
        control,
        sensory,
        0.0,
        shock_noise,
        relaxation,
        clipping,
    )

    # Shocked twin receives standardized pulse.
    shocked = step(
        shocked,
        sensory,
        0.75,
        shock_noise,
        relaxation,
        clipping,
    )

    initial_effect = dist(shocked, control)

    effects = [initial_effect]

    half_time = None
    ninety_time = None

    peak_effect = initial_effect
    peak_time = 0

    # ---------------------------------------------
    # Recovery: same environment, same noise
    # ---------------------------------------------
    for t in range(1, RECOVERY + 1):
        n = noise[WARMUP + t]

        shocked = step(
            shocked,
            sensory,
            0.0,
            n,
            relaxation,
            clipping,
        )

        control = step(
            control,
            sensory,
            0.0,
            n,
            relaxation,
            clipping,
        )

        effect = dist(shocked, control)
        effects.append(effect)

        if effect > peak_effect:
            peak_effect = effect
            peak_time = t

        if initial_effect > 1e-12:
            fraction_remaining = effect / initial_effect

            if half_time is None and fraction_remaining <= 0.50:
                half_time = t

            if ninety_time is None and fraction_remaining <= 0.10:
                ninety_time = t

    # ---------------------------------------------
    # Metrics
    # ---------------------------------------------
    residual = effects[-1]

    auc = sum(effects)

    if initial_effect > 1e-12:
        recovery_fraction = 1.0 - residual / initial_effect
        normalized_auc = auc / initial_effect
        amplification = peak_effect / initial_effect
    else:
        recovery_fraction = float("nan")
        normalized_auc = float("nan")
        amplification = float("nan")

    # Late-window residual guards against a lucky
    # final tick accidentally looking recovered.
    late = effects[-50:]
    late_mean = statistics.mean(late)

    return {
        "initial_effect": initial_effect,
        "peak_effect": peak_effect,
        "peak_time": peak_time,
        "amplification": amplification,
        "half_time": (
            half_time if half_time is not None
            else RECOVERY + 1
        ),
        "ninety_time": (
            ninety_time if ninety_time is not None
            else RECOVERY + 1
        ),
        "residual": residual,
        "late_mean": late_mean,
        "recovery_fraction": recovery_fraction,
        "normalized_auc": normalized_auc,
    }

def finite_mean(rows, key):
    vals = [
        row[key]
        for row in rows
        if math.isfinite(row[key])
    ]
    return statistics.mean(vals) if vals else float("nan")


METRICS = [
    "initial_effect",
    "peak_effect",
    "peak_time",
    "amplification",
    "half_time",
    "ninety_time",
    "residual",
    "late_mean",
    "recovery_fraction",
    "normalized_auc",
]


results = {
    name: []
    for name in CONDITIONS
}

for trial in range(TRIALS):
    trial_seed = SEED + trial

    for name, condition in CONDITIONS.items():
        results[name].append(
            run_trial(trial_seed, condition)
        )


print("=" * 78)
print("LONK COUNTERFACTUAL PULSE-RESPONSE LAB")
print("=" * 78)
print(f"Trials/condition : {TRIALS}")
print(f"Warmup           : {WARMUP}")
print(f"Recovery window  : {RECOVERY}")
print(f"Pain pulse       : 0.75")
print(f"Master seed      : {SEED}")
print()

print("MEAN RESULTS")
print("-" * 78)

for name, rows in results.items():
    print()
    print(name)

    for metric in METRICS:
        print(
            f"  {metric:20} "
            f"{finite_mean(rows, metric):.9f}"
        )


print()
print("=" * 78)
print("PAIRED DIFFERENCES")
print("=" * 78)

COMPARISONS = [
    ("FULL", "NO_RELAXATION"),
    ("NO_CLIPPING", "NEITHER"),
    ("FULL", "NO_CLIPPING"),
]

for left_name, right_name in COMPARISONS:
    print()
    print(f"{left_name} minus {right_name}")

    left = results[left_name]
    right = results[right_name]

    for metric in METRICS:
        diffs = []

        for a, b in zip(left, right):
            av = a[metric]
            bv = b[metric]

            if math.isfinite(av) and math.isfinite(bv):
                diffs.append(av - bv)

        if not diffs:
            continue

        mean_diff = statistics.mean(diffs)

        if len(diffs) > 1:
            sd = statistics.stdev(diffs)
            se = sd / math.sqrt(len(diffs))
            ci = 1.96 * se
        else:
            ci = float("nan")

        print(
            f"  {metric:20} "
            f"delta={mean_diff:+.9f} "
            f"95%CI=[{mean_diff-ci:+.9f}, "
            f"{mean_diff+ci:+.9f}]"
        )


print()
print("=" * 78)
print("RECOVERY CHECK")
print("=" * 78)

for name, rows in results.items():
    recovered_50 = sum(
        row["half_time"] <= RECOVERY
        for row in rows
    )

    recovered_90 = sum(
        row["ninety_time"] <= RECOVERY
        for row in rows
    )

    positive_recovery = sum(
        math.isfinite(row["recovery_fraction"])
        and row["recovery_fraction"] > 0
        for row in rows
    )

    print()
    print(name)
    print(
        f"  reached 50% recovery: "
        f"{recovered_50}/{TRIALS} "
        f"({100*recovered_50/TRIALS:.1f}%)"
    )
    print(
        f"  reached 90% recovery: "
        f"{recovered_90}/{TRIALS} "
        f"({100*recovered_90/TRIALS:.1f}%)"
    )
    print(
        f"  positive final recovery: "
        f"{positive_recovery}/{TRIALS} "
        f"({100*positive_recovery/TRIALS:.1f}%)"
    )


print()
print("=" * 78)
print("INTERPRETATION")
print("=" * 78)
print("Shock and control twins receive identical future noise.")
print("Their separation therefore estimates the causal effect")
print("of the standardized pain pulse inside this simulation.")
print()
print("Evidence for restoration requires:")
print("  1. non-trivial initial shock effect")
print("  2. declining shock/control separation")
print("  3. small late residual")
print("  4. substantial 50% / 90% recovery rates")
print()
print("This tests computational restorative dynamics.")
print("It does not establish biological life or consciousness.")
