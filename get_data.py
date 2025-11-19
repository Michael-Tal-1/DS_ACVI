#!/usr/bin/env python3
"""
NASA POWER ACVI Data Downloader
Downloads climate data from NASA POWER API for agricultural regions.
Supports parallel downloads for improved performance.
"""

import requests
import pandas as pd
import numpy as np
import io
import time
import random
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class ACVIDataDownloader:
    def __init__(self, output_dir: str = "acvi_parallel_dataset"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.parameters: List[str] = [
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

        self.base_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
        self.data_store: Dict[str, pd.DataFrame] = {}
        self.locations = self._get_locations()

    def _get_locations(self) -> Dict[str, Dict[str, float]]:
        return {
            "UA_Center_Kirovohrad": {"lat": 48.50, "lon": 32.26},
            "UA_South_Kherson": {"lat": 46.63, "lon": 32.61},
            "UA_West_Ternopil": {"lat": 49.55, "lon": 25.59},
            "UA_North_Chernihiv": {"lat": 51.49, "lon": 31.28},
            "UA_East_Kharkiv": {"lat": 49.99, "lon": 36.23},
            "UA_Vinnytsia": {"lat": 49.23, "lon": 28.46},
            "UA_Poltava": {"lat": 49.58, "lon": 34.55},
            "UA_Odesa": {"lat": 46.48, "lon": 30.72},
            "UA_Zhytomyr": {"lat": 50.25, "lon": 28.66},
            "UA_Lviv": {"lat": 49.83, "lon": 24.02},
            "PL_Mazowieckie": {"lat": 52.22, "lon": 21.01},
            "PL_Wielkopolskie": {"lat": 52.40, "lon": 16.92},
            "DE_Bavaria": {"lat": 48.79, "lon": 11.61},
            "DE_LowerSaxony": {"lat": 52.63, "lon": 9.84},
            "FR_Beauce": {"lat": 48.44, "lon": 1.51},
            "FR_Bordeaux": {"lat": 44.83, "lon": -0.57},
            "RO_Wallachia": {"lat": 44.42, "lon": 26.10},
            "RO_Moldavia": {"lat": 46.56, "lon": 26.91},
            "HU_Puszta": {"lat": 47.16, "lon": 19.50},
            "IT_PoValley": {"lat": 45.07, "lon": 7.68},
            "ES_Andalusia": {"lat": 37.38, "lon": -5.98},
            "ES_CastillaLeon": {"lat": 41.65, "lon": -4.72},
            "NL_Flevoland": {"lat": 52.52, "lon": 5.47},
            "UK_Lincolnshire": {"lat": 53.23, "lon": -0.54},
            "US_Iowa": {"lat": 41.87, "lon": -93.60},
            "US_Kansas": {"lat": 39.01, "lon": -98.48},
            "US_Illinois": {"lat": 40.63, "lon": -89.39},
            "US_Nebraska": {"lat": 41.49, "lon": -99.90},
            "US_California_CentralValley": {"lat": 36.77, "lon": -119.41},
            "US_NorthDakota": {"lat": 47.55, "lon": -101.00},
            "US_Minnesota": {"lat": 46.72, "lon": -94.68},
            "CA_Saskatchewan": {"lat": 52.93, "lon": -106.45},
            "CA_Alberta": {"lat": 53.93, "lon": -116.57},
            "CA_Manitoba": {"lat": 49.89, "lon": -97.13},
            "BR_MatoGrosso": {"lat": -12.68, "lon": -56.92},
            "BR_Parana": {"lat": -25.25, "lon": -52.02},
            "BR_Goias": {"lat": -15.82, "lon": -49.84},
            "AR_BuenosAires": {"lat": -38.41, "lon": -63.61},
            "AR_Cordoba": {"lat": -31.42, "lon": -64.18},
            "AR_SantaFe": {"lat": -31.61, "lon": -60.69},
            "AR_LaPampa": {"lat": -36.61, "lon": -64.28},
            "CN_Henan": {"lat": 33.88, "lon": 113.61},
            "CN_Heilongjiang": {"lat": 45.75, "lon": 126.63},
            "CN_Shandong": {"lat": 36.65, "lon": 117.12},
            "CN_Jilin": {"lat": 43.81, "lon": 126.55},
            "IN_Punjab": {"lat": 30.73, "lon": 76.77},
            "IN_MadhyaPradesh": {"lat": 23.47, "lon": 77.94},
            "IN_UttarPradesh": {"lat": 26.84, "lon": 80.94},
            "KZ_Kostanay": {"lat": 53.21, "lon": 63.63},
            "KZ_Akmola": {"lat": 51.16, "lon": 71.47},
            "TR_Konya": {"lat": 37.87, "lon": 32.48},
            "ZA_FreeState": {"lat": -29.08, "lon": 26.15},
            "ZA_WesternCape": {"lat": -33.92, "lon": 18.42},
            "AU_NewSouthWales": {"lat": -31.84, "lon": 145.61},
            "AU_WesternAustralia": {"lat": -31.95, "lon": 115.86},
            "AU_Victoria": {"lat": -37.02, "lon": 144.96},
            "EG_NileDelta": {"lat": 30.04, "lon": 31.23},
        }

    def _download_single_location(
        self, args: Tuple
    ) -> Optional[Tuple[str, pd.DataFrame]]:
        location_name, coords, start_date, end_date, params_str = args

        time.sleep(random.uniform(0.1, 0.2))

        url = (
            f"{self.base_url}?"
            f"parameters={params_str}&"
            f"community=AG&"
            f"longitude={coords['lon']}&"
            f"latitude={coords['lat']}&"
            f"start={start_date}&"
            f"end={end_date}&"
            f"format=CSV"
        )

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=90)

                if response.status_code == 429:
                    time.sleep(5 + attempt * 2)
                    continue

                response.raise_for_status()

                content_text = response.text

                header_idx = -1
                lines = content_text.splitlines()
                for i, line in enumerate(lines):
                    if "YEAR" in line and "DOY" in line:
                        header_idx = i
                        break

                if header_idx == -1:
                    raise ValueError("Header not found")

                df = pd.read_csv(io.StringIO(content_text), header=header_idx)

                if "YEAR" in df.columns and "DOY" in df.columns:
                    df["Date"] = pd.to_datetime(
                        df["YEAR"] * 1000 + df["DOY"], format="%Y%j"
                    )
                    df.set_index("Date", inplace=True)
                    df = df.replace(-999, np.nan)
                    return (location_name, df)
                else:
                    raise ValueError("YEAR/DOY columns missing")

            except Exception as e:
                if attempt == max_attempts - 1:
                    return None
                time.sleep(2)

        return None

    def download_data_parallel(
        self, start_date: str, end_date: str, workers: int = 4
    ) -> "ACVIDataDownloader":
        print(f"Initializing parallel download")
        print(f"  Locations: {len(self.locations)}")
        print(f"  Workers: {workers}")
        print(f"  Period: {start_date} - {end_date}")
        print()

        params_str = ",".join(self.parameters)

        tasks = []
        for location, coords in self.locations.items():
            tasks.append((location, coords, start_date, end_date, params_str))

        successful = 0
        failed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_location = {
                executor.submit(self._download_single_location, task): task[0]
                for task in tasks
            }

            for i, future in enumerate(
                concurrent.futures.as_completed(future_to_location), 1
            ):
                location_name = future_to_location[future]
                try:
                    result = future.result()
                    if result:
                        name, df = result
                        self.data_store[name] = df
                        successful += 1
                        status = "OK"
                    else:
                        failed += 1
                        status = "FAILED"

                    print(
                        f"[{i:2d}/{len(self.locations)}] {location_name:30s} {status}",
                        end="\r",
                    )

                except Exception as exc:
                    failed += 1
                    print(f"\n[ERROR] {location_name}: {exc}")

        print()
        print(f"\nDownload complete: {successful} successful, {failed} failed")
        return self

    def save_data(self):
        if not self.data_store:
            print("No data to save")
            return

        print(f"\nSaving {len(self.data_store)} datasets...")

        for location, df in self.data_store.items():
            location_dir = self.output_dir / location
            location_dir.mkdir(exist_ok=True)

            start_year = df.index.min().strftime("%Y")
            end_year = df.index.max().strftime("%Y")
            filename = f"acvi_{location}_{start_year}-{end_year}.csv"
            filepath = location_dir / filename

            df.to_csv(filepath)

        print(f"Data saved to: {self.output_dir}")


if __name__ == "__main__":
    START_DATE = "20090101"
    END_DATE = "20231231"
    WORKERS = 12

    downloader = ACVIDataDownloader(output_dir="acvi_global_dataset_parallel")
    downloader.download_data_parallel(
        start_date=START_DATE, end_date=END_DATE, workers=WORKERS
    )
    downloader.save_data()
