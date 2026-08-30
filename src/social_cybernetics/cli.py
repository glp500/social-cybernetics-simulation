"""Stable command-line boundary for configuration and deterministic runs."""

import json
from pathlib import Path
from typing import Annotated, Any, NoReturn

import typer
import yaml

from social_cybernetics.batch import execute_batch
from social_cybernetics.batch_config import ResolvedBatchSpecification, load_batch_specification
from social_cybernetics.config import SimulationConfig, load_config
from social_cybernetics.domain import InvariantViolationError
from social_cybernetics.persistence import (
    BundlePublicationError,
    RunBundleSession,
    RunRecords,
)
from social_cybernetics.runtime.mesa import SugarscapeModel
from social_cybernetics.runtime.mesa.model import SpatialSnapshotSink
from social_cybernetics.sensitivity import ResolvedSensitivityDesign, load_sensitivity_design

app = typer.Typer(
    help="Validate and run the Social Cybernetics Sugarscape model.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def _json_line(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _configuration_error(error: Exception) -> NoReturn:
    typer.echo(
        _json_line({"error": "invalid_configuration", "message": str(error)}),
        err=True,
    )
    raise typer.Exit(code=2)


def _output_error(error: Exception) -> NoReturn:
    typer.echo(
        _json_line({"error": "output_failure", "message": str(error)}),
        err=True,
    )
    raise typer.Exit(code=1)


def _read_config(path: Path) -> SimulationConfig:
    try:
        return load_config(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        _configuration_error(error)


def _read_batch_specification(path: Path) -> ResolvedBatchSpecification:
    try:
        return load_batch_specification(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        typer.echo(
            _json_line({"error": "invalid_batch_specification", "message": str(error)}),
            err=True,
        )
        raise typer.Exit(code=2) from error


def _read_sensitivity_design(path: Path) -> ResolvedSensitivityDesign:
    try:
        return load_sensitivity_design(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        typer.echo(
            _json_line({"error": "invalid_sensitivity_specification", "message": str(error)}),
            err=True,
        )
        raise typer.Exit(code=2) from error


def _execute_model(
    config: SimulationConfig,
    *,
    spatial_sink: SpatialSnapshotSink | None = None,
) -> tuple[SugarscapeModel, dict[str, Any]]:
    try:
        model = SugarscapeModel(config, spatial_sink=spatial_sink)
        model.run()
        return model, model.summary()
    except InvariantViolationError as error:
        typer.echo(_json_line({"error": "invariant_failure", "message": str(error)}), err=True)
        raise typer.Exit(code=1) from error
    except BundlePublicationError:
        raise
    except Exception as error:  # pragma: no cover - defensive process boundary
        typer.echo(
            _json_line({"error": "runtime_failure", "message": str(error)}),
            err=True,
        )
        raise typer.Exit(code=1) from error


@app.command()
def validate(
    config: Annotated[Path, typer.Option("--config", help="YAML configuration to validate.")],
) -> None:
    """Validate only implemented schema variants without running the model."""

    validated = _read_config(config)
    typer.echo(
        _json_line(
            {
                "schema_version": validated.schema_version,
                "status": "valid",
                "study": validated.study,
            }
        )
    )


@app.command()
def run(
    config: Annotated[Path, typer.Option("--config", help="YAML configuration to execute.")],
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Publish a validated persistent run bundle."),
    ] = None,
) -> None:
    """Execute a run, optionally publish its records, and print one JSON summary."""

    validated = _read_config(config)
    if output is None:
        _, summary = _execute_model(validated)
        typer.echo(_json_line(summary))
        return
    try:
        with RunBundleSession(output, validated) as session:
            model, summary = _execute_model(validated, spatial_sink=session)
            session.publish(
                summary=summary,
                records=RunRecords(
                    model=model.model_records,
                    cohort=model.cohort_records,
                    agent_events=model.event_records,
                    shock_events=model.shock_event_snapshots,
                    shock_exposures=model.shock_exposures,
                    cell_damage=model.cell_damage_applications,
                ),
                rng_provenance=model.rng_provenance,
            )
    except (BundlePublicationError, OSError, ValueError) as error:
        _output_error(error)
    typer.echo(_json_line(summary))


@app.command()
def batch(
    specification: Annotated[
        Path,
        typer.Option("--spec", help="Ordered batch YAML specification to execute."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", help="Publish the complete validated batch attempt."),
    ],
) -> None:
    """Execute ordered runs sequentially and publish JSON and Parquet indexes."""

    validated = _read_batch_specification(specification)
    _execute_batch(validated, output)


def _execute_batch(specification: ResolvedBatchSpecification, output: Path) -> None:
    try:
        result = execute_batch(specification, output)
    except Exception as error:  # pragma: no cover - defensive aggregate-output boundary
        _output_error(error)
    typer.echo(_json_line(result.summary()))
    if result.failed_runs:
        raise typer.Exit(code=1)


@app.command()
def sensitivity(
    specification: Annotated[
        Path,
        typer.Option("--spec", help="Seeded Morris sensitivity YAML to execute."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", help="Publish the generated batch attempt."),
    ],
) -> None:
    """Generate validated sensitivity runs and execute them as one ordinary batch."""

    design = _read_sensitivity_design(specification)
    _execute_batch(design.batch, output)


if __name__ == "__main__":  # pragma: no cover
    app()
