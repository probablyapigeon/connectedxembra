import numpy as np

PERSONALITIES = {
    "COURAGE": {"b": 0.2,  "r": 0.5, "m": 0.3, "k": 0.1},
    "WISDOM":  {"b": 0.4,  "r": 0.2, "m": 0.6, "k": 0.05},
    "POWER":   {"b": -0.1, "r": 0.8, "m": 0.4, "k": -0.2},
}

TARGET = 0.8
THRESHOLD = 1e12

# x_0 = [Psi_0, Psi_-1, theta_0, G_0]
X0 = np.array([-0.1, -0.1, 0.0, 0.0], dtype=float)

# Previous experimentally observed crossing indices.
# Our earlier loops label the first update as t=0, so closed-form
# state x_n should cross at n = observed_index + 1.
OBSERVED = {
    "COURAGE": 104,
    "WISDOM": 141,
    "POWER":   412,
}


def build_system(p):
    b, r, m, k = p["b"], p["r"], p["m"], p["k"]
    a = r + 0.06

    A = np.array([
        [a,       m,   1.0,   0.285],
        [1.0,     0.0, 0.0,   0.0],
        [k*a,     k*m, 1.0+k, k*0.285],
        [0.2,     0.0, 0.0,   0.95],
    ], dtype=float)

    c = np.array([
        b,
        0.0,
        k * (b - TARGET),
        0.0,
    ], dtype=float)

    return A, c


def closed_form_setup(A, c):
    # Fixed point satisfies:
    # x* = A x* + c
    # (I-A)x* = c
    I = np.eye(A.shape[0])
    x_star = np.linalg.solve(I - A, c)

    # A = V diag(lambda) V^-1
    eigvals, V = np.linalg.eig(A)
    V_inv = np.linalg.inv(V)

    # Coordinates of initial displacement in eigenbasis.
    alpha = V_inv @ (X0 - x_star)

    return x_star, eigvals, V, alpha


def state_closed_form(n, x_star, eigvals, V, alpha):
    # x_n = x* + V diag(lambda^n) alpha
    modal = (eigvals ** n) * alpha
    x = x_star.astype(complex) + V @ modal

    # Imaginary residue should only be numerical roundoff.
    imag = float(np.max(np.abs(x.imag)))
    return x.real, imag


print("=" * 78)
print("AGENTIC LONK — CLOSED-FORM EIGENMODE PROPHECY")
print("=" * 78)
print("No update_agent loop.")
print("No x <- A@x+c recurrence.")
print("Each queried state is computed directly from A's eigenmodes.")

for name, p in PERSONALITIES.items():
    A, c = build_system(p)
    x_star, eigvals, V, alpha = closed_form_setup(A, c)

    rho = float(np.max(np.abs(eigvals)))

    first_n = None
    previous_mag = None
    crossing_state = None
    max_imag = 0.0

    # This loop searches integer TIME, but does NOT evolve state recursively.
    for n in range(0, 2001):
        x, imag = state_closed_form(
            n, x_star, eigvals, V, alpha
        )

        max_imag = max(max_imag, imag)
        mag = float(np.max(np.abs(x)))

        if mag > THRESHOLD:
            first_n = n
            crossing_state = x
            break

        previous_mag = mag

    predicted_index = (
        first_n - 1 if first_n is not None else None
    )

    print()
    print(name)
    print("-" * 78)
    print(f"spectral radius:             {rho:.12f}")
    print(f"affine fixed point x*:       {x_star}")
    print(f"closed-form crossing n:      {first_n}")
    print(f"equivalent old loop index:   {predicted_index}")
    print(f"observed old loop index:     {OBSERVED[name]}")
    print(
        f"EXACT CROSSING MATCH:         "
        f"{predicted_index == OBSERVED[name]}"
    )

    if first_n is not None:
        print(f"|x_(n-1)|_inf:               {previous_mag:.6e}")
        print(
            f"|x_n|_inf:                   "
            f"{np.max(np.abs(crossing_state)):.6e}"
        )
        print(f"x_n:                         {crossing_state}")

    print(f"max imaginary roundoff:      {max_imag:.3e}")

    print("modal coefficients:")
    for lam, coeff in zip(eigvals, alpha):
        print(
            f"  λ={lam.real:+.9f}{lam.imag:+.9f}j "
            f"|λ|={abs(lam):.9f} "
            f"alpha={coeff.real:+.6e}{coeff.imag:+.6e}j"
        )

print()
print("=" * 78)
print("PASS CONDITION")
print("=" * 78)
print("COURAGE -> 104")
print("WISDOM  -> 141")
print("POWER   -> 412")
print()
print("If all three exact matches are True, the threshold crossings")
print("are recoverable directly from the affine eigenmode solution.")
