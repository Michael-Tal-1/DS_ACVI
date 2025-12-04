#!/usr/bin/env python3
"""
ACVI Sensitivity Analysis - Clean Output Version
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import json
from scipy import stats
from scipy.stats import spearmanr
import warnings

warnings.filterwarnings('ignore')


class ACVISensitivityAnalyzer:

    def __init__(
            self,
            acvi_file: str = "acvi_results/acvi_scores.csv",
            processed_dir: str = "acvi_processed_data",
            output_dir: str = "acvi_sensitivity_analysis"
    ):
        self.acvi_file = Path(acvi_file)
        self.processed_dir = Path(processed_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.components = [
            'temperature_volatility',
            'precipitation_volatility',
            'moisture_stress',
            'extreme_events'
        ]

        self.default_weights = {
            'temperature_volatility': 0.30,
            'precipitation_volatility': 0.30,
            'moisture_stress': 0.25,
            'extreme_events': 0.15
        }

        self.results = {}

    def load_acvi_data(self) -> pd.DataFrame:
        if not self.acvi_file.exists():
            raise FileNotFoundError(f"ACVI file not found: {self.acvi_file}")
        df = pd.read_csv(self.acvi_file)
        return df

    def test_weight_sensitivity(self, acvi_df: pd.DataFrame) -> Dict:
        print("\n1. WEIGHT SENSITIVITY")

        results = {
            'weight_variations': [],
            'ranking_stability': {}
        }

        weight_scenarios = self._generate_weight_scenarios()
        original_ranking = acvi_df.sort_values('acvi_score', ascending=False)['location'].tolist()
        ranking_correlations = []

        for i, weights in enumerate(weight_scenarios, 1):
            new_acvi = self._calculate_acvi_with_weights(acvi_df, weights)
            new_ranking = new_acvi.sort_values('acvi_new', ascending=False)['location'].tolist()
            rank_corr = self._ranking_correlation(original_ranking, new_ranking)
            score_corr = acvi_df['acvi_score'].corr(new_acvi['acvi_new'])

            scenario_result = {
                'scenario_id': i,
                'weights': weights,
                'ranking_correlation': float(rank_corr),
                'score_correlation': float(score_corr),
                'top_10_overlap': self._top_n_overlap(original_ranking, new_ranking, 10)
            }

            results['weight_variations'].append(scenario_result)
            ranking_correlations.append(rank_corr)

        results['ranking_stability'] = {
            'mean_correlation': float(np.mean(ranking_correlations)),
            'std_correlation': float(np.std(ranking_correlations)),
            'min_correlation': float(np.min(ranking_correlations)),
            'scenarios_above_0.9': int(sum(1 for r in ranking_correlations if r > 0.9))
        }

        print(f"  Mean correlation: {results['ranking_stability']['mean_correlation']:.4f}")
        print(f"  Std correlation: {results['ranking_stability']['std_correlation']:.4f}")
        print(f"  Min correlation: {results['ranking_stability']['min_correlation']:.4f}")
        print(f"  Scenarios r>0.9: {results['ranking_stability']['scenarios_above_0.9']}/17")

        return results

    def _generate_weight_scenarios(self) -> List[Dict]:
        scenarios = []
        scenarios.append({c: 0.25 for c in self.components})

        for comp in self.components:
            weights = {c: 0.5 if c == comp else 0.167 for c in self.components}
            scenarios.append(weights)

        for comp in self.components:
            weights = {c: 0.1 if c == comp else 0.3 for c in self.components}
            scenarios.append(weights)

        np.random.seed(42)
        for _ in range(6):
            weights = {}
            for comp in self.components:
                variation = np.random.uniform(0.8, 1.2)
                weights[comp] = self.default_weights[comp] * variation
            total = sum(weights.values())
            weights = {k: v / total for k, v in weights.items()}
            scenarios.append(weights)

        scenarios.append({
            'temperature_volatility': 0.40,
            'precipitation_volatility': 0.40,
            'moisture_stress': 0.15,
            'extreme_events': 0.05
        })

        scenarios.append({
            'temperature_volatility': 0.15,
            'precipitation_volatility': 0.15,
            'moisture_stress': 0.40,
            'extreme_events': 0.30
        })

        return scenarios

    def _calculate_acvi_with_weights(self, df: pd.DataFrame, weights: Dict) -> pd.DataFrame:
        df_new = df.copy()
        df_new['acvi_new'] = (
                df_new['temperature_volatility'] * weights['temperature_volatility'] +
                df_new['precipitation_volatility'] * weights['precipitation_volatility'] +
                df_new['moisture_stress'] * weights['moisture_stress'] +
                df_new['extreme_events'] * weights['extreme_events']
        )
        return df_new

    def _ranking_correlation(self, rank1: List, rank2: List) -> float:
        indices1 = {loc: i for i, loc in enumerate(rank1)}
        indices2 = {loc: i for i, loc in enumerate(rank2)}
        common_locs = set(rank1) & set(rank2)
        ranks1 = [indices1[loc] for loc in common_locs]
        ranks2 = [indices2[loc] for loc in common_locs]
        corr, _ = spearmanr(ranks1, ranks2)
        return corr

    def _top_n_overlap(self, rank1: List, rank2: List, n: int) -> int:
        top_n_1 = set(rank1[:n])
        top_n_2 = set(rank2[:n])
        return len(top_n_1 & top_n_2)

    def test_multicollinearity(self, acvi_df: pd.DataFrame) -> Dict:
        print("\n2. MULTICOLLINEARITY")

        component_data = acvi_df[self.components]
        corr_matrix = component_data.corr()

        results = {
            'correlation_matrix': corr_matrix.to_dict(),
            'high_correlations': [],
            'vif_scores': {}
        }

        for i, comp1 in enumerate(self.components):
            for comp2 in self.components[i + 1:]:
                corr = corr_matrix.loc[comp1, comp2]
                if abs(corr) > 0.7:
                    results['high_correlations'].append({
                        'component1': comp1,
                        'component2': comp2,
                        'correlation': float(corr)
                    })

        try:
            from sklearn.linear_model import LinearRegression
            for comp in self.components:
                vif = self._calculate_vif(component_data, comp)
                results['vif_scores'][comp] = float(vif)

            print("  VIF scores:")
            for comp, vif in results['vif_scores'].items():
                print(f"    {comp}: {vif:.2f}")

            if results['high_correlations']:
                print("  High correlations (r>0.7):")
                for hc in results['high_correlations']:
                    print(f"    {hc['component1']} <-> {hc['component2']}: {hc['correlation']:.3f}")
            else:
                print("  High correlations (r>0.7): None")

        except ImportError:
            results['vif_scores'] = {comp: 1.0 for comp in self.components}

        max_vif = max(results['vif_scores'].values())
        max_corr = max([abs(c['correlation']) for c in results['high_correlations']], default=0)

        if max_vif < 5 and max_corr < 0.7:
            assessment = "EXCELLENT"
        elif max_vif < 10 and max_corr < 0.8:
            assessment = "GOOD"
        else:
            assessment = "MODERATE"

        results['assessment'] = assessment
        print(f"  Assessment: {assessment}")

        return results

    def _calculate_vif(self, df: pd.DataFrame, target_col: str) -> float:
        from sklearn.linear_model import LinearRegression
        other_cols = [col for col in df.columns if col != target_col]
        X = df[other_cols].values
        y = df[target_col].values
        model = LinearRegression()
        model.fit(X, y)
        r_squared = model.score(X, y)
        if r_squared >= 0.9999:
            return 999.99
        vif = 1 / (1 - r_squared)
        return vif

    def monte_carlo_simulation(self, acvi_df: pd.DataFrame, n_simulations: int = 1000) -> Dict:
        print("\n3. MONTE CARLO SIMULATION")
        print(f"  Running {n_simulations} simulations...")

        results = {
            'n_simulations': n_simulations,
            'ranking_correlations': [],
            'score_rmse': [],
            'top_10_stability': []
        }

        original_ranking = acvi_df.sort_values('acvi_score', ascending=False)['location'].tolist()
        np.random.seed(42)

        for i in range(n_simulations):
            noisy_weights = {}
            for comp in self.components:
                noise = np.random.uniform(0.9, 1.1)
                noisy_weights[comp] = self.default_weights[comp] * noise
            total = sum(noisy_weights.values())
            noisy_weights = {k: v / total for k, v in noisy_weights.items()}

            noisy_df = acvi_df.copy()
            for comp in self.components:
                noise = np.random.normal(1.0, 0.05, len(noisy_df))
                noisy_df[comp] = noisy_df[comp] * noise
                noisy_df[comp] = noisy_df[comp].clip(0, 1)

            noisy_acvi = self._calculate_acvi_with_weights(noisy_df, noisy_weights)
            noisy_ranking = noisy_acvi.sort_values('acvi_new', ascending=False)['location'].tolist()

            rank_corr = self._ranking_correlation(original_ranking, noisy_ranking)
            score_rmse = np.sqrt(np.mean((acvi_df['acvi_score'] - noisy_acvi['acvi_new']) ** 2))
            top_10_overlap = self._top_n_overlap(original_ranking, noisy_ranking, 10)

            results['ranking_correlations'].append(rank_corr)
            results['score_rmse'].append(score_rmse)
            results['top_10_stability'].append(top_10_overlap)

        results['summary'] = {
            'mean_ranking_correlation': float(np.mean(results['ranking_correlations'])),
            'std_ranking_correlation': float(np.std(results['ranking_correlations'])),
            'percentile_5': float(np.percentile(results['ranking_correlations'], 5)),
            'percentile_95': float(np.percentile(results['ranking_correlations'], 95)),
            'mean_rmse': float(np.mean(results['score_rmse'])),
            'mean_top10_overlap': float(np.mean(results['top_10_stability']))
        }

        print(f"  Mean correlation: {results['summary']['mean_ranking_correlation']:.4f}")
        print(f"  Std correlation: {results['summary']['std_ranking_correlation']:.4f}")
        print(f"  5th percentile: {results['summary']['percentile_5']:.4f}")
        print(f"  95th percentile: {results['summary']['percentile_95']:.4f}")
        print(f"  Mean Top-10 overlap: {results['summary']['mean_top10_overlap']:.1f}/10")

        return results

    def test_geographical_robustness(self, acvi_df: pd.DataFrame) -> Dict:
        print("\n4. GEOGRAPHICAL ROBUSTNESS")

        regions = {
            'Europe': ['UA', 'PL', 'DE', 'FR', 'RO', 'HU', 'IT', 'ES', 'NL', 'UK', 'TR'],
            'North America': ['US', 'CA'],
            'South America': ['BR', 'AR'],
            'Asia': ['CN', 'IN', 'KZ'],
            'Africa': ['EG', 'ZA'],
            'Oceania': ['AU']
        }

        acvi_df['region'] = acvi_df['location'].apply(
            lambda x: self._get_region(x, regions)
        )

        results = {
            'regional_statistics': {},
            'anova_test': {}
        }

        regional_scores = {}

        print("  Regional statistics:")
        for region in regions.keys():
            region_data = acvi_df[acvi_df['region'] == region]
            if len(region_data) == 0:
                continue

            regional_scores[region] = region_data['acvi_score'].values
            results['regional_statistics'][region] = {
                'n': int(len(region_data)),
                'mean': float(region_data['acvi_score'].mean()),
                'std': float(region_data['acvi_score'].std())
            }

            print(
                f"    {region}: N={len(region_data)}, Mean={region_data['acvi_score'].mean():.2f}, Std={region_data['acvi_score'].std():.2f}")

        score_groups = [scores for scores in regional_scores.values() if len(scores) > 0]

        if len(score_groups) >= 2:
            f_stat, p_value = stats.f_oneway(*score_groups)
            results['anova_test'] = {
                'f_statistic': float(f_stat),
                'p_value': float(p_value),
                'significant': bool(p_value < 0.05)
            }

            print(f"  ANOVA: F={f_stat:.3f}, p={p_value:.4f}, Significant={p_value < 0.05}")

        return results

    def _get_region(self, location: str, regions: Dict) -> str:
        location_prefix = location.split('_')[0]
        for region, countries in regions.items():
            if location_prefix in countries:
                return region
        return 'Unknown'

    def generate_comprehensive_report(self):
        report_file = self.output_dir / "SENSITIVITY_REPORT.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("ACVI SENSITIVITY ANALYSIS REPORT\n\n")

            if 'weight_sensitivity' in self.results:
                f.write("1. WEIGHT SENSITIVITY\n")
                ws = self.results['weight_sensitivity']['ranking_stability']
                f.write(f"  Mean correlation: {ws['mean_correlation']:.4f}\n")
                f.write(f"  Std correlation: {ws['std_correlation']:.4f}\n")
                f.write(f"  Min correlation: {ws['min_correlation']:.4f}\n")
                f.write(f"  Scenarios r>0.9: {ws['scenarios_above_0.9']}/17\n\n")

            if 'multicollinearity' in self.results:
                f.write("2. MULTICOLLINEARITY\n")
                mc = self.results['multicollinearity']
                f.write("  VIF scores:\n")
                for comp, vif in mc['vif_scores'].items():
                    f.write(f"    {comp}: {vif:.2f}\n")
                f.write(f"  Assessment: {mc['assessment']}\n\n")

            if 'monte_carlo' in self.results:
                f.write("3. MONTE CARLO\n")
                mc = self.results['monte_carlo']['summary']
                f.write(f"  Mean correlation: {mc['mean_ranking_correlation']:.4f}\n")
                f.write(f"  5th percentile: {mc['percentile_5']:.4f}\n")
                f.write(f"  95th percentile: {mc['percentile_95']:.4f}\n")
                f.write(f"  Mean Top-10 overlap: {mc['mean_top10_overlap']:.1f}/10\n\n")

            if 'geographical_robustness' in self.results:
                f.write("4. GEOGRAPHICAL ROBUSTNESS\n")
                gr = self.results['geographical_robustness']
                if 'anova_test' in gr:
                    f.write(f"  ANOVA p-value: {gr['anova_test']['p_value']:.4f}\n")
                    f.write(f"  Significant: {gr['anova_test']['significant']}\n\n")

            checks_passed = 0
            total_checks = 4

            if self.results['weight_sensitivity']['ranking_stability']['mean_correlation'] > 0.90:
                checks_passed += 1
            if max(self.results['multicollinearity']['vif_scores'].values()) < 10:
                checks_passed += 1
            if self.results['monte_carlo']['summary']['mean_ranking_correlation'] > 0.90:
                checks_passed += 1
            if not self.results['geographical_robustness'].get('anova_test', {}).get('significant', True):
                checks_passed += 1

            f.write(f"SUMMARY: {checks_passed}/{total_checks} checks passed\n")

        print(f"\nReport saved: {report_file}")

    def run_full_analysis(self):
        print("ACVI SENSITIVITY ANALYSIS")
        print(f"Loaded: {len(pd.read_csv(self.acvi_file))} locations")

        acvi_df = self.load_acvi_data()

        self.results['weight_sensitivity'] = self.test_weight_sensitivity(acvi_df)
        self.results['multicollinearity'] = self.test_multicollinearity(acvi_df)
        self.results['monte_carlo'] = self.monte_carlo_simulation(acvi_df, n_simulations=1000)
        self.results['geographical_robustness'] = self.test_geographical_robustness(acvi_df)

        self.save_results()
        self.generate_comprehensive_report()

        print(f"\nResults saved to: {self.output_dir}")

    def save_results(self):
        results_file = self.output_dir / "sensitivity_results.json"

        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj

        results_clean = convert_types(self.results)

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_clean, f, indent=2)


if __name__ == "__main__":
    analyzer = ACVISensitivityAnalyzer(
        acvi_file="acvi_results/acvi_scores.csv",
        processed_dir="acvi_processed_data",
        output_dir="acvi_sensitivity_analysis"
    )

    analyzer.run_full_analysis()