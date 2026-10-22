---
title: 'Story 1.4: Factory Assignment, Centroid Joins & Vectorized Haversine Distance'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 1
story: 4
story_key: '1-4-factory-assignment-centroid-joins-and-haversine-distance'
---

# Story 1.4: Factory Assignment, Centroid Joins & Vectorized Haversine Distance

## Intent
**Problem:** Order lines need to be mapped to production plants, validated against order grains, and geocoded with shipping distances for both US and Canadian destinations.
**Approach:** Create a mapping module that assigns the 15 products to 5 facilities, enforces 1 factory per Order ID across all 8,549 clean order lines, joins centroids, and computes great-circle distances via vectorized Haversine ($R = 6,371.0088$ km).

## User Story
As a logistics engineer,
I want to map products to factories, join destination centroids, and compute great-circle shipping distances in kilometers,
So that route-level spatial analytics and distance-sensitive simulations have accurate inputs.

## Acceptance Criteria
- **Given** the deduplicated dataset,
- **When** `src/map_factories.py::process_mapping_pipeline()` runs,
- **Then** 100% of products map to factories with zero unmapped lines,
- **And** every Order ID maps to exactly 1 factory across all 8,549 clean order lines,
- **And** 5,067 customer shipments are identified (1,702 multi-factory [33.6%], 2,240 multi-order-line),
- **And** vectorized Haversine calculates non-zero distance for all US and Canadian destinations,
- **And** `route_key` (`Factory -> State/Province`) and `route_key_region` (`Factory -> Region`) are generated.

## Implementation Files
- `src/map_factories.py`
- `tests/test_mapping.py::test_factory_and_product_configs`
- `tests/test_mapping.py::test_product_mapping_coverage`
- `tests/test_mapping.py::test_order_line_single_factory_invariant`
- `tests/test_mapping.py::test_customer_shipment_grains`
- `tests/test_mapping.py::test_haversine_distance_math`
- `tests/test_mapping.py::test_distance_computation_and_centroids`
- `tests/test_mapping.py::test_route_keys`
