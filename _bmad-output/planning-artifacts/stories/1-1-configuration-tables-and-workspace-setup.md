---
title: 'Story 1.1: Configuration Tables & Workspace Environment Setup'
type: 'chore'
created: '10-20-2026'
status: 'done'
epic: 1
story: 1
story_key: '1-1-configuration-tables-and-workspace-setup'
---

# Story 1.1: Configuration Tables & Workspace Environment Setup

## Intent
**Problem:** Downstream spatial algorithms, factory mapping, and simulation pipelines require centralized, immutable reference tables and repository hygiene.
**Approach:** Define standardized CSV configuration tables for factories, product-factory mapping, destination centroids (US and Canadian provinces), generator YAML parameters, and exclude raw data via `.gitignore`.

## User Story
As an operations analyst and developer,
I want standardized reference tables for factories, product mappings, geographic centroids, and generator parameters,
So that all downstream spatial and simulation algorithms rely on single sources of truth.

## Acceptance Criteria
- **Given** the workspace root,
- **When** the configuration tables are loaded,
- **Then** `config/factories.csv` contains all 5 production facilities with valid coordinates,
- **And** `config/product_factory.csv` maps all 15 products to the 5 facilities,
- **And** `config/geographic_centroids.csv` contains all 59 destinations (49 US jurisdictions + 10 Canadian provinces),
- **And** `config/generator.yaml` defines empirical distributions, 5 seeds (`[42, 101, 202, 303, 404]`), and stress injection parameters,
- **And** `.gitignore` excludes `data/original/` and `data/derived/surrogate_key_mapping.csv`.

## Implementation Files
- `config/factories.csv`
- `config/product_factory.csv`
- `config/geographic_centroids.csv`
- `config/generator.yaml`
- `.gitignore`
- `tests/test_architecture.py::test_config_files_present_and_valid`
- `tests/test_architecture.py::test_gitignore_data_separation`
