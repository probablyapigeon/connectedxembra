import math
import random

PERSONALITIES = {
    "courage": {
        "baseline": 0.2,
        "reactivity": 0.5,
        "memory": 0.3,
        "stiffness": 0.1,
        "noise": 0.05,
    },
    "wisdom": {
        "baseline": 0.4,
        "reactivity": 0.2,
        "memory": 0.6,
        "stiffness": 0.05,
        "noise": 0.02,
    },
    "power": {
        "baseline": -0.1,
        "reactivity": 0.8,
        "memory": 0.4,
        "stiffness": -0.2,
        "noise": 0.1,
    },
}

TARGET = 0.8
MOOD_DECAY = 0.95
MOOD_SENSITIVITY = 0.2


def run(name, agent, steps=1000, seed=12345, use_noise=True):
    rng = random.Random(seed)

    psi = -0.1
    psi_prev = psi
    theta = 0.0
    global_mood = 0.0

    max_abs = 0.0
    exploded_at = None
    history = []

    for t in range(steps):
        # Same global-mood recurrence as Lonk.
        global_mood *= MOOD_DECAY
        global_mood += MOOD_SENSITIVITY * psi

        memory_term = agent["memory"] * psi_prev

        F = (
            theta
            + agent["reactivity"] * psi
            + agent["baseline"]
            + memory_term
            + global_mood * 0.3
        )

        epsilon = (
            rng.uniform(-agent["noise"], agent["noise"])
            if use_noise else 0.0
        )

        psi_new = F + epsilon

        theta_new = (
            theta
            + agent["stiffness"] * (psi_new - TARGET)
        )

        psi_prev = psi
        psi = psi_new
        theta = theta_new

        magnitude = max(abs(psi), abs(theta), abs(global_mood))
        max_abs = max(max_abs, magnitude)

        history.append((t, psi, theta, global_mood))

        if not all(math.isfinite(x) for x in (psi, theta, global_mood)):
            exploded_at = t
            break

        if magnitude > 1e12:
            exploded_at = t
            break

    if exploded_at is not None:
        status = "DIVERGED"
    else:
        tail = history[-100:]
        tail_mag = max(
            max(abs(p), abs(th), abs(g))
            for _, p, th, g in tail
        )

        if tail_mag < 10:
            status = "BOUNDED"
        else:
            status = "LARGE / POSSIBLY UNSTABLE"

    return {
        "name": name,
        "status": status,
        "steps": len(history),
        "exploded_at": exploded_at,
        "psi": psi,
        "theta": theta,
        "global_mood": global_mood,
        "max_abs": max_abs,
        "history": history,
    }


print("=" * 68)
print("AGENTIC LONK — NO-MERCY STABILITY TEST")
print("=" * 68)

for use_noise in (False, True):
    print()
    print("NOISE:", "ON" if use_noise else "OFF")
    print("-" * 68)

    for name, agent in PERSONALITIES.items():
        r = run(name, agent, use_noise=use_noise)

        print(
            f"{name.upper():8} "
            f"{r['status']:25} "
            f"steps={r['steps']:4} "
            f"explode={str(r['exploded_at']):>5} "
            f"max|x|={r['max_abs']:.6e}"
        )

        print(
            f"         final Psi={r['psi']:.6e} "
            f"theta={r['theta']:.6e} "
            f"mood={r['global_mood']:.6e}"
        )

print()
print("NOTE:")
print("This tests update_agent() itself.")
print("It intentionally excludes the per-frame high_health/low_health/etc.")
print("event injections so we can isolate the recurrence first.")
