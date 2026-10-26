"""
run_benchmarks.py
-----------------
Comprehensive Benchmark Suite for Track A (Continuous Optimization).

Executes:
  1. Multi-Optimizer Comparison across 4 Landscapes:
     - Convex Quadratic
     - Strongly Convex Quadratic
     - Non-Convex Saddle Landscape (with Saddle Point and Minima)
     - Noisy Objective
  2. 10-Seed Repeated Runs for Stochastic Methods (SGD, MiniBatch, Noisy Adam)
     reporting mean +/- std for final objective and runtime.
  3. Step-Size Sensitivity Sweep across learning rates [1e-4, 1e-3, 1e-2, 1e-1, 0.5, 1.0, 2.0].
  4. Gauss-Newton evaluation on non-linear least squares residuals.
  5. Generates publication-grade convergence and sensitivity plots.
"""

import os
import sys
import time
import json
from typing import Dict, List, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt

# Bootstrap repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_A_continuous.code.optimizers import (
    GradientDescent,
    SGD,
    MiniBatchSGD,
    Momentum,
    NAG,
    AdaGrad,
    RMSProp,
    Adam,
    NewtonRaphson,
    GaussNewton,
)
from track_A_continuous.code.landscapes import (
    ConvexQuadratic,
    StronglyConvexQuadratic,
    NonConvexSaddle,
    NoisyObjective,
    ml_optimization_demo,
    continuous_vs_discrete_demo,
)


def run_optimizer_on_objective(
    opt_name: str,
    optimizer: Any,
    objective: Any,
    theta_init: np.ndarray,
    max_iters: int = 100,
) -> Tuple[List[float], float, np.ndarray]:
    """
    Runs a single optimizer on a specified objective for max_iters steps.
    Returns: (loss_history, wall_clock_ms, final_theta)
    """
    theta = theta_init.copy().astype(float)
    optimizer.reset()
    loss_history = [objective.f(theta)]

    t0 = time.perf_counter()

    for it in range(max_iters):
        if opt_name == "NAG":
            theta, _ = optimizer.step(theta, objective.grad)
        elif opt_name == "NewtonRaphson":
            g = objective.grad(theta)
            H = objective.hessian(theta)
            theta = optimizer.step(theta, g, H)
        else:
            g = objective.grad(theta)
            theta = optimizer.step(theta, g)

        loss_val = objective.f(theta)
        # Guard against explosion / NaN
        if np.isnan(loss_val) or np.isinf(loss_val) or loss_val > 1e8:
            loss_history.append(1e8)
            break
        loss_history.append(loss_val)

    runtime_ms = (time.perf_counter() - t0) * 1000.0
    return loss_history, runtime_ms, theta


def run_gauss_newton_experiment(max_iters: int = 50) -> Dict[str, Any]:
    """
    Evaluates Gauss-Newton on non-linear curve fitting residuals:
      y = a * exp(b * x), residuals r_i(a, b) = y_i - a * exp(b * x_i)
    """
    rng = np.random.RandomState(42)
    x_data = np.linspace(0, 1, 30)
    true_a, true_b = 2.5, 1.2
    y_data = true_a * np.exp(true_b * x_data) + rng.randn(30) * 0.05

    def get_residuals_and_jacobian(theta: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        a, b = theta[0], theta[1]
        y_pred = a * np.exp(b * x_data)
        residuals = y_pred - y_data
        J = np.zeros((len(x_data), 2))
        J[:, 0] = np.exp(b * x_data)          # d/da
        J[:, 1] = a * x_data * np.exp(b * x_data)  # d/db
        return residuals, J

    theta = np.array([1.0, 0.5])  # Starting guess
    gn = GaussNewton(lr=1.0, damping=1e-3)
    history = []

    t0 = time.perf_counter()
    for _ in range(max_iters):
        r, J = get_residuals_and_jacobian(theta)
        loss = 0.5 * np.sum(r ** 2)
        history.append(float(loss))
        theta = gn.step(theta, r, J)

    runtime_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "final_theta": [float(x) for x in theta],
        "true_theta": [true_a, true_b],
        "final_loss": float(history[-1]),
        "loss_history": history,
        "runtime_ms": round(runtime_ms, 3),
    }


def run_full_benchmarks(
    results_dir: str = "track_A_continuous/results",
) -> Dict[str, Any]:
    os.makedirs(results_dir, exist_ok=True)
    print("======================================================================")
    print(" Running Track A Continuous Optimization Benchmark Suite")
    print("======================================================================")

    # 1. Instantiate Objectives
    convex_obj = ConvexQuadratic()
    sconvex_obj = StronglyConvexQuadratic()
    saddle_obj = NonConvexSaddle()
    noisy_obj = NoisyObjective(sconvex_obj, sigma=0.3, seed=42)

    # 2. Configure Optimizers
    optimizers_config = {
        "GD": (GradientDescent, {"lr": 0.05}),
        "SGD": (SGD, {"lr": 0.05}),
        "MiniBatchSGD": (MiniBatchSGD, {"lr": 0.05}),
        "Momentum": (Momentum, {"lr": 0.05, "beta": 0.9}),
        "NAG": (NAG, {"lr": 0.05, "beta": 0.9}),
        "AdaGrad": (AdaGrad, {"lr": 0.3}),
        "RMSProp": (RMSProp, {"lr": 0.05, "gamma": 0.9}),
        "Adam": (Adam, {"lr": 0.08, "beta1": 0.9, "beta2": 0.999}),
        "NewtonRaphson": (NewtonRaphson, {"lr": 1.0, "damping": 1e-4}),
    }

    # 3. Trajectory Benchmarks on Deterministic Landscapes
    landscapes = {
        "Convex_Quadratic": (convex_obj, np.array([4.0, 4.0])),
        "Strongly_Convex": (sconvex_obj, np.array([3.0, 3.0])),
        "NonConvex_Saddle": (saddle_obj, np.array([0.1, 0.01])), # near saddle
    }

    landscape_results = {}

    for land_name, (obj, init_pos) in landscapes.items():
        landscape_results[land_name] = {}
        print(f"\n[Benchmarking] Landscape: {land_name} (Initial position: {init_pos})")
        for opt_name, (OptClass, kwargs) in optimizers_config.items():
            opt = OptClass(**kwargs)
            hist, runtime_ms, final_th = run_optimizer_on_objective(
                opt_name, opt, obj, init_pos, max_iters=100
            )
            landscape_results[land_name][opt_name] = {
                "initial_loss": hist[0],
                "final_loss": round(hist[-1], 6),
                "runtime_ms": round(runtime_ms, 3),
                "loss_history": hist,
                "final_theta": [round(float(x), 4) for x in final_th],
            }
            print(f"  {opt_name:<15}: Final Loss={hist[-1]:>10.5f} | Runtime={runtime_ms:>6.2f} ms")

    # 4. Stochastic Methods: 10 Repeated Runs (Mean +/- Std)
    print("\n[Benchmarking] Stochastic Methods on Noisy Objective (10 Runs, Seeds 0..9)...")
    stochastic_opts = ["SGD", "MiniBatchSGD", "Adam"]
    stochastic_summary = {}

    for opt_name in stochastic_opts:
        OptClass, kwargs = optimizers_config[opt_name]
        runs_final_loss = []
        runs_runtime = []

        for seed in range(10):
            noisy_obj.set_seed(seed * 7 + 13)
            opt = OptClass(**kwargs)
            hist, runtime_ms, _ = run_optimizer_on_objective(
                opt_name, opt, noisy_obj, np.array([3.0, 3.0]), max_iters=100
            )
            runs_final_loss.append(hist[-1])
            runs_runtime.append(runtime_ms)

        stochastic_summary[opt_name] = {
            "loss_mean": float(np.mean(runs_final_loss)),
            "loss_std": float(np.std(runs_final_loss)),
            "runtime_mean_ms": float(np.mean(runs_runtime)),
            "runtime_std_ms": float(np.std(runs_runtime)),
            "runs_final_loss": [round(x, 4) for x in runs_final_loss],
        }
        print(f"  {opt_name:<15}: Loss={np.mean(runs_final_loss):.4f} ± {np.std(runs_final_loss):.4f} | Time={np.mean(runs_runtime):.2f} ± {np.std(runs_runtime):.2f} ms")

    # 5. Step-Size Sensitivity Sweep
    print("\n[Benchmarking] Learning Rate Sensitivity Sweep...")
    lr_sweep = [1e-4, 1e-3, 1e-2, 0.05, 0.1, 0.5, 1.0, 2.0]
    sweep_opts = ["GD", "Momentum", "Adam", "AdaGrad"]
    sensitivity_results = {m: [] for m in sweep_opts}

    for lr in lr_sweep:
        for opt_name in sweep_opts:
            if opt_name == "GD":
                opt = GradientDescent(lr=lr)
            elif opt_name == "Momentum":
                opt = Momentum(lr=lr, beta=0.9)
            elif opt_name == "Adam":
                opt = Adam(lr=lr)
            elif opt_name == "AdaGrad":
                opt = AdaGrad(lr=lr)

            hist, _, _ = run_optimizer_on_objective(
                opt_name, opt, sconvex_obj, np.array([3.0, 3.0]), max_iters=80
            )
            sensitivity_results[opt_name].append({
                "lr": lr,
                "final_loss": min(hist[-1], 100.0), # cap for plotting
            })

    # 6. Gauss-Newton Residual Experiment
    print("\n[Benchmarking] Gauss-Newton on Non-Linear Least Squares...")
    gn_result = run_gauss_newton_experiment()
    print(f"  Gauss-Newton: True theta=[2.5, 1.2], Estimated={gn_result['final_theta']} | Final Loss={gn_result['final_loss']:.6f}")

    # 7. Generate Plots
    print("\n[Plotting] Generating publication convergence and sensitivity figures...")
    plot_convergence(landscape_results, os.path.join(results_dir, "convergence_trajectories.png"))
    plot_sensitivity(sensitivity_results, lr_sweep, os.path.join(results_dir, "step_size_sensitivity.png"))

    # 8. Save JSON & CSV
    all_data = {
        "metadata": {
            "track": "Track A: Continuous Optimization",
            "hardware_labeled": "[Hardware-Measured]",
            "num_stochastic_seeds": 10,
        },
        "landscapes": landscape_results,
        "stochastic_summary": stochastic_summary,
        "gauss_newton": gn_result,
        "ml_demo": ml_optimization_demo(),
        "discrete_contrast": continuous_vs_discrete_demo(),
    }

    json_path = os.path.join(results_dir, "optimizer_benchmarks.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2)

    csv_path = os.path.join(results_dir, "optimizer_benchmarks_summary.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Landscape,Optimizer,Initial_Loss,Final_Loss,Runtime_ms\n")
        for land, opt_dict in landscape_results.items():
            for opt, res in opt_dict.items():
                f.write(f"{land},{opt},{res['initial_loss']},{res['final_loss']},{res['runtime_ms']}\n")

    print(f"All benchmarks complete. Results saved to {json_path} and {csv_path}")
    return all_data


def plot_convergence(landscape_results: Dict[str, Any], save_path: str):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    titles = [
        ("Convex_Quadratic", "Convex Quadratic (kappa=20)"),
        ("Strongly_Convex", "Strongly Convex (mu=1.58, L=4.41)"),
        ("NonConvex_Saddle", "Non-Convex Saddle Landscape"),
    ]

    for ax, (key, title) in zip(axes, titles):
        opts_data = landscape_results[key]
        for opt_name, res in opts_data.items():
            losses = res["loss_history"]
            # Plot log scale if positive, or shifted
            shifted_losses = [max(1e-6, l - min(res["final_loss"], 0.0) + 1e-4) for l in losses]
            ax.plot(shifted_losses[:60], label=opt_name, linewidth=1.8 if opt_name in ["Adam", "NewtonRaphson"] else 1.2)
        ax.set_yscale("log")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Iteration Step")
        ax.set_ylabel("Loss (log scale)")
        ax.grid(True, linestyle="--", alpha=0.6)
        if key == "NonConvex_Saddle":
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_sensitivity(sensitivity_results: Dict[str, Any], lr_sweep: List[float], save_path: str):
    plt.figure(figsize=(8, 5))
    for opt_name, data in sensitivity_results.items():
        losses = [d["final_loss"] for d in data]
        plt.plot(lr_sweep, losses, marker="o", label=opt_name, linewidth=1.8)

    plt.xscale("log")
    plt.yscale("log")
    plt.title("Step-Size Sensitivity (Learning Rate Sweep on Strongly Convex)", fontsize=13, fontweight="bold")
    plt.xlabel("Learning Rate (eta, log scale)")
    plt.ylabel("Final Loss after 80 steps (log scale)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


if __name__ == "__main__":
    run_full_benchmarks()
