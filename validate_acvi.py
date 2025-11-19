"""
ACVI Validation with FAO Yield Data
Calculates correlation between ACVI and crop yield volatility.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import json
from scipy import stats
import matplotlib.pyplot as plt
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ACVIValidator:
    def __init__(
        self,
        acvi_file: str = "acvi_results/acvi_scores.csv",
        fao_file: str = "fao_yield_data/yield_volatility.csv",
    ):
        self.acvi_file = Path(acvi_file)
        self.fao_file = Path(fao_file)
        self.output_dir = Path("acvi_validation")
        self.output_dir.mkdir(exist_ok=True)

        self.location_to_country = {
            "UA_Center_Kirovohrad": "UA",
            "UA_South_Kherson": "UA",
            "UA_West_Ternopil": "UA",
            "UA_North_Chernihiv": "UA",
            "UA_East_Kharkiv": "UA",
            "UA_Vinnytsia": "UA",
            "UA_Poltava": "UA",
            "UA_Odesa": "UA",
            "UA_Zhytomyr": "UA",
            "UA_Lviv": "UA",
            "PL_Mazowieckie": "PL",
            "PL_Wielkopolskie": "PL",
            "DE_Bavaria": "DE",
            "DE_LowerSaxony": "DE",
            "FR_Beauce": "FR",
            "FR_Bordeaux": "FR",
            "RO_Wallachia": "RO",
            "RO_Moldavia": "RO",
            "HU_Puszta": "HU",
            "IT_PoValley": "IT",
            "ES_Andalusia": "ES",
            "ES_CastillaLeon": "ES",
            "NL_Flevoland": "NL",
            "UK_Lincolnshire": "UK",
            "US_Iowa": "US",
            "US_Kansas": "US",
            "US_Illinois": "US",
            "US_Nebraska": "US",
            "US_California_CentralValley": "US",
            "US_NorthDakota": "US",
            "US_Minnesota": "US",
            "CA_Saskatchewan": "CA",
            "CA_Alberta": "CA",
            "CA_Manitoba": "CA",
            "BR_MatoGrosso": "BR",
            "BR_Parana": "BR",
            "BR_Goias": "BR",
            "AR_BuenosAires": "AR",
            "AR_Cordoba": "AR",
            "AR_SantaFe": "AR",
            "AR_LaPampa": "AR",
            "CN_Henan": "CN",
            "CN_Heilongjiang": "CN",
            "CN_Shandong": "CN",
            "CN_Jilin": "CN",
            "IN_Punjab": "IN",
            "IN_MadhyaPradesh": "IN",
            "IN_UttarPradesh": "IN",
            "KZ_Kostanay": "KZ",
            "KZ_Akmola": "KZ",
            "TR_Konya": "TR",
            "ZA_FreeState": "ZA",
            "ZA_WesternCape": "ZA",
            "AU_NewSouthWales": "AU",
            "AU_WesternAustralia": "AU",
            "AU_Victoria": "AU",
            "EG_NileDelta": "EG",
        }

    def load_data(self):
        if not self.acvi_file.exists():
            print(f"ACVI file not found: {self.acvi_file}")
            return None, None

        if not self.fao_file.exists():
            print(f"FAO file not found: {self.fao_file}")
            return None, None

        acvi_df = pd.read_csv(self.acvi_file)
        fao_df = pd.read_csv(self.fao_file)

        return acvi_df, fao_df

    def aggregate_location_acvi(self, acvi_df: pd.DataFrame) -> pd.DataFrame:
        acvi_df["country"] = acvi_df["location"].map(self.location_to_country)

        country_acvi = (
            acvi_df.groupby("country")
            .agg(
                {
                    "acvi_score": "mean",
                    "temperature_volatility": "mean",
                    "precipitation_volatility": "mean",
                    "moisture_stress": "mean",
                    "extreme_events": "mean",
                }
            )
            .reset_index()
        )

        return country_acvi

    def calculate_correlations(
        self, acvi_df: pd.DataFrame, fao_df: pd.DataFrame
    ):
        print("Calculating correlations...")

        country_acvi = self.aggregate_location_acvi(acvi_df)

        results = {}

        for crop in ["wheat", "maize"]:
            crop_data = fao_df[fao_df["crop"] == crop]

            merged = pd.merge(
                country_acvi, crop_data, on="country", how="inner"
            )

            if len(merged) < 3:
                print(f"  {crop}: insufficient data (n={len(merged)})")
                continue

            correlations = {}

            for metric in ["cv_yield", "detrended_cv"]:
                if metric not in merged.columns:
                    continue

                corr_acvi, p_acvi = stats.pearsonr(
                    merged["acvi_score"], merged[metric]
                )

                correlations[f"acvi_vs_{metric}"] = {
                    "correlation": float(corr_acvi),
                    "p_value": float(p_acvi),
                    "significant": bool(p_acvi < 0.05),
                    "n_samples": int(len(merged)),
                }

                for component in [
                    "temperature_volatility",
                    "precipitation_volatility",
                    "moisture_stress",
                    "extreme_events",
                ]:
                    if component in merged.columns:
                        corr, p = stats.pearsonr(
                            merged[component], merged[metric]
                        )
                        correlations[f"{component}_vs_{metric}"] = {
                            "correlation": float(corr),
                            "p_value": float(p),
                        }

            # Convert DataFrame to dict, ensuring numpy types are converted to Python types
            merged_dict = merged.copy()
            for col in merged_dict.columns:
                if (
                    merged_dict[col].dtype == np.float64
                    or merged_dict[col].dtype == np.float32
                ):
                    merged_dict[col] = merged_dict[col].astype(float)
                elif (
                    merged_dict[col].dtype == np.int64
                    or merged_dict[col].dtype == np.int32
                ):
                    merged_dict[col] = merged_dict[col].astype(int)

            results[crop] = {
                "correlations": correlations,
                "data": merged_dict.to_dict("records"),
            }

            print(
                f"  {crop}: r={correlations.get('acvi_vs_cv_yield', {}).get('correlation', 0):.3f}, "
                f"p={correlations.get('acvi_vs_cv_yield', {}).get('p_value', 1):.4f}, "
                f"n={len(merged)}"
            )

        return results

    def create_validation_report(self, results: Dict):
        report_file = self.output_dir / "validation_report.txt"

        with open(report_file, "w") as f:
            f.write("-" * 80 + "\n")
            f.write(
                "ACVI VALIDATION REPORT - CORRELATION WITH CROP YIELD VOLATILITY\n"
            )
            f.write("-" * 80 + "\n\n")

            for crop, data in results.items():
                f.write(f"\n{crop.upper()}\n")
                f.write("-" * 40 + "\n")

                correlations = data["correlations"]

                acvi_corr = correlations.get("acvi_vs_cv_yield", {})
                if acvi_corr:
                    f.write(f"ACVI vs Yield CV:\n")
                    f.write(f"  Correlation: {acvi_corr['correlation']:.4f}\n")
                    f.write(f"  P-value: {acvi_corr['p_value']:.4f}\n")
                    f.write(f"  Significant: {acvi_corr['significant']}\n")
                    f.write(f"  Sample size: {acvi_corr['n_samples']}\n\n")

                f.write("Component Correlations:\n")
                for key, val in correlations.items():
                    if "component" in key or "vs_cv_yield" in key:
                        if key != "acvi_vs_cv_yield":
                            comp_name = key.replace("_vs_cv_yield", "")
                            f.write(
                                f"  {comp_name}: r={val['correlation']:.4f}\n"
                            )

                f.write("\n")

            f.write("-" * 80 + "\n")
            f.write("INTERPRETATION:\n")
            f.write("r > 0.6: Strong positive correlation\n")
            f.write("r > 0.4: Moderate positive correlation\n")
            f.write("r > 0.2: Weak positive correlation\n")
            f.write("p < 0.05: Statistically significant\n")

    def run_validation(self):
        print("=" * 60)
        print("ACVI VALIDATION WITH FAO YIELD DATA")
        print("=" * 60)

        acvi_df, fao_df = self.load_data()

        if acvi_df is None or fao_df is None:
            print("\nValidation aborted: missing data files")
            return

        results = self.calculate_correlations(acvi_df, fao_df)

        results_file = self.output_dir / "validation_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        self.create_validation_report(results)

        print(f"\nValidation complete. Results saved to '{self.output_dir}'")


if __name__ == "__main__":
    validator = ACVIValidator()
    validator.run_validation()
