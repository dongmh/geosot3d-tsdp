#!/usr/bin/env bash
# Download all public datasets needed for the Xi'an experiment.
#
# Prerequisites:
#   - NASA Earthdata Login account: https://urs.earthdata.nasa.gov/
#   - .netrc with Earthdata credentials (see https://disc.gsfc.nasa.gov/data-access)
#   - curl, gdal_translate, jq
#
# This script does NOT redistribute any data. It fetches from the original
# providers and caches the results under data/cache/.

set -euo pipefail

BBOX_LON_MIN=108.85
BBOX_LON_MAX=109.00
BBOX_LAT_MIN=34.18
BBOX_LAT_MAX=34.30

CACHE_DIR="$(dirname "$0")/cache"
mkdir -p "$CACHE_DIR"

echo "==> Downloading ASTER GDEM V3 tiles for Xi'an"
# Tile naming: ASTGTMV003_NXXEYYY (e.g., N34E108)
# We need N34E108 only.
DEM_TILE="ASTGTMV003_N34E108"
DEM_URL="https://e4ftl01.cr.usgs.gov/ASTT/ASTGTM.003/2000.03.01/${DEM_TILE}.zip"
DEM_ZIP="$CACHE_DIR/${DEM_TILE}.zip"

if [[ ! -f "$DEM_ZIP" ]]; then
  curl -nL -o "$DEM_ZIP" "$DEM_URL" || {
    echo "ERROR: Failed to download GDEM. Check your .netrc has Earthdata credentials." >&2
    exit 1
  }
fi

unzip -o "$DEM_ZIP" -d "$CACHE_DIR" >/dev/null
DEM_TIF="$CACHE_DIR/${DEM_TILE}_dem.tif"

echo "==> Clipping DEM to study bbox"
gdal_translate -projwin \
  $BBOX_LON_MIN $BBOX_LAT_MAX $BBOX_LON_MAX $BBOX_LAT_MIN \
  "$DEM_TIF" "$CACHE_DIR/gdem_xian.tif" >/dev/null

echo "==> Fetching OpenStreetMap buildings via Overpass API"
OSM_OUT="$CACHE_DIR/osm_xian_buildings.geojson"

OVERPASS_QUERY=$(cat <<EOF
[out:json][timeout:120];
(
  way["building"](${BBOX_LAT_MIN},${BBOX_LON_MIN},${BBOX_LAT_MAX},${BBOX_LON_MAX});
  relation["building"](${BBOX_LAT_MIN},${BBOX_LON_MIN},${BBOX_LAT_MAX},${BBOX_LON_MAX});
);
out geom;
EOF
)

curl -sG "https://overpass-api.de/api/interpreter" \
  --data-urlencode "data=$OVERPASS_QUERY" \
  -o "$CACHE_DIR/osm_xian_raw.json"

# Convert to GeoJSON via osmtogeojson (npm install -g osmtogeojson)
if command -v osmtogeojson >/dev/null 2>&1; then
  osmtogeojson "$CACHE_DIR/osm_xian_raw.json" > "$OSM_OUT"
else
  echo "WARNING: osmtogeojson not found; raw JSON saved at $CACHE_DIR/osm_xian_raw.json" >&2
  echo "         Install with: npm install -g osmtogeojson" >&2
fi

echo "==> Done. Cached files in $CACHE_DIR :"
ls -lh "$CACHE_DIR" | sed 's/^/    /'

echo
echo "Next: run the experiment with"
echo "    python -m experiments.xian --output results/xian.csv"
