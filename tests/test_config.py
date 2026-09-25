from pathlib import Path

from global_heat_allocation.config import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_model_config_has_conserved_energy_units() -> None:
    config = load_config(ROOT / "config" / "model.yml")
    assert config["energy"]["canonical_unit"] == "GJ"
    assert config["energy"]["perturbation_gj"] > 0


def test_target_journal_is_journal_of_cleaner_production() -> None:
    config = load_config(ROOT / "config" / "model.yml")
    assert config["project"]["target_journal"] == "Journal of Cleaner Production"


def test_acquisition_sources_have_unique_immutable_paths() -> None:
    config = load_config(ROOT / "config" / "data_sources.yml")
    sources = [source for source in config["sources"] if source["acquire"]]
    keys = [source["key"] for source in sources]
    paths = [source["local_filename"] for source in sources]
    assert len(keys) == len(set(keys))
    assert len(paths) == len(set(paths))
    assert all(source["url"].startswith("https://") for source in sources)
