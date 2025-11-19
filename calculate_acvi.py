"""
Agro-Climatic Volatility Index (ACVI) Calculation
Computes ACVI for each location based on processed climate data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import json
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ACVICalculator:
    def __init__(
        self,
        input_dir: str = "acvi_processed_data",
        growing_season: Optional[Tuple[int, int]] = None,
        crop_type: str = "wheat",
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path("acvi_results")
        self.output_dir.mkdir(exist_ok=True)

        self.core_parameters = [
            "T2M",
            "T2M_RANGE",
            "PRECTOTCORR",
            "GWETROOT",
            "EVPTRNS",
            "RH2M",
            "WS10M_MAX",
            "ALLSKY_SFC_SW_DWN",
        ]

        self.derived_parameters = [
            "GDD",
            "VPD",
            "DRY_SPELL_LENGTH",
            "HEAT_DAYS",
            "FROST_DAYS",
        ]

        self.weights = {
            "temperature_volatility": 0.15,
            "precipitation_volatility": 0.25,
            "moisture_stress": 0.20,
            "extreme_events": 0.40,
        }

        # Growing season (month numbers, e.g., April-September = 4,9)
        # Default to spring-summer for wheat/maize in Northern Hemisphere
        self.growing_season = growing_season or (4, 9)

        # Crop-specific thresholds
        self.crop_type = crop_type
        self.crop_thresholds = {
            "wheat": {
                "heat_stress_temp": 30,  # °C
                "optimal_temp": 20,
                "base_temp": 0,
                "max_temp": 35,
            },
            "maize": {
                "heat_stress_temp": 35,  # °C
                "optimal_temp": 25,
                "base_temp": 10,
                "max_temp": 40,
            },
        }
        self.thresholds = self.crop_thresholds.get(
            crop_type, self.crop_thresholds["wheat"]
        )

    def load_location_data(
        self, location_path: Path
    ) -> Optional[pd.DataFrame]:
        csv_files = list(location_path.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV files found in {location_path}")
            return None

        try:
            df = pd.read_csv(csv_files[0], index_col=0, parse_dates=True)
            return df
        except Exception as e:
            logger.error(f"Error loading {csv_files[0]}: {e}")
            return None

    def filter_growing_season(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter data to growing season months only."""
        if self.growing_season is None:
            return df

        start_month, end_month = self.growing_season
        if start_month <= end_month:
            mask = (df.index.month >= start_month) & (
                df.index.month <= end_month
            )
        else:
            # Handle cases like Oct-Mar (10,3)
            mask = (df.index.month >= start_month) | (
                df.index.month <= end_month
            )

        filtered = df[mask]
        logger.debug(
            f"Filtered to growing season {start_month}-{end_month}: {len(filtered)}/{len(df)} records"
        )
        return filtered

    def validate_input_data(self, df: pd.DataFrame) -> bool:
        """Check data quality before calculation."""
        required_params = ["T2M", "PRECTOTCORR", "GWETROOT"]

        for param in required_params:
            if param not in df.columns:
                logger.warning(f"Missing required parameter: {param}")
                return False

        missing_pct = df[required_params].isna().mean()
        if (missing_pct > 0.3).any():
            logger.warning(f"High missing data: {missing_pct.to_dict()}")
            return False

        return True

    def compute_cv(self, series: pd.Series) -> float:
        mean_val = series.mean()
        if mean_val == 0 or np.isnan(mean_val):
            return 0.0
        return (series.std() / abs(mean_val)) * 100

    def compute_temporal_cv(self, df: pd.DataFrame, param: str) -> float:
        if param not in df.columns:
            return 0.0

        yearly_means = df[param].resample("YE").mean()
        return self.compute_cv(yearly_means)

    def compute_interannual_variability(
        self, df: pd.DataFrame, param: str
    ) -> float:
        if param not in df.columns:
            return 0.0

        yearly_values = df[param].resample("YE").mean()
        return float(yearly_values.std())

    def compute_extreme_frequency(
        self, df: pd.DataFrame, param: str, threshold_percentile: float = 90
    ) -> float:
        if param not in df.columns:
            return 0.0

        data = df[param].dropna()
        if len(data) == 0:
            return 0.0

        threshold = data.quantile(threshold_percentile / 100.0)
        extreme_count = (data > threshold).sum()
        return float(extreme_count / len(data))

    def temperature_volatility_index(self, df: pd.DataFrame) -> float:
        components = []

        # Diurnal temperature range variability
        if "T2M_RANGE" in df.columns:
            cv_range = self.compute_temporal_cv(df, "T2M_RANGE")
            components.append(cv_range)

        # Interannual temperature variability (use CV instead of std * 10)
        if "T2M" in df.columns:
            yearly_temps = df["T2M"].resample("YE").mean()
            temp_cv = self.compute_cv(yearly_temps)
            components.append(temp_cv)

        # Heat stress days above crop-specific threshold
        if "T2M" in df.columns or "T2M_MAX" in df.columns:
            temp_col = "T2M_MAX" if "T2M_MAX" in df.columns else "T2M"
            heat_stress_days = (
                df[temp_col] > self.thresholds["heat_stress_temp"]
            ).sum()
            heat_stress_pct = (heat_stress_days / len(df)) * 100
            components.append(heat_stress_pct)

        # GDD variability (indicates inconsistent growing conditions)
        if "GDD" in df.columns:
            cv_gdd = self.compute_temporal_cv(df, "GDD")
            components.append(cv_gdd)

        return float(np.mean(components)) if components else 0.0

    def precipitation_volatility_index(self, df: pd.DataFrame) -> float:
        components = []

        if "PRECTOTCORR" in df.columns:
            cv_precip = self.compute_temporal_cv(df, "PRECTOTCORR")
            components.append(cv_precip)

            yearly_totals = df["PRECTOTCORR"].resample("YE").sum()
            interannual_var = self.compute_cv(yearly_totals)
            components.append(interannual_var)

        if "DRY_SPELL_LENGTH" in df.columns:
            max_dry_spell = df["DRY_SPELL_LENGTH"].max()
            components.append(max_dry_spell)

        return float(np.mean(components)) if components else 0.0

    def moisture_stress_index(self, df: pd.DataFrame) -> float:
        components = []

        if "GWETROOT" in df.columns:
            # Mean moisture deficit
            gwet_mean = df["GWETROOT"].mean()
            moisture_deficit = (1 - gwet_mean) * 100
            components.append(moisture_deficit)

            # Soil moisture variability
            cv_gwet = self.compute_temporal_cv(df, "GWETROOT")
            components.append(cv_gwet)

        # VPD: normalize by typical crop stress threshold (2-3 kPa)
        if "VPD" in df.columns:
            vpd_mean = df["VPD"].mean()
            vpd_stress_threshold = 2.5  # kPa
            vpd_stress_index = (vpd_mean / vpd_stress_threshold) * 100
            components.append(min(vpd_stress_index, 100))  # Cap at 100

        if "EVPTRNS" in df.columns:
            cv_evap = self.compute_temporal_cv(df, "EVPTRNS")
            components.append(cv_evap)

        return float(np.mean(components)) if components else 0.0

    def extreme_events_index(self, df: pd.DataFrame) -> float:
        components = []

        # Heat stress days
        if "HEAT_DAYS" in df.columns:
            heat_days_per_year = df["HEAT_DAYS"].resample("YE").sum().mean()
            # Normalize: 30 days/year = 100% stress
            components.append(min(heat_days_per_year / 30 * 100, 100))

        # Frost days
        if "FROST_DAYS" in df.columns:
            frost_days_per_year = df["FROST_DAYS"].resample("YE").sum().mean()
            # Normalize: 20 days/year = 100% stress
            components.append(min(frost_days_per_year / 20 * 100, 100))

        # Dry days
        if "DRY_DAYS" in df.columns:
            dry_days_per_year = df["DRY_DAYS"].resample("YE").sum().mean()
            # Normalize: 90 days/year = 100% stress
            components.append(min(dry_days_per_year / 90 * 100, 100))

        # Extreme wind events
        if "WS10M_MAX" in df.columns:
            extreme_wind = self.compute_extreme_frequency(df, "WS10M_MAX", 95)
            components.append(extreme_wind * 100)

        # Solar radiation variability
        if "ALLSKY_SFC_SW_DWN" in df.columns:
            cv_radiation = self.compute_temporal_cv(df, "ALLSKY_SFC_SW_DWN")
            components.append(cv_radiation)

        return float(np.mean(components)) if components else 0.0

    def calculate_acvi(self, df: pd.DataFrame) -> Dict:
        # Filter to growing season
        df_growing = self.filter_growing_season(df)

        if len(df_growing) == 0:
            logger.warning("No data after growing season filter")
            df_growing = df

        temp_vol = self.temperature_volatility_index(df_growing)
        precip_vol = self.precipitation_volatility_index(df_growing)
        moisture_stress = self.moisture_stress_index(df_growing)
        extreme_events = self.extreme_events_index(df_growing)

        acvi_score = (
            self.weights["temperature_volatility"] * temp_vol
            + self.weights["precipitation_volatility"] * precip_vol
            + self.weights["moisture_stress"] * moisture_stress
            + self.weights["extreme_events"] * extreme_events
        )

        return {
            "acvi_score": float(acvi_score),
            "components": {
                "temperature_volatility": float(temp_vol),
                "precipitation_volatility": float(precip_vol),
                "moisture_stress": float(moisture_stress),
                "extreme_events": float(extreme_events),
            },
            "weights": self.weights,
        }

    def normalize_component(
        self, value: float, min_val: float, max_val: float
    ) -> float:
        if max_val == min_val:
            return 50.0
        return ((value - min_val) / (max_val - min_val)) * 100

    def robust_normalize(self, value: float, values: list) -> float:
        """Use robust scaling with percentiles to reduce outlier impact."""
        p5, p95 = np.percentile(values, [5, 95])
        if p95 == p5:
            return 50.0
        normalized = ((value - p5) / (p95 - p5)) * 100
        return float(np.clip(normalized, 0, 100))

    def calculate_all_locations(self):
        print("Step 1: Calculating raw component indices...")
        raw_results = {}

        for location_dir in self.input_dir.iterdir():
            if not location_dir.is_dir():
                continue

            location_name = location_dir.name
            df = self.load_location_data(location_dir)

            if df is None:
                continue

            if not self.validate_input_data(df):
                logger.warning(
                    f"Skipping {location_name}: data quality issues"
                )
                continue

            acvi_result = self.calculate_acvi(df)
            raw_results[location_name] = acvi_result

        print(f"Processed {len(raw_results)} locations")

        print("\nStep 2: Normalizing components to 0-100 scale...")
        normalized_results = self.normalize_components(raw_results)

        print("\nStep 3: Final ACVI scores:")
        sorted_locations = sorted(
            normalized_results.items(),
            key=lambda x: x[1]["acvi_score"],
            reverse=True,
        )
        for location, data in sorted_locations:
            print(f"  {location}: ACVI = {data['acvi_score']:.2f}")

        self.save_results(normalized_results)
        self.create_summary_report(normalized_results)

        print(
            f"\nACVI calculation complete. Results saved to '{self.output_dir}'"
        )

    def normalize_components(self, results: Dict) -> Dict:
        logger.info(
            "Normalizing components to 0-100 scale using robust percentiles..."
        )

        component_names = [
            "temperature_volatility",
            "precipitation_volatility",
            "moisture_stress",
            "extreme_events",
        ]

        # Use robust normalization with percentiles
        normalized_results = {}
        for location, data in results.items():
            normalized_components = {}
            for comp in component_names:
                original_value = data["components"][comp]
                all_values = [r["components"][comp] for r in results.values()]
                normalized_value = self.robust_normalize(
                    original_value, all_values
                )
                normalized_components[comp] = normalized_value

            acvi_score = (
                self.weights["temperature_volatility"]
                * normalized_components["temperature_volatility"]
                + self.weights["precipitation_volatility"]
                * normalized_components["precipitation_volatility"]
                + self.weights["moisture_stress"]
                * normalized_components["moisture_stress"]
                + self.weights["extreme_events"]
                * normalized_components["extreme_events"]
            )

            normalized_results[location] = {
                "acvi_score": float(acvi_score),
                "components": normalized_components,
                "components_raw": data["components"],
                "weights": self.weights,
            }

        return normalized_results

    def save_results(self, results: Dict):
        results_file = self.output_dir / "acvi_scores.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        df_results = []
        for location, data in results.items():
            row = {
                "location": location,
                "acvi_score": data["acvi_score"],
                **data["components"],
            }
            df_results.append(row)

        df = pd.DataFrame(df_results)
        df = df.sort_values("acvi_score", ascending=False)
        df.to_csv(self.output_dir / "acvi_scores.csv", index=False)

    def create_summary_report(self, results: Dict):
        summary_file = self.output_dir / "ACVI_SUMMARY.txt"

        sorted_results = sorted(
            results.items(), key=lambda x: x[1]["acvi_score"], reverse=True
        )

        with open(summary_file, "w") as f:
            f.write("-" * 80 + "\n")
            f.write("AGRO-CLIMATIC VOLATILITY INDEX (ACVI) - RESULTS\n")
            f.write("-" * 80 + "\n\n")

            f.write(f"Total Locations Analyzed: {len(results)}\n")
            f.write(f"Component Weights:\n")
            for component, weight in self.weights.items():
                f.write(f"  - {component}: {weight:.2%}\n")

            f.write("\n" + "-" * 80 + "\n")
            f.write("TOP 10 HIGHEST VOLATILITY LOCATIONS\n")
            f.write("-" * 80 + "\n\n")

            for i, (location, data) in enumerate(sorted_results[:10], 1):
                f.write(f"{i}. {location}\n")
                f.write(f"   ACVI Score: {data['acvi_score']:.2f}\n")
                f.write(f"   Components:\n")
                for comp, value in data["components"].items():
                    f.write(f"     - {comp}: {value:.2f}\n")
                f.write("\n")

            f.write("-" * 80 + "\n")
            f.write("TOP 10 LOWEST VOLATILITY LOCATIONS\n")
            f.write("-" * 80 + "\n\n")

            for i, (location, data) in enumerate(
                reversed(sorted_results[-10:]), 1
            ):
                f.write(f"{i}. {location}\n")
                f.write(f"   ACVI Score: {data['acvi_score']:.2f}\n")
                f.write(f"   Components:\n")
                for comp, value in data["components"].items():
                    f.write(f"     - {comp}: {value:.2f}\n")
                f.write("\n")


if __name__ == "__main__":
    calculator = ACVICalculator(input_dir="acvi_processed_data")
    calculator.calculate_all_locations()
