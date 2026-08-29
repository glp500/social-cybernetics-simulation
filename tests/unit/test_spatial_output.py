from pathlib import Path

import numpy as np
import pytest
from netCDF4 import Dataset

from social_cybernetics.config import AgentConfig, SimulationConfig, WorldConfig
from social_cybernetics.persistence import BundleValidationError
from social_cybernetics.spatial_output import (
    SPATIAL_SCHEMA_VERSION,
    SpatialHistoryWriter,
    validate_spatial_history,
)


def _arrays(value: float = 10.0) -> dict[str, np.ndarray]:
    shape = (2, 1)
    return {
        "resource_stock": np.full(shape, value, dtype=np.float64),
        "effective_capacity": np.full(shape, 10.0, dtype=np.float64),
        "effective_regeneration": np.full(shape, 0.1, dtype=np.float64),
        "recovery_remaining": np.zeros(shape, dtype=np.int64),
        "baseline_capacity": np.full(shape, 10.0, dtype=np.float64),
        "baseline_regeneration": np.full(shape, 0.1, dtype=np.float64),
    }


def _config() -> SimulationConfig:
    return SimulationConfig(
        duration=1,
        world=WorldConfig(width=2, height=1),
        agents=AgentConfig(count=0, initial_positions=()),
    )


def test_streamed_spatial_history_has_the_complete_versioned_schema(tmp_path: Path) -> None:
    path = tmp_path / "spatial.nc"
    config = _config()
    writer = SpatialHistoryWriter(path, config)
    writer.record(tick=0, **_arrays())
    writer.record(tick=1, **_arrays(8.0))
    writer.close()

    validate_spatial_history(path, config=config, completed_ticks=1)

    with Dataset(path, "r") as dataset:
        assert dataset.getncattr("schema_version") == SPATIAL_SCHEMA_VERSION
        assert dataset.getncattr("axis_order") == "tick,x,y"
        assert set(dataset.dimensions) == {"tick", "x", "y"}
        assert dataset.dimensions["tick"].isunlimited()
        assert len(dataset.dimensions["tick"]) == 2
        assert len(dataset.dimensions["x"]) == 2
        assert len(dataset.dimensions["y"]) == 1
        assert set(dataset.variables) == {
            "tick",
            "x",
            "y",
            "resource_stock",
            "effective_capacity",
            "effective_regeneration",
            "recovery_remaining",
            "baseline_capacity",
            "baseline_regeneration",
        }
        assert dataset.variables["resource_stock"].dimensions == ("tick", "x", "y")
        assert dataset.variables["recovery_remaining"].dtype == np.dtype("int64")
        assert dataset.variables["baseline_capacity"].dimensions == ("x", "y")
        np.testing.assert_array_equal(dataset.variables["tick"][:], [0, 1])
        np.testing.assert_allclose(dataset.variables["resource_stock"][:, :, 0], [[10, 10], [8, 8]])
        np.testing.assert_allclose(dataset.variables["baseline_capacity"][:, :], 10.0)


def test_spatial_writer_requires_canonical_consecutive_ticks(tmp_path: Path) -> None:
    writer = SpatialHistoryWriter(
        tmp_path / "spatial.nc",
        _config(),
    )
    writer.record(tick=0, **_arrays())

    with pytest.raises(BundleValidationError, match="expected spatial tick 1"):
        writer.record(tick=2, **_arrays())

    writer.close()


def test_spatial_writer_rejects_wrong_shapes_and_changed_baselines(tmp_path: Path) -> None:
    writer = SpatialHistoryWriter(
        tmp_path / "spatial.nc",
        _config(),
    )

    wrong_shape = _arrays()
    wrong_shape["resource_stock"] = np.ones((1, 2), dtype=np.float64)
    with pytest.raises(BundleValidationError, match="resource_stock shape"):
        writer.record(tick=0, **wrong_shape)

    writer.record(tick=0, **_arrays())
    changed_baseline = _arrays(8.0)
    changed_baseline["baseline_capacity"] = np.full((2, 1), 11.0)
    with pytest.raises(BundleValidationError, match="baseline_capacity changed"):
        writer.record(tick=1, **changed_baseline)

    writer.close()


def test_spatial_validation_rejects_an_incomplete_tick_history(tmp_path: Path) -> None:
    path = tmp_path / "spatial.nc"
    config = _config()
    writer = SpatialHistoryWriter(path, config)
    writer.record(tick=0, **_arrays())
    writer.close()

    with pytest.raises(BundleValidationError, match="snapshot count"):
        validate_spatial_history(path, config=config, completed_ticks=1)
