"""
test_continuous_optimizers.py
-----------------------------
Unit Test Suite for Track A (Continuous Optimization).

Tests:
  1. Finite-Difference Gradient Check for Hand-Derived Neural Network Backpropagation.
  2. Convergence of Gradient Descent, Adam, and Newton-Raphson to Known Analytical Minima.
  3. Hessian-Vector Product (HVP) Accuracy against Explicit Numerical Hessian.
  4. Positive Semi-Definiteness of Empirical Fisher Information Matrix.
  5. Convergence of Gauss-Newton on Non-Linear Residuals.
"""

import numpy as np
import pytest

from track_A_continuous.code.optimizers import (
    GradientDescent,
    Adam,
    NewtonRaphson,
    GaussNewton,
)
from track_A_continuous.code.neural_net_backprop import (
    SmallMLP,
    verify_gradient,
    hessian_vector_product,
    full_hessian_numerical,
    empirical_fisher_matrix,
    low_rank_curvature_approximation,
)
from track_A_continuous.code.landscapes import (
    StronglyConvexQuadratic,
    NonConvexSaddle,
)


def test_hand_derived_backprop_against_finite_differences():
    """
    Verifies that the hand-derived analytical backprop gradients
    match numerical finite differences within relative error < 1e-5.
    """
    rng = np.random.RandomState(42)
    X = rng.randn(10, 2)
    y = rng.randn(10, 1)

    mlp = SmallMLP(d_in=2, d_hidden=4, d_out=1, seed=42)
    is_valid, rel_error = verify_gradient(mlp, X, y, tol=1e-5)

    assert is_valid, f"Gradient check failed! Relative error = {rel_error:.2e}"
    assert rel_error < 1e-5


def test_known_minimum_strongly_convex_convergence():
    """
    Tests that GD, Adam, and Newton-Raphson converge to the exact known analytical
    minimum x* = [0.0, 1.0], f(x*) = -1.0 on StronglyConvexQuadratic.
    """
    obj = StronglyConvexQuadratic()
    x_init = np.array([5.0, -3.0])

    # 1. Newton-Raphson (should reach exact minimum in 1 step for quadratic)
    newton = NewtonRaphson(lr=1.0, damping=1e-8)
    g = obj.grad(x_init)
    H = obj.hessian(x_init)
    x_newton = newton.step(x_init, g, H)
    np.testing.assert_allclose(x_newton, obj.x_star, atol=1e-5)
    np.testing.assert_allclose(obj.f(x_newton), obj.f_star, atol=1e-5)

    # 2. Gradient Descent (iterative convergence)
    gd = GradientDescent(lr=0.1)
    x_gd = x_init.copy()
    for _ in range(80):
        x_gd = gd.step(x_gd, obj.grad(x_gd))
    np.testing.assert_allclose(x_gd, obj.x_star, atol=1e-3)

    # 3. Adam
    adam = Adam(lr=0.1)
    x_adam = x_init.copy()
    for _ in range(250):
        x_adam = adam.step(x_adam, obj.grad(x_adam))
    np.testing.assert_allclose(x_adam, obj.x_star, atol=1e-2)


def test_hessian_vector_product_accuracy():
    """
    Verifies that directional finite-difference HVP matches H @ v.
    """
    rng = np.random.RandomState(42)
    X = rng.randn(5, 2)
    y = rng.randn(5, 1)
    mlp = SmallMLP(d_in=2, d_hidden=3, d_out=1, seed=123)

    P = len(mlp.get_params_flat())
    v = rng.randn(P)
    v /= np.linalg.norm(v)  # Unit vector

    hvp = hessian_vector_product(mlp, X, y, v, eps=1e-5)
    H_full = full_hessian_numerical(mlp, X, y)
    exact_hv = H_full @ v

    rel_error = np.linalg.norm(hvp - exact_hv) / (np.linalg.norm(exact_hv) + 1e-10)
    assert rel_error < 1e-3, f"HVP mismatch! Relative error = {rel_error:.2e}"


def test_fisher_matrix_positive_semidefinite():
    """
    Verifies that the empirical Fisher information matrix F is symmetric positive semi-definite.
    """
    rng = np.random.RandomState(42)
    X = rng.randn(8, 2)
    y = rng.randn(8, 1)
    mlp = SmallMLP(d_in=2, d_hidden=3, d_out=1, seed=99)

    F = empirical_fisher_matrix(mlp, X, y)
    evals = np.linalg.eigvalsh(F)

    # All eigenvalues of F must be non-negative (within floating point precision)
    assert np.all(evals >= -1e-8), f"Negative eigenvalues found in Fisher matrix: {evals[evals < 0]}"


def test_gauss_newton_nonlinear_residuals():
    """
    Verifies that Gauss-Newton successfully minimizes non-linear least squares residuals.
    """
    rng = np.random.RandomState(42)
    x_pts = np.linspace(0, 1, 15)
    y_true = 3.0 * np.exp(0.5 * x_pts)

    def get_res_and_jac(theta):
        a, b = theta[0], theta[1]
        r = a * np.exp(b * x_pts) - y_true
        J = np.zeros((len(x_pts), 2))
        J[:, 0] = np.exp(b * x_pts)
        J[:, 1] = a * x_pts * np.exp(b * x_pts)
        return r, J

    theta = np.array([1.5, 0.1])
    gn = GaussNewton(lr=1.0, damping=1e-4)

    for _ in range(25):
        r, J = get_res_and_jac(theta)
        theta = gn.step(theta, r, J)

    r_final, _ = get_res_and_jac(theta)
    loss_final = 0.5 * np.sum(r_final ** 2)
    assert loss_final < 1e-6, f"Gauss-Newton failed to converge, final loss = {loss_final}"
    np.testing.assert_allclose(theta, [3.0, 0.5], atol=1e-3)
