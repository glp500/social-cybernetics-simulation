"""Incremental NetCDF persistence for complete ecological spatial histories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from netCDF4 import Dataset
from numpy.typing import NDArray

from social_cybernetics.config import SimulationConfig
from social_cybernetics.domain import initialize_resources
from social_cybernetics.persistence_errors import BundleValidationError

SPATIAL_SCHEMA_VERSION = "scs-spatial-history/v0.1.0"

type FloatArray = NDArray[np.float64]
type IntArray = NDArray[np.int64]

_DYNAMIC_VARIABLES = {
    "resource_stock": np.dtype("float64"),
    "effective_capacity": np.dtype("float64"),
    "effective_regeneration": np.dtype("float64"),
    "recovery_remaining": np.dtype("int64"),
}
_STATIC_VARIABLES = {
    "baseline_capacity": np.dtype("float64"),
    "baseline_regeneration": np.dtype("float64"),
}
_COORDINATES = {"tick", "x", "y"}


def _float_array(name: str, value: NDArray[Any], shape: tuple[int, int]) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != shape:
        raise BundleValidationError(f"{name} shape must be {shape}, got {array.shape}")
    if not np.all(np.isfinite(array)) or np.any(array < 0):
        raise BundleValidationError(f"{name} must contain finite nonnegative values")
    return array


def _int_array(name: str, value: NDArray[Any], shape: tuple[int, int]) -> IntArray:
    array = np.asarray(value)
    if array.shape != shape:
        raise BundleValidationError(f"{name} shape must be {shape}, got {array.shape}")
    if not np.issubdtype(array.dtype, np.integer) or np.any(array < 0):
        raise BundleValidationError(f"{name} must contain nonnegative integers")
    return np.asarray(array, dtype=np.int64)


class SpatialHistoryWriter:
    """Append canonical tick snapshots to one bounded-memory NetCDF stream."""

    def __init__(self, path: Path, config: SimulationConfig) -> None:
        self.path = Path(path)
        self.config = config
        self.shape = (config.world.width, config.world.height)
        self.snapshot_count = 0
        self._closed = False
        self._baseline_capacity: FloatArray | None = None
        self._baseline_regeneration: FloatArray | None = None
        self._dataset = Dataset(self.path, "w", format="NETCDF4")
        try:
            self._initialize_dataset()
        except Exception:
            self._dataset.close()
            raise

    def _initialize_dataset(self) -> None:
        dataset = self._dataset
        width, height = self.shape
        dataset.setncattr("schema_version", SPATIAL_SCHEMA_VERSION)
        dataset.setncattr("model_schema_version", self.config.schema_version)
        dataset.setncattr("axis_order", "tick,x,y")
        dataset.setncattr("units", "abstract_dimensionless")
        dataset.createDimension("tick", None)
        dataset.createDimension("x", width)
        dataset.createDimension("y", height)
        tick = dataset.createVariable("tick", "i8", ("tick",), fill_value=False)
        x = dataset.createVariable("x", "i8", ("x",), fill_value=False)
        y = dataset.createVariable("y", "i8", ("y",), fill_value=False)
        tick.setncattr("long_name", "completed model tick")
        x.setncattr("long_name", "Mesa x coordinate")
        y.setncattr("long_name", "Mesa y coordinate")
        x[:] = np.arange(width, dtype=np.int64)
        y[:] = np.arange(height, dtype=np.int64)

        spatial_chunks = (min(width, 64), min(height, 64))
        dynamic_chunks = (1, *spatial_chunks)
        for name, dtype in _DYNAMIC_VARIABLES.items():
            dataset.createVariable(
                name,
                dtype,
                ("tick", "x", "y"),
                compression="zlib",
                complevel=4,
                shuffle=True,
                fletcher32=True,
                chunksizes=dynamic_chunks,
                fill_value=False,
            )
        for name, dtype in _STATIC_VARIABLES.items():
            dataset.createVariable(
                name,
                dtype,
                ("x", "y"),
                compression="zlib",
                complevel=4,
                shuffle=True,
                fletcher32=True,
                chunksizes=spatial_chunks,
                fill_value=False,
            )

    def record(
        self,
        *,
        tick: int,
        resource_stock: NDArray[Any],
        effective_capacity: NDArray[Any],
        effective_regeneration: NDArray[Any],
        recovery_remaining: NDArray[Any],
        baseline_capacity: NDArray[Any],
        baseline_regeneration: NDArray[Any],
    ) -> None:
        """Validate and synchronously append one tick in canonical order."""

        if self._closed:
            raise BundleValidationError("cannot record into a closed spatial history")
        if isinstance(tick, bool) or not isinstance(tick, int) or tick != self.snapshot_count:
            raise BundleValidationError(
                f"expected spatial tick {self.snapshot_count}, received {tick}"
            )

        stock = _float_array("resource_stock", resource_stock, self.shape)
        capacity = _float_array("effective_capacity", effective_capacity, self.shape)
        regeneration = _float_array("effective_regeneration", effective_regeneration, self.shape)
        remaining = _int_array("recovery_remaining", recovery_remaining, self.shape)
        baseline_capacity_array = _float_array("baseline_capacity", baseline_capacity, self.shape)
        baseline_regeneration_array = _float_array(
            "baseline_regeneration", baseline_regeneration, self.shape
        )
        if np.any(stock > baseline_capacity_array) or np.any(capacity > baseline_capacity_array):
            raise BundleValidationError(
                "spatial stock and effective capacity exceed baseline capacity"
            )
        if np.any(regeneration > baseline_regeneration_array):
            raise BundleValidationError("effective regeneration exceeds baseline regeneration")

        if self.snapshot_count == 0:
            self._baseline_capacity = np.array(baseline_capacity_array, copy=True)
            self._baseline_regeneration = np.array(baseline_regeneration_array, copy=True)
            self._dataset.variables["baseline_capacity"][:, :] = baseline_capacity_array
            self._dataset.variables["baseline_regeneration"][:, :] = baseline_regeneration_array
        else:
            saved_capacity = self._baseline_capacity
            saved_regeneration = self._baseline_regeneration
            if saved_capacity is None or saved_regeneration is None:
                raise BundleValidationError("spatial baseline state is unavailable")
            if not np.array_equal(baseline_capacity_array, saved_capacity):
                raise BundleValidationError("baseline_capacity changed during the run")
            if not np.array_equal(baseline_regeneration_array, saved_regeneration):
                raise BundleValidationError("baseline_regeneration changed during the run")

        index = self.snapshot_count
        self._dataset.variables["tick"][index] = tick
        self._dataset.variables["resource_stock"][index, :, :] = stock
        self._dataset.variables["effective_capacity"][index, :, :] = capacity
        self._dataset.variables["effective_regeneration"][index, :, :] = regeneration
        self._dataset.variables["recovery_remaining"][index, :, :] = remaining
        self.snapshot_count += 1
        self._dataset.sync()

    def close(self) -> None:
        if not self._closed:
            self._dataset.close()
            self._closed = True

    def __enter__(self) -> SpatialHistoryWriter:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def validate_spatial_history(
    path: Path,
    *,
    config: SimulationConfig,
    completed_ticks: int,
) -> None:
    """Validate a closed spatial artifact without loading dynamic arrays."""

    expected_snapshots = completed_ticks + 1
    try:
        with Dataset(path, "r") as dataset:
            if dataset.getncattr("schema_version") != SPATIAL_SCHEMA_VERSION:
                raise BundleValidationError("spatial history schema is unsupported")
            if dataset.getncattr("model_schema_version") != config.schema_version:
                raise BundleValidationError("spatial model schema differs from configuration")
            if dataset.getncattr("axis_order") != "tick,x,y":
                raise BundleValidationError("spatial axis order is invalid")
            if set(dataset.dimensions) != {"tick", "x", "y"}:
                raise BundleValidationError("spatial dimensions differ from contract")
            if not dataset.dimensions["tick"].isunlimited():
                raise BundleValidationError("spatial tick dimension must be unlimited")
            if len(dataset.dimensions["tick"]) != expected_snapshots:
                raise BundleValidationError("spatial snapshot count differs from completed ticks")
            if (
                len(dataset.dimensions["x"]) != config.world.width
                or len(dataset.dimensions["y"]) != config.world.height
            ):
                raise BundleValidationError("spatial world dimensions differ from configuration")

            expected_variables = _COORDINATES | set(_DYNAMIC_VARIABLES) | set(_STATIC_VARIABLES)
            if set(dataset.variables) != expected_variables:
                raise BundleValidationError("spatial variables differ from contract")
            variable_contracts = {
                "tick": (np.dtype("int64"), ("tick",)),
                "x": (np.dtype("int64"), ("x",)),
                "y": (np.dtype("int64"), ("y",)),
                **{name: (dtype, ("tick", "x", "y")) for name, dtype in _DYNAMIC_VARIABLES.items()},
                **{name: (dtype, ("x", "y")) for name, dtype in _STATIC_VARIABLES.items()},
            }
            for name, (dtype, dimensions) in variable_contracts.items():
                variable = dataset.variables[name]
                if variable.dtype != dtype or variable.dimensions != dimensions:
                    raise BundleValidationError(f"spatial variable contract differs: {name}")

            np.testing.assert_array_equal(
                dataset.variables["tick"][:], np.arange(expected_snapshots, dtype=np.int64)
            )
            np.testing.assert_array_equal(
                dataset.variables["x"][:], np.arange(config.world.width, dtype=np.int64)
            )
            np.testing.assert_array_equal(
                dataset.variables["y"][:], np.arange(config.world.height, dtype=np.int64)
            )
            _, expected_capacity = initialize_resources(
                (config.world.width, config.world.height),
                initial_stock=config.resources.initial_stock,
                capacity=config.resources.capacity,
            )
            expected_regeneration = np.full(
                expected_capacity.shape,
                config.resources.regeneration_rate,
                dtype=np.float64,
            )
            np.testing.assert_array_equal(
                dataset.variables["baseline_capacity"][:], expected_capacity
            )
            np.testing.assert_array_equal(
                dataset.variables["baseline_regeneration"][:], expected_regeneration
            )
    except BundleValidationError:
        raise
    except Exception as error:
        raise BundleValidationError("spatial history violates its data contract") from error
