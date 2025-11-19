"""
Statistical Analysis of NASA POWER ACVI Dataset
Performs comprehensive multivariate analysis with outlier and missing value detection.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
import json
from scipy import stats
from datetime import datetime


class ACVIStatisticalAnalyzer:
    def __init__(self, data_dir: str = "acvi_global_dataset_parallel"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path("acvi_statistical_reports")
        self.output_dir.mkdir(exist_ok=True)

        self.parameters = [
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

        self.results = {}

    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        print("Loading datasets...")
        datasets = {}

        for location_dir in self.data_dir.iterdir():
            if not location_dir.is_dir():
                continue

            csv_files = list(location_dir.glob("*.csv"))
            if not csv_files:
                continue

            location_name = location_dir.name
            df = pd.read_csv(csv_files[0], index_col=0, parse_dates=True)
            datasets[location_name] = df

        print(f"Loaded {len(datasets)} locations")
        return datasets

    def analyze_missing_values(
        self, datasets: Dict[str, pd.DataFrame]
    ) -> Dict:
        print("Analyzing missing values...")
        missing_report = {}

        for location, df in datasets.items():
            location_missing = {}
            total_rows = len(df)

            for param in self.parameters:
                if param in df.columns:
                    missing_count = df[param].isna().sum()
                    missing_pct = (missing_count / total_rows) * 100

                    location_missing[param] = {
                        "count": int(missing_count),
                        "percentage": round(missing_pct, 2),
                    }

            total_missing = sum(v["count"] for v in location_missing.values())
            location_missing["total_missing"] = total_missing
            location_missing["total_cells"] = total_rows * len(self.parameters)
            location_missing["overall_pct"] = round(
                (total_missing / (total_rows * len(self.parameters))) * 100, 2
            )

            missing_report[location] = location_missing

        return missing_report

    def detect_outliers(self, datasets: Dict[str, pd.DataFrame]) -> Dict:
        print("Detecting outliers (IQR method)...")
        outlier_report = {}

        for location, df in datasets.items():
            location_outliers = {}

            for param in self.parameters:
                if param not in df.columns:
                    continue

                data = df[param].dropna()
                if len(data) == 0:
                    continue

                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = ((data < lower_bound) | (data > upper_bound)).sum()
                outlier_pct = (outliers / len(data)) * 100

                location_outliers[param] = {
                    "count": int(outliers),
                    "percentage": round(outlier_pct, 2),
                    "bounds": {
                        "lower": round(lower_bound, 2),
                        "upper": round(upper_bound, 2),
                    },
                }

            outlier_report[location] = location_outliers

        return outlier_report

    def compute_descriptive_stats(
        self, datasets: Dict[str, pd.DataFrame]
    ) -> Dict:
        print("Computing descriptive statistics...")
        stats_report = {}

        for location, df in datasets.items():
            location_stats = {}

            for param in self.parameters:
                if param not in df.columns:
                    continue

                data = df[param].dropna()
                if len(data) == 0:
                    continue

                location_stats[param] = {
                    "mean": round(data.mean(), 3),
                    "median": round(data.median(), 3),
                    "std": round(data.std(), 3),
                    "min": round(data.min(), 3),
                    "max": round(data.max(), 3),
                    "q25": round(data.quantile(0.25), 3),
                    "q75": round(data.quantile(0.75), 3),
                    "cv": (
                        round((data.std() / data.mean()) * 100, 2)
                        if data.mean() != 0
                        else None
                    ),
                    "skewness": round(stats.skew(data), 3),
                    "kurtosis": round(stats.kurtosis(data), 3),
                }

            stats_report[location] = location_stats

        return stats_report

    def compute_temporal_trends(
        self, datasets: Dict[str, pd.DataFrame]
    ) -> Dict:
        print("Computing temporal trends...")
        trends_report = {}

        for location, df in datasets.items():
            location_trends = {}

            df_yearly = df.groupby(df.index.year).mean()
            years = np.arange(len(df_yearly))

            for param in self.parameters:
                if param not in df_yearly.columns:
                    continue

                values = df_yearly[param].dropna()
                if len(values) < 3:
                    continue

                years_subset = years[: len(values)]
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    years_subset, values
                )

                location_trends[param] = {
                    "slope": float(round(slope, 6)),
                    "r_squared": float(round(r_value**2, 4)),
                    "p_value": float(round(p_value, 4)),
                    "trend": "increasing" if slope > 0 else "decreasing",
                    "significant": bool(p_value < 0.05),
                }

            trends_report[location] = location_trends

        return trends_report

    def compute_correlations(self, datasets: Dict[str, pd.DataFrame]) -> Dict:
        print("Computing parameter correlations...")
        correlation_report = {}

        for location, df in datasets.items():
            available_params = [p for p in self.parameters if p in df.columns]
            if len(available_params) < 2:
                continue

            corr_matrix = df[available_params].corr()

            correlation_report[location] = {}
            for i, param1 in enumerate(available_params):
                for param2 in available_params[i + 1 :]:
                    corr_value = corr_matrix.loc[param1, param2]
                    if not np.isnan(corr_value):
                        key = f"{param1}_vs_{param2}"
                        correlation_report[location][key] = round(
                            corr_value, 3
                        )

        return correlation_report

    def create_summary_report(self) -> Dict:
        summary = {
            "analysis_date": datetime.now().isoformat(),
            "total_locations": len(self.results.get("descriptive_stats", {})),
            "parameters_analyzed": self.parameters,
            "data_directory": str(self.data_dir),
        }

        if "missing_values" in self.results:
            total_missing = sum(
                loc["total_missing"]
                for loc in self.results["missing_values"].values()
            )
            summary["total_missing_values"] = total_missing

        if "outliers" in self.results:
            total_outliers = sum(
                sum(param["count"] for param in loc.values())
                for loc in self.results["outliers"].values()
            )
            summary["total_outliers"] = total_outliers

        return summary

    def run_full_analysis(self):
        datasets = self.load_all_data()

        self.results["descriptive_stats"] = self.compute_descriptive_stats(
            datasets
        )
        self.results["missing_values"] = self.analyze_missing_values(datasets)
        self.results["outliers"] = self.detect_outliers(datasets)
        self.results["temporal_trends"] = self.compute_temporal_trends(
            datasets
        )
        self.results["correlations"] = self.compute_correlations(datasets)
        self.results["summary"] = self.create_summary_report()

        self.save_results()
        print(f"\nAnalysis complete. Reports saved to '{self.output_dir}'")

    def save_results(self):
        for analysis_type, data in self.results.items():
            filepath = self.output_dir / f"{analysis_type}.json"
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

        self.create_readable_summary()

    def create_readable_summary(self):
        summary_file = self.output_dir / "SUMMARY.txt"

        with open(summary_file, "w") as f:
            f.write("-" * 80 + "\n")
            f.write("ACVI DATASET - STATISTICAL ANALYSIS SUMMARY\n")
            f.write("-" * 80 + "\n\n")

            summary = self.results["summary"]
            f.write(f"Analysis Date: {summary['analysis_date']}\n")
            f.write(f"Total Locations: {summary['total_locations']}\n")
            f.write(
                f"Total Missing Values: {summary.get('total_missing_values', 0)}\n"
            )
            f.write(
                f"Total Outliers Detected: {summary.get('total_outliers', 0)}\n\n"
            )

            f.write("Parameters Analyzed:\n")
            for param in self.parameters:
                f.write(f"  - {param}\n")

            f.write("\n" + "-" * 80 + "\n")
            f.write("MISSING VALUES BY LOCATION (Top 10)\n")
            f.write("-" * 80 + "\n\n")

            missing_sorted = sorted(
                self.results["missing_values"].items(),
                key=lambda x: x[1].get("total_missing", 0),
                reverse=True,
            )[:10]

            for location, data in missing_sorted:
                f.write(f"{location}:\n")
                f.write(f"  Total Missing: {data['total_missing']} ")
                f.write(f"({data['overall_pct']}%)\n\n")

            f.write("-" * 80 + "\n")
            f.write("OUTLIERS BY LOCATION (Top 10)\n")
            f.write("-" * 80 + "\n\n")

            outlier_totals = {}
            for location, params in self.results["outliers"].items():
                total = sum(param["count"] for param in params.values())
                outlier_totals[location] = total

            outlier_sorted = sorted(
                outlier_totals.items(), key=lambda x: x[1], reverse=True
            )[:10]

            for location, total in outlier_sorted:
                f.write(f"{location}: {total} outliers\n")


if __name__ == "__main__":
    analyzer = ACVIStatisticalAnalyzer(data_dir="acvi_global_dataset_parallel")
    analyzer.run_full_analysis()
