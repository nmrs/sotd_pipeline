"""Pytest configuration and shared fixtures for SOTD Pipeline tests."""

import tempfile
import shutil
from pathlib import Path
import pytest
import yaml


@pytest.fixture(scope="function")
def temp_data_dir():
    """Create a temporary data directory for tests."""
    temp_dir = tempfile.mkdtemp()
    temp_data_dir = Path(temp_dir) / "data"
    temp_data_dir.mkdir(parents=True)

    yield temp_data_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def temp_correct_matches_file(temp_data_dir):
    """Create a temporary correct_matches.yaml file for tests."""
    correct_matches_path = temp_data_dir / "correct_matches.yaml"

    # Create empty correct_matches.yaml
    with open(correct_matches_path, "w") as f:
        yaml.dump({}, f)

    return correct_matches_path


@pytest.fixture(scope="function")
def temp_brushes_file(temp_data_dir):
    """Create a temporary brushes.yaml file for tests."""
    brushes_path = temp_data_dir / "brushes.yaml"

    # Copy production brushes.yaml if it exists
    production_brushes = Path("data/brushes.yaml")
    if production_brushes.exists():
        shutil.copy(production_brushes, brushes_path)
    else:
        # Create minimal test brushes.yaml
        with open(brushes_path, "w") as f:
            yaml.dump({"brands": {}}, f)

    return brushes_path


@pytest.fixture(scope="function")
def temp_handles_file(temp_data_dir):
    """Create a temporary handles.yaml file for tests."""
    handles_path = temp_data_dir / "handles.yaml"

    # Copy production handles.yaml if it exists
    production_handles = Path("data/handles.yaml")
    if production_handles.exists():
        shutil.copy(production_handles, handles_path)
    else:
        # Create minimal test handles.yaml
        with open(handles_path, "w") as f:
            yaml.dump({"brands": {}}, f)

    return handles_path


@pytest.fixture(scope="function")
def temp_knots_file(temp_data_dir):
    """Create a temporary knots.yaml file for tests."""
    knots_path = temp_data_dir / "knots.yaml"

    # Copy production knots.yaml if it exists
    production_knots = Path("data/knots.yaml")
    if production_knots.exists():
        shutil.copy(production_knots, knots_path)
    else:
        # Create minimal test knots.yaml
        with open(knots_path, "w") as f:
            yaml.dump({"brands": {}}, f)

    return knots_path


@pytest.fixture(scope="function")
def temp_blades_file(temp_data_dir):
    """Create a temporary blades.yaml file for tests."""
    blades_path = temp_data_dir / "blades.yaml"

    # Copy production blades.yaml if it exists
    production_blades = Path("data/blades.yaml")
    if production_blades.exists():
        shutil.copy(production_blades, blades_path)
    else:
        # Create minimal test blades.yaml
        with open(blades_path, "w") as f:
            yaml.dump({"brands": {}}, f)

    return blades_path


@pytest.fixture(scope="function")
def temp_soaps_file(temp_data_dir):
    """Create a temporary soaps.yaml file for tests."""
    soaps_path = temp_data_dir / "soaps.yaml"

    # Copy production soaps.yaml if it exists
    production_soaps = Path("data/soaps.yaml")
    if production_soaps.exists():
        shutil.copy(production_soaps, soaps_path)
    else:
        # Create minimal test soaps.yaml
        with open(soaps_path, "w") as f:
            yaml.dump({"brands": {}}, f)

    return soaps_path


@pytest.fixture(scope="function")
def temp_razors_file(temp_data_dir):
    """Create a temporary razors.yaml file for tests."""
    razors_path = temp_data_dir / "razors.yaml"

    # Copy production razors.yaml if it exists
    production_razors = Path("data/razors.yaml")
    if production_razors.exists():
        shutil.copy(production_razors, razors_path)
    else:
        # Create minimal test razors.yaml
        with open(razors_path, "w") as f:
            yaml.dump({"brands": {}}, f)

    return razors_path


@pytest.fixture(scope="function")
def temp_brush_scoring_config_file(temp_data_dir):
    """Create a temporary brush_scoring_config.yaml file for tests."""
    config_path = temp_data_dir / "brush_scoring_config.yaml"

    # Copy production config if it exists
    production_config = Path("data/brush_scoring_config.yaml")
    if production_config.exists():
        shutil.copy(production_config, config_path)
    else:
        # Create minimal test config
        with open(config_path, "w") as f:
            yaml.dump({"scoring": {}}, f)

    return config_path


@pytest.fixture(scope="function")
def temp_brush_splits_file(temp_data_dir):
    """Create a temporary brush_splits.yaml file for tests."""
    splits_path = temp_data_dir / "brush_splits.yaml"

    # Copy production splits if it exists
    production_splits = Path("data/brush_splits.yaml")
    if production_splits.exists():
        shutil.copy(production_splits, splits_path)
    else:
        # Create minimal test splits
        with open(splits_path, "w") as f:
            yaml.dump({"splits": {}}, f)

    return splits_path


@pytest.fixture(scope="function")
def temp_extract_overrides_file(temp_data_dir):
    """Create a temporary extract_overrides.yaml file for tests."""
    overrides_path = temp_data_dir / "extract_overrides.yaml"

    # Copy production overrides if it exists
    production_overrides = Path("data/extract_overrides.yaml")
    if production_overrides.exists():
        shutil.copy(production_overrides, overrides_path)
    else:
        # Create minimal test overrides
        with open(overrides_path, "w") as f:
            yaml.dump({}, f)

    return overrides_path
