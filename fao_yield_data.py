#!/usr/bin/env python3
"""
FAO Crop Yield Data Downloader
Downloads wheat and maize yield data from FAOSTAT for validation.
Uses official faostat Python package.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
import json

try:
    import faostat
except ImportError:
    print("ERROR: faostat package not installed")
    print("Install with: pip install faostat")
    exit(1)


class FAOYieldDownloader:
    def __init__(self, output_dir: str = "fao_yield_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        faostat.set_requests_args(timeout=180)

        self.country_codes = {
            "UA": 230,
            "US": 231,
            "PL": 173,
            "DE": 79,
            "FR": 68,
            "RO": 183,
            "HU": 97,
            "IT": 106,
            "ES": 203,
            "NL": 150,
            "UK": 229,
            "CA": 33,
            "BR": 21,
            "AR": 9,
            "CN": 41,
            "IN": 100,
            "KZ": 108,
            "TR": 223,
            "ZA": 202,
            "AU": 10,
            "EG": 59,
        }

        self.crop_items = {
            "wheat": 15,
            "maize": 56,
        }

    def download_yield_data(
        self, country_code: int, crop_item: int
    ) -> pd.DataFrame:
        try:
            pars = {
                "area": country_code,
                "element": 2413,
                "item": crop_item,
                "year": list(range(2009, 2024)),
            }

            df = faostat.get_data_df("QCL", pars=pars, strval=False)

            if df is None or len(df) == 0:
                return None

            if "Year" in df.columns and "Value" in df.columns:
                df = df[["Year", "Value"]].copy()
                df.columns = ["year", "value"]
            elif "year" in df.columns and "value" in df.columns:
                df = df[["year", "value"]].copy()
            else:
                return None

            # Convert year to integer (API returns it as string)
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
            df = df.dropna(subset=["year"])
            df["year"] = df["year"].astype(int)

            df = df[df["year"] >= 2009]
            df = df.dropna(subset=["value"])
            df = df.sort_values("year")

            if len(df) == 0:
                return None

            return df

        except Exception as e:
            return None

    def calculate_yield_volatility(self, df: pd.DataFrame) -> Dict:
        if df is None or len(df) < 3:
            return None

        yields = df["value"].values

        cv = (
            (np.std(yields) / np.mean(yields)) * 100
            if np.mean(yields) > 0
            else 0
        )

        detrended_yields = yields - np.polyval(
            np.polyfit(range(len(yields)), yields, 1), range(len(yields))
        )
        detrended_cv = (
            (np.std(detrended_yields) / np.mean(yields)) * 100
            if np.mean(yields) > 0
            else 0
        )

        return {
            "mean_yield": float(np.mean(yields)),
            "std_yield": float(np.std(yields)),
            "cv_yield": float(cv),
            "detrended_cv": float(detrended_cv),
            "min_yield": float(np.min(yields)),
            "max_yield": float(np.max(yields)),
            "range": float(np.max(yields) - np.min(yields)),
        }

    def download_all_countries(self):
        print("Downloading crop yield data from FAOSTAT")
        print("Using official faostat package\n")

        results = {}

        for country_abbr, country_code in self.country_codes.items():
            print(f"{country_abbr}:")
            country_data = {}

            for crop_name, crop_item in self.crop_items.items():
                print(f"  {crop_name:10s} ", end="", flush=True)

                df = self.download_yield_data(country_code, crop_item)

                if df is not None and len(df) > 0:
                    volatility = self.calculate_yield_volatility(df)

                    if volatility:
                        country_data[crop_name] = {
                            "data": df.to_dict("records"),
                            "volatility": volatility,
                        }
                        print(f"OK (CV: {volatility['cv_yield']:5.2f}%)")
                    else:
                        print("FAILED (insufficient data)")
                else:
                    print("FAILED (no data)")

            if country_data:
                results[country_abbr] = country_data

        self.save_results(results)
        print(f"\nDownload complete. Data saved to '{self.output_dir}'")

        return results

    def save_results(self, results: Dict):
        results_file = self.output_dir / "fao_yield_data.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        volatility_records = []
        for country, crops in results.items():
            for crop, data in crops.items():
                vol = data["volatility"]
                volatility_records.append(
                    {
                        "country": country,
                        "crop": crop,
                        "mean_yield": vol["mean_yield"],
                        "cv_yield": vol["cv_yield"],
                        "detrended_cv": vol["detrended_cv"],
                    }
                )

        df_vol = pd.DataFrame(volatility_records)
        df_vol.to_csv(self.output_dir / "yield_volatility.csv", index=False)


if __name__ == "__main__":
    downloader = FAOYieldDownloader()
    downloader.download_all_countries()
