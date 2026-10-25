# Church of God Map — Florida and the Southeast

A project I made because the official Church of God website is really not great when trying to find a location.

Updated monthly.

**Live map:** https://78tacos.github.io/cog-locations/

## Use the map

Open `index.html` for the radius search. Open `directory.html` for the printable list. Both are static files at the repository root, which is what GitHub Pages serves from `main`. They load `churches.js`. `churches.json` is the same list.

Every record keeps the church name, pastor, street address, city, state, ZIP, phone, website, and email, along with map coordinates. Pastor and email stay in the data.

## Refresh the directory

`scripts/refresh.py` rewrites `churches.json` and `churches.js`:

1. It downloads each Florida page from the [Church of God locator](https://churchofgod.org/church_locator/churches.php?state=FL), about 3 seconds apart.
2. It reads the name, pastor, address, city, state, ZIP, phone, website, and email by walking the `<p>` text on each page (`parse_churches`).
3. It geocodes street addresses with the [US Census Bureau batch geocoder](https://geocoding.geo.census.gov/geocoder/). A batch miss runs `fallback_geocode`: Census one-line, then Nominatim, then ArcGIS. The last resort is that ZIP's center, stored with `"approx": true`.
4. The cache reuses a saved pin only when `"approx"` is false. Approximate pins are geocoded again.
5. It keeps every Florida church and records its county. A church that can't be placed is still listed in the directory without a pin.

```bash
python3 scripts/refresh.py
```

The script defaults to Florida. Additional USPS state codes can be passed (`python3 scripts/refresh.py FL GA AL SC NC TN MS`). The published directory now includes Florida and the Southeast states (Georgia, Alabama, South Carolina, North Carolina, Tennessee, and Mississippi). `python3 scripts/refresh.py FL GA AL SC NC TN MS` rebuilds it. The monthly job runs `python scripts/refresh.py FL GA AL SC NC TN MS` so the next refresh keeps every published state.

The download pauses between pages, so a full run takes a few minutes. Review the diff before merging. Pages publishes the root files on `main`, and the live map is https://78tacos.github.io/cog-locations/.

## Monthly update

`.github/workflows/refresh.yml` runs at 13:00 UTC on the 1st of each month. It can also be started by hand with **workflow_dispatch**. The workflow runs the script and commits to main only when the data changed.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
