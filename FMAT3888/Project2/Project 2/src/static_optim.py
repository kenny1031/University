import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# ================================================================
# 1. OPTIMISATION ENGINE
# ================================================================
class StaticPortfolioOptimizer:
    def __init__(self, mu, Sigma, phi, r_f):
        """
        mu: np.ndarray (expected returns, N)
        Sigma: np.ndarray (covariance, NxN)
        phi: float (exposure to risky assets)
        r_f: float (risk-free rate, monthly)
        """
        self.mu = np.asarray(mu, float).ravel()
        self.Sigma = 0.5 * (Sigma + Sigma.T)
        self.phi = phi
        self.r_f = r_f
        self.N = len(self.mu)

    # ------------------------------------------------------------
    def optimise_growth_bucket(
        self,
        r_target,
        L=None,
        U=None,
        tol=1e-8
    ):
        """
        Optimise risky-asset weights w_G subject to:
            sum(w) = 1
            mu'w >= r_req
            L <= w <= U
        Where r_req is adjusted by phi and risk-free rate.
        """
        mu, S, N, phi, r_f = self.mu, self.Sigma, self.N, self.phi, self.r_f

        # required risky bucket target
        r_req = (r_target - (1.0 - phi) * r_f) / phi

        if L is None:
            L = -np.inf * np.ones(N)
        if U is None:
            U = np.inf * np.ones(N)
        bounds = list(zip(L, U))

        cons = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "ineq", "fun": lambda w: float(mu @ w - r_req)}
        ]

        def obj(w):
            return 0.5 * float(w @ S @ w)

        w0 = np.ones(N) / N
        res = minimize(
            obj, w0,
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"ftol": 1e-9, "maxiter": 2000, "disp": False}
        )
        w = res.x
        active = (mu @ w - r_req) <= max(tol, tol * abs(r_req))
        return w, active

    # ------------------------------------------------------------
    def combine_with_cash(self, w_G):
        """Return full portfolio with cash included."""
        w_full = np.concatenate([[1 - self.phi], self.phi * w_G])
        return w_full


# ================================================================
# 2. EFFICIENT FRONTIER + RISK VS CASH PLOTS
# ================================================================
class EfficientFrontierPlotter:
    @staticmethod
    def plot_with_cash_only(
        mu: np.ndarray,
        Sigma: np.ndarray,
        phi: float,
        r_f: float,
        r_target: float,
        n_samples: int=10000,
        seed: int=42,
        w: np.array=None,
        short_cap: float=0.3,
        ef_points: int=120,
        max_trials_factor: int=50,
        title: str="Efficient Frontier: risk vs cash-transformed"
    ) -> None:
        """
        Same code as your original plot_with_cash_only(),
        but converted into staticmethod inside the class.
        """
        rng = np.random.default_rng(seed)
        mu = np.asarray(mu, float).ravel()
        Sigma = np.asarray(Sigma, float)
        n = len(mu)
        # ------------------- helper -------------------
        def project_sum1_and_cap(w0, cap):
            shift = (1.0 - w0.sum()) / n
            w = w0 + shift
            for _ in range(6):
                if np.all(np.abs(w) <= cap) and np.isclose(w.sum(), 1.0, atol=1e-8):
                    break
                w = np.clip(w, -cap, cap)
                shift = (1.0 - w.sum()) / n
                w += shift
            return w

        # ------------------- sample feasible weights -------------------
        W = []
        trials = 0
        max_trials = int(max_trials_factor * n_samples)

        while len(W) < n_samples and trials < max_trials:
            trials += 1
            w0 = rng.uniform(-short_cap, short_cap, n)
            w_feas = project_sum1_and_cap(w0, short_cap)
            if np.all(np.abs(w_feas) <= short_cap) and np.isclose(w_feas.sum(), 1.0, atol=1e-6):
                W.append(w_feas)

        W = np.asarray(W)

        # ------------------- risk-space cloud -------------------
        mu_G_sim = W @ mu
        sigma_G_sim = np.sqrt(np.einsum('ij,jk,ik->i', W, Sigma, W))

        # ------------------- efficient frontier (risk space) -------------------
        bounds = [(-short_cap, short_cap)] * n
        mu_targets = np.linspace(mu.min(), mu.max(), ef_points)
        mu_G_vals, sigma_G_vals = [], []

        def var_obj(w_vec):
            return w_vec @ Sigma @ w_vec

        def project_feas(w0):
            return project_sum1_and_cap(w0, short_cap)

        w0 = project_feas(np.ones(n) / n)

        for mu_t in mu_targets:
            cons = (
                {'type': 'eq', 'fun': lambda ww: np.sum(ww) - 1.0},
                {'type': 'ineq', 'fun': lambda ww, mu_t=mu_t: np.dot(ww, mu) - mu_t}
            )
            res = minimize(
                var_obj, w0,
                method="SLSQP",
                bounds=bounds,
                constraints=cons,
                options={'ftol': 1e-12, 'maxiter': 400}
            )
            if res.success:
                w_opt = res.x
                mu_G_vals.append(float(w_opt @ mu))
                sigma_G_vals.append(float(np.sqrt(w_opt @ Sigma @ w_opt)))
                w0 = w_opt

        mu_G_vals = np.asarray(mu_G_vals)
        sigma_G_vals = np.asarray(sigma_G_vals)

        # ------------------- cash transform -------------------
        mu_T_sim = (1 - phi) * r_f + phi * mu_G_sim
        sigma_T_sim = phi * sigma_G_sim
        mu_T_vals = (1 - phi) * r_f + phi * mu_G_vals
        sigma_T_vals = phi * sigma_G_vals

        # ------------------- given portfolio -------------------
        given_risk_pt = given_cash_pt = None
        if w is not None:
            w = np.asarray(w)
            mu_w = float(w @ mu)
            sigma_w = float(np.sqrt(w @ Sigma @ w))
            given_risk_pt = (sigma_w, mu_w)
            given_cash_pt = (phi * sigma_w, (1 - phi) * r_f + phi * mu_w)

        # ------------------- plot -------------------
        plt.figure(figsize=(9.5, 6.6))
        plt.scatter(sigma_G_sim, mu_G_sim, s=6, alpha=0.18, label="Simulated (risk space)")
        if len(mu_G_vals) > 0:
            order_risk = np.argsort(sigma_G_vals)
            plt.plot(sigma_G_vals[order_risk], mu_G_vals[order_risk], lw=2.4, label="Efficient Frontier (risk)")

        # cash
        plt.scatter(sigma_T_sim, mu_T_sim, s=6, alpha=0.25, label="Simulated (cash)")
        if len(mu_T_vals) > 0:
            order_cash = np.argsort(sigma_T_vals)
            plt.plot(sigma_T_vals[order_cash], mu_T_vals[order_cash], lw=2.6, label="Efficient Frontier (cash)")

        if given_risk_pt:
            plt.scatter(*given_risk_pt, marker="*", s=220, label="Given (risk)")
        if given_cash_pt:
            plt.scatter(*given_cash_pt, marker="X", s=140, label="Given (cash)")

        plt.axhline(r_f, ls='--', label="Risk-free")
        plt.axhline(r_target, ls='--', label=f"Target μ={r_target:.4f}")

        plt.xlabel(r"$\sigma$")
        plt.ylabel(r"$\mu$")
        plt.grid(True, ls="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.show()


# ================================================================
# 3. NAV PLOTTING AFTER CUT
# ================================================================
class NAVPlotter:
    @staticmethod
    def plot_after_cut(
        returns, mu_G, w_growth, r_f,
        cut=pd.Timestamp("2021-01-29")
    ):
        """
        Cleaned version of your plot_after_cut_cash_and_1to6().
        """
        cols = returns.columns.tolist()
        returns = returns[[cols[-1]] + cols[:-1][:6]].copy()

        returns = returns.sort_index().apply(pd.to_numeric, errors="coerce")
        returns_post = returns[returns.index >= cut]
        if len(returns_post) == 0:
            raise ValueError("No data after cut.")

        # combine cash + growth assets
        w_full = np.concatenate([[1 - w_growth.sum()], w_growth])

        nv_assets = (1 + returns_post).cumprod() * 100
        r_port = (returns_post * w_full).sum(axis=1)
        nv_port = (1 + r_port).cumprod() * 100
        nv_assets["Optimal Portfolio"] = nv_port

        mu = np.concatenate([[r_f], mu_G])
        exp_monthly = float(w_full @ mu)
        t = np.arange(len(returns_post))
        exp_curve = 100 * (1 + exp_monthly)**t

        plt.figure(figsize=(10, 6))
        for col in returns.columns:
            plt.plot(returns_post.index, nv_assets[col], lw=1.8)

        plt.plot(returns_post.index, nv_port, lw=2.5, label="Optimal Portfolio", color='black')
        plt.plot(returns_post.index, exp_curve, 'r--', lw=3, label="Expected")

        plt.axvline(cut, color='gray', ls='--')
        plt.legend()
        plt.grid(True, ls=':')
        plt.tight_layout()
        plt.show()


# ================================================================
# 4. PHI–UTILITY PLOT
# ================================================================
class PhiUtilityPlotter:
    @staticmethod
    def plot_phi_Z(mu, Sigma, wG, r_f,
                   n_phi=300, range_mult=1.5, gamma=1.0,
                   mark_phis=(0.3, 0.9)):
        """
        Clean version of your CARA utility curve plot.
        """
        mu = np.asarray(mu, float)
        Sigma = np.asarray(Sigma, float)
        wG = np.asarray(wG, float)

        mu_G = float(wG @ mu)
        sigma_G2 = float(wG @ Sigma @ wG)
        sigma_G = np.sqrt(sigma_G2)

        phi_star = (mu_G - r_f) / (gamma * sigma_G2)

        half_width = range_mult * max(1.0, abs(phi_star))
        phi = np.linspace(phi_star - half_width, phi_star + half_width, n_phi)

        Z = -np.exp(-gamma * ((1 - phi) * r_f + phi * mu_G)
                    + 0.5 * (gamma * phi * sigma_G)**2)

        plt.figure(figsize=(7.5, 5))
        plt.plot(phi, Z, lw=2)

        Z_star = -np.exp(-gamma * ((1 - phi_star) * r_f + phi_star * mu_G)
                         + 0.5 * (gamma * phi_star * sigma_G)**2)
        plt.scatter([phi_star], [Z_star], s=120, marker='*', color='red')

        plt.xlabel("φ")
        plt.ylabel("Utility")
        plt.grid(True)
        plt.tight_layout()
        plt.show()


# ================================================================
# 5. RISK & CASH CLOUDS WITH ISO-LINES
# ================================================================
class RiskCloudPlotter:
    @staticmethod
    def plot(
        mu, Sigma, phi, r_f, r_target,
        n_samples=15000, seed=42, w=None,
        short_cap=0.3, gamma=1.0,
        sharpe_levels=(0.14, 0.12, 0.10),
        cara_constants=(-0.00619, -0.00549, -0.005)
    ):
        """
        Cleaned version of your plot_risk_and_cash_clouds_with_iso().
        """
        # --- identical logic preserved ---
        mu = np.asarray(mu)
        Sigma = np.asarray(Sigma)
        n = len(mu)

        rng = np.random.default_rng(seed)

        # helper
        def project_sum1_and_cap(w0):
            shift = (1 - w0.sum()) / n
            w = w0 + shift
            for _ in range(6):
                if np.all(np.abs(w) <= short_cap) and np.isclose(w.sum(), 1, atol=1e-8):
                    break
                w = np.clip(w, -short_cap, short_cap)
                shift = (1 - w.sum()) / n
                w += shift
            return w

        # sample
        W = []
        while len(W) < n_samples:
            w0 = rng.uniform(-short_cap, short_cap, n)
            w_feas = project_sum1_and_cap(w0)
            if np.all(np.abs(w_feas) <= short_cap):
                W.append(w_feas)

        W = np.asarray(W)

        mu_G_sim = W @ mu
        sigma_G_sim = np.sqrt(np.einsum('ij,jk,ik->i', W, Sigma, W))

        mu_T_sim = (1 - phi) * r_f + phi * mu_G_sim
        sigma_T_sim = phi * sigma_G_sim

        # ---------------- plot ----------------
        plt.figure(figsize=(9.2, 6.6))

        plt.scatter(sigma_G_sim, mu_G_sim, s=6, alpha=0.18, label="Risk space")
        plt.scatter(sigma_T_sim, mu_T_sim, s=6, alpha=0.28, label="Cash space")

        sig_grid = np.linspace(min(sigma_G_sim), max(sigma_G_sim), 400)

        # iso-Sharpe
        for S in sharpe_levels:
            plt.plot(sig_grid, r_f + S * sig_grid, ls='--', label=f"Sharpe S={S}")

        # iso-CARA
        for C in cara_constants:
            mu_cara = 0.5 * gamma * sig_grid**2 - (C / gamma)
            plt.plot(sig_grid, mu_cara, label=f"CARA C={C}")

        plt.axhline(r_f, ls='--')
        plt.axhline(r_target, ls='--')

        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()