# ADR 0001: Separate the Scientific Model and Runtime

## Status

Accepted — 2026-08-28

## Context

The scientific claims must not become accidental consequences of Mesa APIs. Mechanisms also need
fast, framework-independent unit and property tests.

## Decision

Maintain an ODD+D scientific specification independently of software. Implement equations, state,
observations, beliefs, intents, gates, resolution, physiology, and records in a pure domain package.
Use a one-way Mesa adapter for space, time advancement, lifecycle, collection, and visualisation.

## Alternatives considered

- **Mesa-native domain:** fewer files, but framework state would become the model contract.
- **Multiple runtime adapters now:** replaceable, but unjustified before a second engine is needed.

## Consequences

Domain code cannot import Mesa or presentation/configuration libraries. Small explicit mapping code is
accepted at the runtime boundary. A Mesa upgrade must preserve domain contracts and regression traces.

