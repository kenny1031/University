import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import statsmodels.api as sm
import torch
import torch.nn as nn
from torch.optim.lr_scheduler import ReduceLROnPlateau
import os
import matplotlib.pyplot as plt
import math
from typing import Dict

# Configuration
DATA_PATH = "../data/cleaned/monthly_returns.csv"
OUTPUT_DIR = "../parameters"

# Modified from: https://www.sciencedirect.com/science/article/pii/S2214635019302333
# Network Architecture
class AutoEncoder(nn.Module):
    def __init__(self, n_features: int, latent_dim: int=10):
        super().__init__()
        # Encoder block
        self.encoder = nn.Sequential(
            nn.Linear(n_features, 128),
            nn.BatchNorm1d(128),
            nn.Dropout(0.1),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, latent_dim)
        )
        self.encoder.add_module(
            "final_norm",
            nn.BatchNorm1d(latent_dim)
        )
        # Decoder block
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Linear(128, n_features)
        )

    def forward(self, x):
        z = self.encoder(x)
        reconstructed = self.decoder(z)
        return reconstructed, z

def train_autoencoder(
    data_tensor: torch.tensor,
    epochs: int=500,
    lr: float=1e-3,
    latent_dim: int=10
) -> AutoEncoder:
    """Training function for autoencoder"""
    n_features = data_tensor.shape[1]
    model = AutoEncoder(n_features, latent_dim)
    criterion = nn.MSELoss()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = ReduceLROnPlateau(optimiser, mode='min', patience=15, factor=0.8)
    for epoch in range(epochs):
        optimiser.zero_grad()
        recon, _ = model(data_tensor)  # After reconstruction loss:
        pred_returns = model.decoder(model.encoder(data_tensor))
        loss_recon = criterion(pred_returns, data_tensor)

        # auxiliary term: correlation between latent factors and returns
        z = model.encoder(data_tensor)
        reg_term = torch.mean((torch.matmul(z, z.T)-torch.matmul(data_tensor, data_tensor.T))**2)

        loss = loss_recon + 0.1 * reg_term
        loss.backward()
        optimiser.step()
        scheduler.step(loss.item())
        if (epoch + 1) % 100 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}] | Loss: {loss.item():.6f}")

    return model



#---------------------------------------------------------------
# Latent factors Autoencoder
#---------------------------------------------------------------
class LatentAutoencoder:
    def __init__(
        self,
        data_path: str=DATA_PATH,
        output_dir: str=OUTPUT_DIR,
        figure_path: str=None
    ) -> None:
        self.data = pd.read_csv(data_path, index_col=0).astype(float).iloc[:,:6]
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self.data.index = pd.to_datetime(self.data.index)
        self.data_train = self.data.loc[
            self.data.index < pd.Timestamp("2021-01-29")
        ]
        self.data_test = self.data.loc[
            self.data.index >= pd.Timestamp("2021-01-29")
        ]
        self.latent_df = None
        self.mu_latent = None
        self.r2_latent = None
        self.Sigma_latent = None
        self.figure_path = figure_path
        if self.figure_path is not None:
            os.makedirs(figure_path, exist_ok=True)

    def estimate_parameters(self):
        self.rolling_window_estimation()
        self.estimate_mu(data=self.data_train)
        self.Sigma_latent = self.estimate_Sigma(data=self.data_train)
        self.latent_df.to_csv(os.path.join(self.output_dir, "latent_df.csv"))
        self.mu_latent.to_csv(os.path.join(self.output_dir, "mu_latent.csv"))
        self.r2_latent.to_csv(os.path.join(self.output_dir, "r2_latent.csv"))
        pd.DataFrame(self.Sigma_latent).to_csv(
            os.path.join(
                self.output_dir,
                "Sigma_latent.csv"
            )
        )
        print(f"Saved parameters to {self.output_dir}")

    def rolling_window_estimation(
        self,
        window: int=120,
        test_period: int=21,
        latent_dim: int=10
    ) -> None:
        print("===Running Factors Autoencoder===")
        numeric_returns = np.array(self.data_train)
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(numeric_returns)
        returns_tensor = torch.tensor(data_scaled, dtype=torch.float32)
        latent_factors = []
        i = 0

        for t in range(window, len(returns_tensor), test_period):
            print(f"===Window {i + 1}===")
            i += 1
            train_data = returns_tensor[t - window:t]
            model = train_autoencoder(
                train_data,
                epochs=500,
                lr=1e-3,
                latent_dim=latent_dim
            )
            with torch.no_grad():
                z_train = model.encoder(train_data)
                latent_factors.append(z_train.numpy())

        # Flatten across all windows
        latent_matrix = np.vstack(latent_factors)
        # Create DataFrame
        self.latent_df = pd.DataFrame(
            latent_matrix,
            columns=[f"Factor{i + 1}" for i in range(latent_matrix.shape[1])]
        )
        print("Latent factors estimated")

    def estimate_mu(self, data: pd.DataFrame):
        if self.latent_df is None:
            raise ValueError("Latent factors not estimated, call rolling_window_estimation")
        numeric_returns = np.array(data)

        min_len = min(len(numeric_returns), len(self.latent_df))
        numeric_returns = numeric_returns[:min_len]
        latent_df = self.latent_df.iloc[:min_len]

        T, N = numeric_returns.shape
        K = latent_df.shape[1]

        # Estimate factor loadings for each asset
        betas = np.zeros((N, K))
        for i in range(N):
            model = LinearRegression().fit(latent_df.values, numeric_returns[:, i])
            betas[i, :] = model.coef_

        # Cross-sectional regression on average returns
        mean_returns = numeric_returns.mean(axis=0)
        model_cs = LinearRegression()
        model_cs.fit(betas, mean_returns)
        # Predicted mean returns for each asset (mu_hat)
        predicted_mu = model_cs.predict(betas)

        # Compute per-asset R^2 by refitting each time-series model
        r2_assets = []
        for i in range(numeric_returns.shape[1]):
            model = LinearRegression().fit(latent_df.values, numeric_returns[:, i])
            preds = model.predict(latent_df.values)
            r2_assets.append(r2_score(numeric_returns[:, i], preds))

        self.mu_latent = pd.DataFrame(
            predicted_mu, 
            index=self.data.columns, 
            columns=["mu_latent"]
        )
        self.r2_latent = pd.DataFrame(
            r2_assets, 
            index=self.data.columns, 
            columns=["r2_latent"]
        )
        print("Expected returns estimated")
        print("R2 scores generated")
        return predicted_mu

    def estimate_Sigma(
        self,
        data: pd.DataFrame | np.ndarray,
        k: int=1, tau=0.75):
        """
        Sample mean and PCA-based covariance estimation
        k : number of principal components to keep
        tau : cumulative explained variance threshold (if k=None)
        """
        R = np.asarray(data.T, float)
        p, n = R.shape

        if self.mu_latent is not None:
            mu = self.mu_latent.to_numpy().flatten()
            assert len(mu) == p, "mu_latent length must match number of assets"
        else:
            mu = R.mean(axis=1)  # fallback
            print("Warning: mu_latent not found, using sample mean instead.")
        # demeaned data
        Y = R - mu[:, None]

        # PCA decomposition on covariance matrix
        pca = PCA()
        pca.fit(Y.T)  # sklearn expects features=assets, samples=time, so transpose
        # explained variance and components
        s2 = pca.explained_variance_
        H = pca.components_.T * np.sqrt(s2)

        # choose number of components
        cvar = np.cumsum(pca.explained_variance_ratio_)
        if k is None:
            advised_k = np.searchsorted(cvar, tau) + 1
        else:
            advised_k = int(k)
        advised_k = min(advised_k, p)

        # construct PCA covariance: Sigma = H Hᵀ + Δ
        Hk = H[:, :advised_k]
        S_hat = np.cov(Y, bias=True)
        N = S_hat - Hk @ Hk.T
        Delta = np.diag(np.clip(np.diag(N), 0, None))
        # Sigma_pca = Hk @ Hk.T + Delta
        Sigma_pca = 0.5 * ((H @ H.T + Delta) + (H @ H.T + Delta).T)
        print("Covariance matrix estimated")
        return Sigma_pca

    def visualise_parameters(self, asset_labels: None=None, growth_flag: bool=False)->None:
        """
        Visualise given mu and Sigma side-by-side.
        Left: Sigma heatmap (scaled by 1e4, with values shown)
        Right: Pie chart for mu values.
        """
        mu, Sigma = self.mu_latent, self.Sigma_latent
        if growth_flag:
            mu, Sigma = self.mu_latent.iloc[:6], self.Sigma_latent[:6, :6]

        mu = mu.to_numpy().flatten()
        if asset_labels is None:
            asset_labels = self.data.columns
        if mu is None or Sigma is None:
            raise ValueError("Must call estimate before visualising parameters")
        p = len(mu)
        assert Sigma.shape == (p, p), "Cov matrix dimension must match length of expecte returns"

        labels = asset_labels if (asset_labels is not None and len(asset_labels) == p) \
            else [f"A{i + 1}" for i in range(p)]

        # === Scale Sigma ===
        scale_factor = 1e4
        Sigma_scaled = Sigma * scale_factor

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

        # --- Left: Heatmap ---
        im = ax1.imshow(Sigma_scaled, cmap='viridis', interpolation='none')
        ax1.set_title("$\Sigma$ ($10^{{-4}}$)")
        ax1.set_xticks(range(p))
        ax1.set_xticklabels(labels, rotation=45, ha='right')
        ax1.set_yticks(range(p))
        ax1.set_yticklabels(labels)

        # Add numeric labels (two decimal places)
        for i in range(p):
            for j in range(p):
                val = Sigma_scaled[i, j]
                ax1.text(
                    j, i, f"{val:.2f}",
                    ha="center",
                    va="center",
                    color="w",
                    fontsize=8
                )

        cbar = fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
        cbar.set_label("Covariance $10e-4$")

        # --- Right: Pie chart for mu ---
        ax2.pie(np.abs(mu), labels=[f"{l}\n({v:.4f})" for l, v in zip(labels, mu)],
                startangle=90, counterclock=False)
        ax2.set_title("$\mu$ (True Values)")

        plt.tight_layout()
        if self.figure_path is not None:
            save_path = os.path.join(self.figure_path, "params_visual.png")
            fig.savefig(save_path,
                        dpi=200,
                        bbox_inches="tight")
            print(f"Figure saved to {self.figure_path}")
        plt.show()

    def plot_nav_mu_growth(
        self,
        cut_date: str = "2021-01-29",
        start_nav: float = 100.0
    ):
        """
        Plot actual NAV vs. predicted mean-return (μ_latent) trajectories
        for all assets, using the autoencoder-estimated μ from estimate_mu().
        """
        if self.mu_latent is None:
            raise ValueError("Run estimate_mu() first to compute predicted μ.")
        if not hasattr(self, "data_train") or self.data_train is None:
            raise ValueError("Training data not loaded (self.data_train missing).")

        cut = pd.Timestamp(cut_date)
        R = self.data.sort_index().apply(pd.to_numeric, errors='coerce').dropna(how='all')
        if R.empty:
            raise ValueError("Input returns DataFrame is empty after cleaning.")

        # Compute cumulative NAV
        NV_all = (1.0 + R).cumprod() * start_nav
        cols = NV_all.columns.tolist()

        # Partition test data (after cut)
        R_test = R.loc[R.index >= cut, cols]
        if R_test.empty:
            raise ValueError(f"No data after {cut_date} to plot NAV trajectories.")

        self.X_test = R_test

        # Use expected returns predicted by Autoencoder model
        mu_pred = self.mu_latent.copy()
        mu_pred = mu_pred.loc[cols].to_numpy().flatten()

        # Plot setup
        n, ncols = len(cols), 3
        nrows = math.ceil(n / ncols)
        fig, axes = plt.subplots(nrows, ncols, figsize=(12, 4.2 * nrows))
        axes = np.atleast_1d(axes).ravel()

        for i, col in enumerate(cols):
            ax = axes[i]
            series = NV_all[col].dropna()
            if series.empty:
                ax.set_title(f"{col} — no data")
                ax.axis("off")
                continue

            # Historical and post-cut series
            hist_to_cut = series.loc[series.index <= cut]
            series_post = series.loc[series.index >= cut]
            if hist_to_cut.empty or series_post.empty:
                ax.set_title(f"{col} — insufficient data")
                ax.axis("off")
                continue

            base_at_cut = hist_to_cut.iloc[-1]
            pred_index = series_post.index
            steps = np.arange(len(pred_index))

            # Actual NAV
            ax.plot(series_post.index, series_post.values, lw=2.2,
                    color='tab:blue', label="Actual NAV")

            # μ-based projection (from model)
            mu_hat = float(self.mu_latent.loc[col, "mu_latent"])
            pred_nav = base_at_cut * (1 + mu_hat) ** steps
            ax.plot(pred_index, pred_nav, lw=1.8, linestyle='--',
                    color='tab:orange', label=f"Predicted μ ({mu_hat:.4f})")

            ax.set_title(col, fontsize=10)
            ax.set_ylabel("Value ($)", fontsize=9)
            ax.grid(True, alpha=0.4)
            ax.legend(loc='best', fontsize=8)

        # Turn off unused panels
        for j in range(i + 1, len(axes)):
            axes[j].axis("off")

        plt.tight_layout()
        plt.tight_layout()
        if self.figure_path is not None:
            save_path = os.path.join(self.figure_path, "nav_vs_mu_predicted.png")
            plt.savefig(save_path, dpi=200, bbox_inches="tight")
            print(f"Saved figure to {save_path}")
        plt.show()

        return self.mu_latent



    def plot_mc_after_cut(
        self,
        w: np.array | list,
        cut_date: str = "2021-01-29",
        mc_paths: int = 300,
        mc_seed: int = 42,
        show_plot: bool = True
    ) -> Dict[str: int, str: float, str: float]:
        """
        Compare true post-cut portfolio NAV vs Monte Carlo simulations
        using autoencoder-predicted μ and training covariance Σ.
        """
        if self.mu_latent is None or self.Sigma_latent is None:
            raise ValueError("Run estimate_parameters() first to compute μ and Σ.")
        if self.data_test is None or len(self.data_test) == 0:
            raise ValueError("Testing data is empty — check your cut date.")

        df = self.data_test.copy()
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        df = df.sort_index()

        # Align to growth assets (assumed 6 risky + 1 cash)
        n_assets = df.shape[1]
        if n_assets < 6:
            raise ValueError("At least 6 risky assets required.")
        df["Cash"] = 0.0  # assume risk-free = 0 return monthly
        df = df[["Cash"] + df.columns[:-1].tolist()]
        df.columns = ["Cash", "1", "2", "3", "4", "5", "6"]

        df_post = df[df.index >= pd.Timestamp(cut_date)]
        if df_post.empty:
            raise ValueError("No data after cut date.")

        # --- Portfolio return path (true NAV) ---
        w_full = np.concatenate([[1 - np.sum(w)], w])  # add cash weight
        r_port = (df_post * w_full).sum(axis=1).dropna()
        nv_true = (1.0 + r_port).cumprod() * 100.0
        n = len(nv_true)
        idx_post = nv_true.index

        # --- Expected return vector μ (from autoencoder) ---
        mu_all = np.concatenate([[0.0], self.mu_latent.iloc[:6, 0].values])
        mu0 = float(w_full @ mu_all)

        # --- Portfolio volatility from training Σ ---
        Sigma = np.asarray(self.Sigma_latent[:6, :6], float)
        sigma0 = float(np.sqrt(w @ Sigma @ w))
        if sigma0 <= 0 or not np.isfinite(sigma0):
            raise ValueError("Invalid σ₀ computed from Σ and w.")

        # --- Monte Carlo simulation ---
        rng = np.random.default_rng(mc_seed)
        shocks = rng.normal(loc=mu0, scale=sigma0, size=(n, mc_paths))
        nv_mc = 100.0 * np.cumprod(1.0 + shocks, axis=0)
        exp_curve = 100.0 * (1.0 + mu0) ** np.arange(n)

        # --- Plot ---
        plt.figure(figsize=(9, 5))
        plt.plot(idx_post, nv_mc, color='0.85', linewidth=0.9, alpha=0.7)
        plt.plot(idx_post, exp_curve, 'r--', linewidth=2.2, 
                 label=f"Expected path ($\mu_0$={mu0:.4f})")
        plt.plot(idx_post, nv_true, color='black', linewidth=2.5, label="True path")
        plt.title(f"Monte Carlo Simulation vs True NAV Path")
        plt.xlabel("Date")
        plt.ylabel("Value ($, start=100)")
        plt.grid(True, linestyle=":", alpha=0.4)
        plt.legend()
        plt.tight_layout()

        if self.figure_path is not None:
            save_path = os.path.join(self.figure_path, "mc_path.png")
            plt.savefig(save_path, dpi=200, bbox_inches="tight")
        if show_plot:
            plt.show()
        else:
            plt.close()

        return {"n": n, "mu0": mu0, "sigma0": sigma0}




    def plot_qq_residuals(self, n_cols: int=3, figsize: tuple=(10, 6)):
        """
        QQ-plots of residuals for each asset's autoencoder-based prediction.
        """
        if self.latent_df is None or self.data_train is None:
            raise ValueError("Run rolling_window_estimation() and estimate_mu() first.")

        # Align length of latent factors and returns
        n = min(len(self.latent_df), len(self.data_train))
        X = self.latent_df.iloc[:n, :].values
        data = self.data_train.iloc[-n:, :]

        asset_names = data.columns
        n_assets = len(asset_names)
        n_rows = int(np.ceil(n_assets / n_cols))

        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten()

        for i, asset_name in enumerate(asset_names):
            y = data[asset_name].values
            preds = LinearRegression().fit(X, y).predict(X)
            residuals = y - preds
            standardized = (residuals - np.mean(residuals)) / np.std(residuals)

            sm.qqplot(standardized, line='45', fit=True, ax=axes[i])
            axes[i].set_title(asset_name, fontsize=9)
            axes[i].set_xlabel("")
            axes[i].set_ylabel("")
            axes[i].grid(alpha=0.3)

        # Turn off any extra axes
        for j in range(i + 1, len(axes)):
            axes[j].axis('off')

        plt.suptitle("QQ Plots of Residuals by Asset", fontsize=12)
        plt.tight_layout(rect=(0, 0, 1, 0.97))
        if self.figure_path is not None:
            save_path = os.path.join(self.figure_path, "qq_residuals.png")
            plt.savefig(save_path, bbox_inches="tight")
        plt.show()

if __name__ == "__main__":
    risk_free_rate = pd.read_csv("../data/cleaned/RF.csv")

    # ---Latent autoencoder---
    #estimator = LatentAutoencoder()
    #estimator.estimate_parameters()
