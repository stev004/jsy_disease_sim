from pathlib import Path

from jersey_outbreak.data_pipeline import build_canonical

ROOT = Path(__file__).resolve().parents[1]


def test_housing_blank_cells_are_quality_warnings(tmp_path: Path) -> None:
    report = build_canonical(ROOT, tmp_path / "processed")

    def warning(source: str, row: str, column: str) -> str:
        return (
            f'census blank cell omitted: {source} row "{row}" '
            f'column "{column}" (publisher states no meaning for a blank)'
        )

    expected = {
        warning(
            "census_2021_household_type_tenure_csv",
            "Couple (one pensioner)",
            "Registered lodging house",
        ),
        warning(
            "census_2021_household_type_tenure_csv",
            "Couple (one pensioner)",
            "Private lodging",
        ),
        warning(
            "census_2021_household_type_tenure_csv",
            "Two or more pensioners",
            "Registered lodging house",
        ),
        warning(
            "census_2021_household_property_type_csv",
            "Temporary Structure/Tent, boat or PortakabinTM",
            "Social housing rent",
        ),
        warning(
            "census_2021_household_property_type_csv",
            "Temporary Structure/Tent, boat or PortakabinTM",
            "Qualified private rent",
        ),
    }

    assert expected <= set(report["warnings"])
