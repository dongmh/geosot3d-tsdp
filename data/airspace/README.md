# Airspace polygons

This directory holds the manually digitised no-fly and restricted-flight
zones for the Xi'an experiment. Each zone is stored as a single GeoJSON
feature with the following properties:

| Property        | Type    | Description                                       |
| --------------- | ------- | ------------------------------------------------- |
| `name`          | string  | Human-readable zone name                          |
| `kind`          | string  | One of: `permanent_no_fly`, `restricted`, `weather` |
| `weight`        | number  | Domain weight from Table 1 (1.0 / 0.9 / 0.5-0.6)  |
| `source`        | string  | Public source URL or document reference           |
| `digitised_on`  | string  | ISO date when the polygon was digitised           |

## Files

| File                         | Zone                              |
| ---------------------------- | --------------------------------- |
| `xian_no_fly_belltower.geojson` | Bell Tower 500-m no-fly cylinder  |
| `xian_no_fly_pagoda.geojson`    | Giant Wild Goose Pagoda no-fly    |
| `xian_restricted_north.geojson` | Northern restricted-flight zone   |
| `xian_restricted_east.geojson`  | Eastern restricted-flight zone    |
| `xian_weather_zone1.geojson`    | Weather-risk zone (variable)      |
| `xian_weather_zone2.geojson`    | Weather-risk zone (variable)      |

## Provenance

These polygons were transcribed from the Civil Aviation Administration of
China public AIP and cross-checked against the DJI FlySafe map snapshot
of 2025-11-01. They are NOT authoritative for actual flight planning
purposes; treat them as research data only.

If you find a polygon that disagrees with the current AIP, please open
an Issue with the source citation and we will update.
