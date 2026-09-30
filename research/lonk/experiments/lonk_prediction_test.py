import math
import numpy as np

PERSONALITIES = {
    "COURAGE": {"b": 0.2,  "r": 0.5, "m": 0.3, "k": 0.1},
    "WISDOM":  {"b": 0.4,  "r": 0.2, "m": 0.6, "k": 0.05},
    "POWER":   {"b": -0.1, "r": 0.8, "m": 0.4, "k": -0.2},
}

TARGET = 0.8
THRESHOLD = 1e12
MAX_STEPS = 2000

# x = [Psi_t, Psi_(t-1), theta_t, G_t]
X0 = np.array([-0.1, -0.1, 0.0, 0.0], dtype=float)


def build_system(p):
    b, r, m, k = p["b"], p["r"], p["m"], p["k"]

    # G_(t+1) = .95 G_t + .2 Psi_t
    #
    # Psi_(t+1)
    # = theta_t + r Psi_t + b + m Psi_(t-1) + .3 G_(t+1)
    # = (r+.06)Psi_t + m Psi_(t-1) + theta_t + .285G_t + b

    a = r + 0.06

    A = np.array([
        [a,       m,   1.0,   0.285],
        [1.0,     0.0, 0.0,   0.0],
        [k*a,     k*m, 1.0+k, k*0.285],
        [0.2,     0.0, 0.0,   0.95],
    ], dtype=float)

    # theta_(t+1) = theta_t + k(Psi_(t+1) - TARGET)
    c = np.array([
        b,
        0.0,
        k * (b - TARGET),
        0.0,
    ], dtype=float)

    return A, c


def direct_lonk(p):
    """Original deterministic Lonk recurrence."""
    psi = -0.1
    psi_prev = -0.1
    theta = 0.0
    mood = 0.0

    history = []

    for t in range(MAX_STEPS):
        mood = 0.95 * mood + 0.2 * psi

        psi_new = (
            theta
            + p["r"] * psi
            + p["b"]
            + p["m"] * psi_prev
            + 0.3 * mood
        )

        theta_new = theta + p["k"] * (psi_new - TARGET)

        psi_prev = psi
        psi = psi_new
        theta = theta_new

        x = np.array([psi, psi_prev, theta, mood])

        history.append(x.copy())

        if np.max(np.abs(x)) > THRESHOLD:
            return t, history

    return None, history


def matrix_lonk(A, c):
    """Same recurrence expressed as x_(t+1)=Ax_t+c."""
    x = X0.copy()
    history = []

    for t in range(MAX_STEPS):
        x = A @ x + c
        history.append(x.copy())

        if np.max(np.abs(x)) > THRESHOLD:
            return t, history

    return None, history


print("=" * 78)
print("AGENTIC LONK — EIGENVALUE PREDICTION / RECONSTRUCTION TEST")
print("=" * 78)

for name, p in PERSONALITIES.items():
    A, c = build_system(p)

    eigvals = np.linalg.eigvals(A)
    rho = max(abs(eigvals))

    direct_t, direct_hist = direct_lonk(p)
    matrix_t, matrix_hist = matrix_lonk(A, c)

    n = min(len(direct_hist), len(matrix_hist))

    max_error = 0.0
    for i in range(n):
        err = np.max(np.abs(direct_hist[i] - matrix_hist[i]))
        max_error = max(max_error, float(err))

    # Relative reconstruction error at the final comparable step.
    scale = max(
        1.0,
        float(np.max(np.abs(direct_hist[n-1])))
    )
    relative_error = float(
        np.max(np.abs(direct_hist[n-1] - matrix_hist[n-1])) / scale
    )

    # Crude dominant-mode estimate:
    # starting scale -> threshold using rho^t.
    initial_scale = max(np.max(np.abs(X0)), 1e-15)

    dominant_estimate = (
        math.log(THRESHOLD / initial_scale) / math.log(rho)
        if rho > 1
        else float("inf")
    )

    print()
    print(name)
    print("-" * 78)
    print(f"spectral radius:             {rho:.9f}")
    print(f"dominant-mode rough estimate:{dominant_estimate:10.2f} steps")
    print(f"direct recurrence crossing:  {direct_t}")
    print(f"matrix recurrence crossing:  {matrix_t}")
    print(f"crossing-time match:          {direct_t == matrix_t}")
    print(f"max absolute trajectory err: {max_error:.6e}")
    print(f"final relative traj. error:  {relative_error:.6e}")

    if direct_t is not None:
        print(
            f"rough estimate error:        "
            f"{dominant_estimate-direct_t:+.2f} steps"
        )

    print("eigenvalues:")
    for z in eigvals:
        print(
            f"  {z.real:+.9f}{z.imag:+.9f}j "
            f"|λ|={abs(z):.9f}"
        )

print()
print("=" * 78)
print("INTERPRETATION")
print("=" * 78)
print("1. direct == matrix crossing validates the affine reconstruction.")
print("2. rho > 1 predicts asymptotic instability.")
print("3. The crude rho-only estimate ignores eigenvector projection and")
print("   constant forcing, so it is NOT expected to hit the exact step.")
print("4. If spectral-radius ordering tracks explosion ordering, the")
print("   eigenstructure explains the relative instability.")
