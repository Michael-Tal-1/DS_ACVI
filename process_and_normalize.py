"""
ACVI Data Processing and Normalization
Computes derived metrics, removes outliers, and normalizes data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple
import json


class ACVIDataProcessor:
    def __init__(
        self,
        input_dir: str = "acvi_global_dataset_parallel",
        output_dir: str = "acvi_processed_data",
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.base_parameters = [
            "T2M",
            "T2M_RANGE",
            "T2M_MIN",
            "T2M_MAX",
            "PRECTOTCORR",
            "GWETROOT",
            "EVPTRNS",
            "RH2M",
            "WS10M_MAX",
            "ALLSKY_SFC_SW_DWN",
        ]

        self.normalization_params = {}

    def load_location_data(self, location_path: Path) -> pd.DataFrame:
        csv_files = list(location_path.glob("*.csv"))
        if not csv_files:
            return None

        df = pd.read_csv(csv_files[0], index_col=0, parse_dates=True)
        return df

    def remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()

        physical_limits = {
            "T2M": (-60, 60),
            "T2M_RANGE": (0, 50),
            "T2M_MIN": (-70, 55),
            "T2M_MAX": (-50, 70),
            "PRECTOTCORR": (0, 500),
            "GWETROOT": (0, 1),
            "EVPTRNS": (0, 20),
            "RH2M": (0, 100),
            "WS10M_MAX": (0, 60),
            "ALLSKY_SFC_SW_DWN": (0, 50),
        }

        for param in self.base_parameters:
            if param not in df_clean.columns or param not in physical_limits:
                continue

            lower_bound, upper_bound = physical_limits[param]

            df_clean.loc[
                (df_clean[param] < lower_bound)
                | (df_clean[param] > upper_bound),
                param,
            ] = np.nan

        return df_clean

    def compute_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df_derived = df.copy()

        if "T2M" in df.columns:
            base_temp = 10.0
            df_derived["GDD"] = df["T2M"].apply(
                lambda x: max(0, x - base_temp)
            )

        if "T2M" in df.columns and "RH2M" in df.columns:
            T = df["T2M"]
            RH = df["RH2M"]

            es = 0.6108 * np.exp((17.27 * T) / (T + 237.3))
            ea = (RH / 100.0) * es
            df_derived["VPD"] = es - ea

        if "PRECTOTCORR" in df.columns:
            df_derived["DRY_DAYS"] = (df["PRECTOTCORR"] < 1.0).astype(int)

            dry_spell_length = []
            current_spell = 0
            for is_dry in df_derived["DRY_DAYS"]:
                if is_dry:
                    current_spell += 1
                else:
                    current_spell = 0
                dry_spell_length.append(current_spell)

            df_derived["DRY_SPELL_LENGTH"] = dry_spell_length

        if "T2M_MAX" in df.columns:
            heat_threshold = 30.0
            df_derived["HEAT_DAYS"] = (df["T2M_MAX"] > heat_threshold).astype(
                int
            )

        if "T2M_MIN" in df.columns:
            frost_threshold = 0.0
            df_derived["FROST_DAYS"] = (
                df["T2M_MIN"] < frost_threshold
            ).astype(int)

        return df_derived

    def compute_global_normalization_params(
        self, all_data: Dict[str, pd.DataFrame]
    ) -> Dict:
        print("Computing global normalization parameters...")

        all_params = set()
        for df in all_data.values():
            all_params.update(df.columns)

        norm_params = {}

        for param in all_params:
            all_values = []
            for df in all_data.values():
                if param in df.columns:
                    values = df[param].dropna().values
                    all_values.extend(values)

            if len(all_values) == 0:
                continue

            all_values = np.array(all_values)

            norm_params[param] = {
                "mean": float(np.mean(all_values)),
                "std": float(np.std(all_values)),
                "min": float(np.min(all_values)),
                "max": float(np.max(all_values)),
                "median": float(np.median(all_values)),
                "q25": float(np.percentile(all_values, 25)),
                "q75": float(np.percentile(all_values, 75)),
            }

        return norm_params

    def normalize_data(
        self, df: pd.DataFrame, method: str = "zscore"
    ) -> pd.DataFrame:
        df_norm = df.copy()

        for param in df_norm.columns:
            if param not in self.normalization_params:
                continue

            params = self.normalization_params[param]

            if method == "zscore":
                if params["std"] > 0:
                    df_norm[f"{param}_norm"] = (
                        df_norm[param] - params["mean"]
                    ) / params["std"]

            elif method == "minmax":
                range_val = params["max"] - params["min"]
                if range_val > 0:
                    df_norm[f"{param}_norm"] = (
                        df_norm[param] - params["min"]
                    ) / range_val

            elif method == "robust":
                IQR = params["q75"] - params["q25"]
                if IQR > 0:
                    df_norm[f"{param}_norm"] = (
                        df_norm[param] - params["median"]
                    ) / IQR

        return df_norm

    def process_single_location(
        self, location_name: str, location_path: Path
    ) -> Tuple[str, pd.DataFrame]:
        df = self.load_location_data(location_path)
        if df is None:
            return None

        df = self.remove_outliers(df)
        df = self.compute_derived_metrics(df)

        return (location_name, df)

    def process_all_locations(self):
        print("Loading and processing all locations...")
        processed_data = {}

        for location_dir in self.input_dir.iterdir():
            if not location_dir.is_dir():
                continue

            location_name = location_dir.name
            result = self.process_single_location(location_name, location_dir)

            if result:
                name, df = result
                processed_data[name] = df
                print(f"  Processed: {name}")

        self.normalization_params = self.compute_global_normalization_params(
            processed_data
        )

        print("\nNormalizing data (z-score)...")
        normalized_data = {}
        for location, df in processed_data.items():
            df_norm = self.normalize_data(df, method="zscore")
            normalized_data[location] = df_norm

        self.save_processed_data(normalized_data)
        self.save_normalization_params()

        print(f"\nProcessing complete. Data saved to '{self.output_dir}'")

    def save_processed_data(self, data: Dict[str, pd.DataFrame]):
        for location, df in data.items():
            location_dir = self.output_dir / location
            location_dir.mkdir(exist_ok=True)

            filename = f"processed_{location}.csv"
            filepath = location_dir / filename

            df.to_csv(filepath)

    def save_normalization_params(self):
        params_file = self.output_dir / "normalization_params.json"

        with open(params_file, "w") as f:
            json.dump(self.normalization_params, f, indent=2)


if __name__ == "__main__":
    processor = ACVIDataProcessor(
        input_dir="acvi_global_dataset_parallel",
        output_dir="acvi_processed_data",
    )
    processor.process_all_locations()
