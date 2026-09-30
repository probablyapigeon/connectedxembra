import numpy as np
import random

ORIGINAL = {
    "COURAGE": {"r": 0.5, "m": 0.3, "k": 0.1},
    "WISDOM":  {"r": 0.2, "m": 0.6, "k": 0.05},
    "POWER":   {"r": 0.8, "m": 0.4, "k": -0.2},
}

def matrix(r, m, k):
    a = r + 0.06
    return np.array([
        [a,     m,   1.0,   0.285],
        [1.0,   0.0, 0.0,   0.0],
        [k*a,   k*m, 1.0+k, k*0.285],
        [0.2,   0.0, 0.0,   0.95],
    ])

def rho(r, m, k):
    return max(abs(np.linalg.eigvals(matrix(r,m,k))))

def distance(a, b):
    return np.sqrt(
        (a["r"]-b["r"])**2 +
        (a["m"]-b["m"])**2 +
        (a["k"]-b["k"])**2
    )

rng = random.Random(260930)

print("="*70)
print("SAVE LONK — MINIMUM STABILITY SEARCH")
print("="*70)

for name, original in ORIGINAL.items():

    old_rho = rho(**original)
    best = None

    # Search increasingly small neighborhoods around original Lonk.
    for radius in np.linspace(0.001, 1.0, 1000):

        for _ in range(1000):

            candidate = {
                "r": original["r"] + rng.uniform(-radius, radius),
                "m": original["m"] + rng.uniform(-radius, radius),
                "k": original["k"] + rng.uniform(-radius, radius),
            }

            new_rho = rho(**candidate)

            if new_rho < 0.999:

                d = distance(original, candidate)

                if best is None or d < best["distance"]:
                    best = {
                        **candidate,
                        "rho": new_rho,
                        "distance": d,
                    }

        # Once we've found a stable candidate and moved beyond its
        # distance, there's little reason to keep expanding far outward.
        if best and radius > best["distance"] * 1.5:
            break

    print()
    print(name)
    print("-"*70)
    print("ORIGINAL")
    print(f"reactivity r = {original['r']:.6f}")
    print(f"memory     m = {original['m']:.6f}")
    print(f"stiffness  k = {original['k']:.6f}")
    print(f"rho          = {old_rho:.9f}  💥")

    if best:
        print()
        print("STABLE CANDIDATE")
        print(f"reactivity r = {best['r']:.6f}")
        print(f"memory     m = {best['m']:.6f}")
        print(f"stiffness  k = {best['k']:.6f}")
        print(f"rho          = {best['rho']:.9f}  ✓")
        print(f"parameter distance = {best['distance']:.9f}")

        print()
        print("CHANGES")
        print(f"Δ reactivity = {best['r']-original['r']:+.6f}")
        print(f"Δ memory     = {best['m']-original['m']:+.6f}")
        print(f"Δ stiffness  = {best['k']-original['k']:+.6f}")

    else:
        print("NO STABLE CANDIDATE FOUND")

print()
print("rho < 1 means small disturbances decay instead of exploding.")
