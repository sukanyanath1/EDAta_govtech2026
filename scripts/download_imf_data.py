import requests
import pandas as pd
import os
from typing import Optional


def get_imf_data(
    country_code_list: list[str],
    indicator_list: list[str],
    years: Optional[list[int]] = None,
) -> pd.DataFrame:
    if years is None:
        years = list(range(2000, 2028))

    rows = []

    for country_code in country_code_list:
        for indicator in indicator_list:
            url = (
                f"https://www.imf.org/external/datamapper/api/v1/{indicator}/{country_code}"
                f"?periods={','.join(map(str, years))}"
            )

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            values = (
                data.get("values", {})
                .get(indicator, {})
                .get(country_code, {})
            )

            row = {
                "WEO Country Code": country_code,
                "WEO Subject Code": indicator,
                "Country": data.get("countryName", country_code),
                "Subject Descriptor": data.get("indicatorName", indicator),
                "Units": data.get("units", ""),
                "Scale": data.get("scale", ""),
                "Country/Series-specific Notes": data.get("notes", ""),
            }

            for year in years:
                row[str(year)] = values.get(str(year), None)

            rows.append(row)

    return pd.DataFrame(rows)


def main():
    country_code_list = ["DEU", "CHE", "FRA", "ITA"]  # Germany, Switzerland, France, Italy

    indicator_list = [
        "NGDP_RPCH",   # Real GDP growth
        # add more indicators here
    ]

    df = get_imf_data(
        country_code_list=country_code_list,
        indicator_list=indicator_list,
        years=list(range(2000, 2028)),
    )

    output_dir = "data/imf"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "imf_data.csv")
    df.to_csv(output_path, index=False)

    print(f"Saved {len(df)} rows to {output_path}")


if __name__ == "__main__":
    main()