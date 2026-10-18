# Tampa Bay Church of God Map

A project I made because the official Church of God website is really not great when trying to find a location.

Updated monthly.

**Live map:** https://78tacos.github.io/tampa-churches/

## Use the map

Open `index.html` for the radius search. Open `directory.html` for the printable list. Both are static files at the repository root, which is what GitHub Pages serves from `main`. They load `churches.js`. `churches.json` is the same list.

Every record keeps the church name, pastor, street address, city, state, ZIP, phone, website, and email, along with map coordinates. Pastor and email stay in the data.

## Refresh the directory

`scripts/refresh.py` rewrites `churches.json` and `churches.js`:

1. It downloads each Florida page from the [Church of God locator](https://churchofgod.org/church_locator/churches.php?state=FL), about 3 seconds apart.
2. It reads the name, pastor, address, city, state, ZIP, phone, website, and email from the HTML tables.
3. It geocodes street addresses with the [US Census Bureau batch geocoder](https://geocoding.geo.census.gov/geocoder/). A ZIP that does not match uses that ZIP's center point and is stored with `"approx": true`.
4. An address that is already on file keeps its saved coordinates.
5. It keeps churches in Hillsborough, Pinellas, Pasco, Manatee, and Sarasota counties, plus any church whose point falls in the Tampa Bay box (latitude 26.9–28.5, longitude −82.95 to −81.9).

```bash
python3 scripts/refresh.py
```

The download pauses between pages, so a full run takes a few minutes. Review the diff before merging. Pages publishes the root files on `main`, and the live map is https://78tacos.github.io/tampa-churches/.

## Monthly update

`.github/workflows/refresh.yml` runs at 13:00 UTC on the 1st of each month. It can also be started by hand with **workflow_dispatch**. The workflow runs the script and opens a pull request only when the data changed.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
