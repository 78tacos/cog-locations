---
name: cog-batch
description: >-
  Use when adding Church of God states or regions to this repo, rebuilding the
  published directory, updating locator binding counts or state floors, or
  opening a region-batch pull request. Use it when several 3–5 state groups
  should ship together in one pull request.
---

# Church of God region batch

Add states by rebuilding the whole published directory in one refresh, then shipping one pull request. A batch is several regions at once (each region is a group of 3–5 states), not one pull request per region.

Merged batches that this procedure follows:

| PR | Region | States | Locator counts | Directory total after |
| --- | --- | --- | --- | --- |
| #11 | South-Central | LA, AR, OK, TX | 56, 77, 57, 258 | 3148 |
| #12 | Upper South | VA, WV, KY | 191, 154, 213 | 3706 |
| #13 | MW-1 | OH, IN, IL, MI | 173, 105, 120, 94 | 4197 |
| #14 | MW-2 | WI, MN, IA, MO | 18, 20, 15, 58 | 4308 |
| #15 | MA-1 | PA, MD, DE, NJ | 107, 120, 22, 98 | 4655 |

#12 also introduced `has_house_number`. That rule is already on main. A new batch uses it; it does not re-implement it. #13 kept a four-digit locator ZIP as published (`6007` for Rolling Meadows, IL) and dropped one Indiana duplicate. #14 set `MIN_PER_STATE` to 15 because Iowa's locator total is 15. A requested state at or above `MIN_PER_STATE` is written from the fresh scrape. Under that count, `keep_published_rows` publishes a never-published state when the fresh count is at least 1. A published state keeps its previous rows only when the fresh count is 0 or lower than the saved count; a fresh count of at least 1 that is at least the saved count replaces those rows. A fresh count of 0 with nothing saved is logged and contributes nothing. There is no "less than half" guard. `MIN_STATEWIDE` remains the combined gate.

The live binding on main `e89dc8e` is **4655**, and the monthly refresh after that commit kept 4655. Per-state counts at that binding: FL 629, GA 493, AL 333, SC 305, NC 436, TN 345, MS 159, LA 56, AR 77, OK 57, TX 258, VA 191, WV 154, KY 213, OH 173, IN 104, IL 120, MI 94, WI 18, MN 20, IA 15, MO 58, PA 107, MD 120, DE 22, NJ 98. Indiana's locator total was 105; `dedupe` kept one of two identical rows, so the directory is 104.

## Steps

### 1. List the regions

Write down each region before refreshing: a short name (the style of MW-1 or MA-1) and its USPS codes. Three to five states per region. Put every region in this same pull request. Do not open a second pull request to "finish" another group from the same batch.

Read the states already published from `PUBLISHED` in `tests/test_southeast.py` and from the `python scripts/refresh.py ...` line in `.github/workflows/refresh.yml`. Those two lists match. The new command is that list plus every new code from every region in this batch.

### 2. Refresh once, with every published state

`write_outputs` replaces `churches.json` and `churches.js` with only the states passed on the command line. A shorter list drops published states. Pass the full list:

```bash
python3 scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX VA WV KY OH IN IL MI WI MN IA MO PA MD DE NJ
```

Add the new codes at the end. There is no separate per-region refresh command and no binding script. The script pages `https://churchofgod.org/church_locator/churches.php` about 3 seconds apart (`REQUEST_INTERVAL_SECONDS`), geocodes through Census, then Nominatim, then ArcGIS, and writes both data files. A full run takes a while. The monthly job's `timeout-minutes` is 90; leave it there unless a run actually exceeds it.

While it runs, `fetch_churches` prints `results {start}–{end} of {total}` for each page. The state's locator binding is that `total` on the page where `end >= total`.

### 3. Compute the combined binding, then check each region

After the run, count the directory. This is a one-off; the repo has no count command:

```bash
python3 -c 'import json; from collections import Counter; rows=json.load(open("churches.json")); c=Counter(r["state"] for r in rows); print(len(rows)); [print(f"{code} {c[code]}") for code in sorted(c)]'
```

For each new state, the directory count should equal the locator `total` from the log. `dedupe` collapses the same name and address, so a state can be one under the locator (Indiana, 105 on the locator, 104 in the directory). Explain that delta in the pull request. Do not "fix" it by inserting the duplicate back.

Combined expected binding = previous directory total + the new states' directory counts. The previous total is the length of `churches.json` on the base commit (4655 at `e89dc8e`). Compare each already-published state to that commit and expect ±0:

```bash
git show e89dc8e:churches.json
```

Use the base tip you actually branched from if main has moved, and say which commit you compared.

Check each region on its own, even though the refresh was one command: sum that region's states, and say the sum in the pull request next to the region's name. Then state the one combined binding for the whole directory. A batch of two regions has two region sums and one combined total, not two pull requests.

`churches.json` and `churches.js` stay in sync because `write_outputs` writes both. `test_writers_match_the_pages_files` fails if one file was edited by hand.

### 4. Update the pages, the workflow, and the tests

Mirror the #11–#15 diffs. Touch only the states this batch adds.

- `.github/workflows/refresh.yml`: the `python scripts/refresh.py` line (no `python3` in the workflow) and the commit message that names every state. The comment above the command stays: a shorter list would drop published states.
- `README.md`: title, the coverage sentence, the fenced `python3 scripts/refresh.py ...` block, and the same command in the prose (including the `python scripts/refresh.py ...` monthly-job sentence). Leave the opening sentence that starts "A project I made...". Update `JOSEPH_README` in `tests/test_refresh.py` when the title changes, and update the coverage sentence and fenced command that test asserts.
- `index.html`: `<title>`, the `.sub` state list, `STATE_NAME`, and a `BOUNDS` entry per new state. `BOUNDS` values are `[[south, west], [north, east]]`. Widen `BOUNDS.ALL` when a new state extends past it (MA-1 moved the east edge from `-75.1` to `-73.9` for New Jersey). The state `<select>` is filled from the data.
- `directory.html`: `<title>`, the `<h1>`, and `STATE_NAME`. Leave the Region / All regions / All parishes labels. Louisiana headings stay parishes through `first.state==='LA'?'Parish':'County'`. Do not strip a trailing " city" from Virginia independent cities; `parse_national_county` only strips `County` and `Parish`.
- `tests/test_southeast.py`:
  - Append codes to `PUBLISHED` in the same order as the refresh command.
  - Add `STATE_FIPS`, `STATE_LABEL`, and `BOXES`. FIPS come from `scripts/national_county.txt` (postal, state FIPS, county FIPS, name), which `refresh.US_STATE_FIPS` already loads. `BOXES` is `(south, north, west, east)`, padded past the state line so ZIP-center pins still pass. It is a looser box than the map's `BOUNDS`.
  - Extend the map, directory, and workflow assertions, including `assertNotIn` for the previous shorter `python scripts/refresh.py ...` line so a dropped state fails CI.
  - Add a per-state floor a little under that state's locator count, with a comment that records the locator binding (the comments already in this test are the pattern). Tiny states sit on the complete count: Iowa's floor is 15 because the locator total is 15. These floors check the committed file. They are not `MIN_PER_STATE`.
  - Leave the directory length check as `assertGreaterEqual(len(self.churches), 4600)` until the binding moves enough to raise that floor. Do not lock the test to an exact total.

`tests/fixtures/sample_page.html` is the shared Florida locator page. Batches #11–#15 did not add fixture files. When a new state's HTML breaks the parser, add a small inline HTML case in `tests/test_refresh.py`, as #13 did for a four-digit ZIP. Store the ZIP the locator published.

Census matches stay in the church's own state (`state_fips_for`). County names come from that state's FIPS in `scripts/national_county.txt`. No new county file.

### 5. Floors

`keep_published_rows` runs before `require_complete_download`. Both run before any write.

- `MIN_PER_STATE` is 15. A requested state at or above that count is written from the fresh scrape. Under that count, a state that has never been published (no rows in the current `churches.json`) goes live with the fresh rows when the fresh count is at least 1. A fresh count of 0 is logged with `Keeping published {STATE} rows: fresh 0, kept 0` and contributes nothing. A state that is already published keeps its previous rows only when the fresh count is 0 or lower than the saved count. The log line is `Keeping published {STATE} rows: fresh {n}, kept {m}`. When the fresh count is at least 1 and at least the saved count, the fresh rows replace the saved ones, even if both counts are under 15. Do not add a "less than half" guard. This is what stops the monthly job from deleting a published state when a scrape comes back empty or shorter: `write_outputs` still replaces the file, but that short state is filled from the previous rows first. A published state can still grow when a later scrape is at least as large as the rows already on disk.
- `fetch_churches` tags a row whose state is blank with the state code of that locator request, before dedupe, and logs how many rows were backfilled. A city line like `Des Moines IA 50309` (no commas) otherwise misses `_CITY_RE` and would be published again beside the kept rows.
- `MIN_STATEWIDE` is 100, checked on the list after that substitution. The floor does not grow with the number of states. An empty scrape of states that have nothing saved raises `SystemExit`, prints `Parsed only N churches`, and leaves the files unchanged. A full refresh that restores every published state still clears 100.
- The command and the workflow test must still list every published state. A state that is not requested is not restored.

### 6. Run the tests

```bash
python3 -m unittest discover -s tests -v
```

That is the CI command (`.github/workflows/ci.yml` runs it as `python -m unittest discover -s tests -v` on Python 3.12). Fix failures before opening the pull request. Do not add states that are not in this batch.

### 7. Pull request checklist

One pull request for the whole multi-region batch.

- CI is green on that `unittest` job.
- The body states the combined expected binding and the previous total it was added to (4655 at `e89dc8e` until main moves).
- The body lists every state's directory count. For new states, also list the locator binding and the delta. Group those counts under each region name so a reader can check the regions separately.
- The body shows the full `python3 scripts/refresh.py ...` command and the matching `python scripts/refresh.py ...` workflow line.
- Note any deduped row, approximate pins, or parser exception the way #12 and #13 did. Say that already-published states stayed at the base tip's counts.
- Live map: https://78tacos.github.io/cog-locations/
