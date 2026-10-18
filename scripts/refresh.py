#!/usr/bin/env python3
"""Rebuild the Tampa Bay Church of God directory from churchofgod.org.

The locator is paged. Pages are fetched about three seconds apart. Street
addresses are geocoded with the US Census batch geocoder. A ZIP that does
not match falls back to that ZIP's center point and is marked approximate.
An address that is already in churches.json keeps its saved coordinates.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCATOR_URL = "https://churchofgod.org/church_locator/churches.php"
CENSUS_BATCH_URL = "https://geocoding.geo.census.gov/geocoder/geographies/addressbatch"
GEONAMES_URL = "https://download.geonames.org/export/zip/US.zip"
USER_AGENT = "tampa-churches-refresh/1.0 (+https://78tacos.github.io/tampa-churches/)"
REQUEST_INTERVAL_SECONDS = 3
MIN_STATEWIDE = 100

CONTACT_KEYS = (
    "name",
    "pastor",
    "address1",
    "address2",
    "city",
    "state",
    "zip",
    "phone",
    "website",
    "email",
)
SCHEMA_KEYS = CONTACT_KEYS + ("lat", "lng", "approx", "county", "city_group")

TARGET_COUNTIES = frozenset(
    {"Hillsborough", "Pinellas", "Pasco", "Manatee", "Sarasota"}
)
LAT_MIN = 26.9
LAT_MAX = 28.5
LNG_MIN = -82.95
LNG_MAX = -81.9

# Census county FIPS for Florida (state 12), without the state prefix.
FL_COUNTY_FIPS = {
    "001": "Alachua",
    "003": "Baker",
    "005": "Bay",
    "007": "Bradford",
    "009": "Brevard",
    "011": "Broward",
    "013": "Calhoun",
    "015": "Charlotte",
    "017": "Citrus",
    "019": "Clay",
    "021": "Collier",
    "023": "Columbia",
    "027": "DeSoto",
    "029": "Dixie",
    "031": "Duval",
    "033": "Escambia",
    "035": "Flagler",
    "037": "Franklin",
    "039": "Gadsden",
    "041": "Gilchrist",
    "043": "Glades",
    "045": "Gulf",
    "047": "Hamilton",
    "049": "Hardee",
    "051": "Hendry",
    "053": "Hernando",
    "055": "Highlands",
    "057": "Hillsborough",
    "059": "Holmes",
    "061": "Indian River",
    "063": "Jackson",
    "065": "Jefferson",
    "067": "Lafayette",
    "069": "Lake",
    "071": "Lee",
    "073": "Leon",
    "075": "Levy",
    "077": "Liberty",
    "079": "Madison",
    "081": "Manatee",
    "083": "Marion",
    "085": "Martin",
    "086": "Miami-Dade",
    "087": "Monroe",
    "089": "Nassau",
    "091": "Okaloosa",
    "093": "Okeechobee",
    "095": "Orange",
    "097": "Osceola",
    "099": "Palm Beach",
    "101": "Pasco",
    "103": "Pinellas",
    "105": "Polk",
    "107": "Putnam",
    "109": "St. Johns",
    "111": "St. Lucie",
    "113": "Santa Rosa",
    "115": "Sarasota",
    "117": "Seminole",
    "119": "Sumter",
    "121": "Suwannee",
    "123": "Taylor",
    "125": "Union",
    "127": "Volusia",
    "129": "Wakulla",
    "131": "Walton",
    "133": "Washington",
}

_CITY_GROUPS = {
    "st petersburg": "Saint Petersburg",
    "st. petersburg": "Saint Petersburg",
    "brandenton": "Bradenton",
}

_COMMENT_RE = re.compile(r"(?is)<!--.*?-->")
_BREAK_RE = re.compile(r"(?is)<br\s*/?>")
_PARAGRAPH_RE = re.compile(r"(?is)<p\b[^>]*>(.*?)</p>")
_BOLD_RE = re.compile(r"(?is)<b\b[^>]*>(.*?)</b>")
_TAG_RE = re.compile(r"(?is)<[^>]+>")
_CITY_RE = re.compile(r"^(.*?),\s*([A-Za-z]{2}),\s*(\d{5})(?:-?\d{4})?$")
_RESULTS_RE = re.compile(
    r"Results\s+([\d,]+)\s+to\s+([\d,]+)\s+of\s+([\d,]+)",
    re.IGNORECASE,
)


def clean_text(raw: str) -> str:
    text = unescape(raw).replace("\xa0", " ")
    return " ".join(text.split())


def _blank_none(value: str) -> str:
    cleaned = " ".join(value.split())
    if cleaned.lower() == "none":
        return ""
    return cleaned


def _norm(value: str) -> str:
    return " ".join((value or "").split()).casefold()


def city_group_for(city: str) -> str:
    cleaned = " ".join(city.split())
    mapped = _CITY_GROUPS.get(cleaned.casefold())
    if mapped:
        return mapped
    return cleaned


def address_key(church: dict) -> tuple[str, str, str, str, str]:
    return (
        _norm(church.get("address1", "")),
        _norm(church.get("address2", "")),
        _norm(church.get("city", "")),
        _norm(church.get("state", "")),
        _norm(church.get("zip", ""))[:5],
    )


def order_key(church: dict) -> tuple[str, str, str, str, str]:
    return (
        _norm(church.get("name", "")),
        _norm(church.get("address1", "")),
        _norm(church.get("address2", "")),
        _norm(church.get("city", "")),
        _norm(church.get("zip", ""))[:5],
    )


def paragraphs(html: str) -> list[tuple[str, str | None]]:
    without_comments = _COMMENT_RE.sub(" ", html)
    with_breaks = _BREAK_RE.sub(" ", without_comments)
    found: list[tuple[str, str | None]] = []
    for body in _PARAGRAPH_RE.findall(with_breaks):
        bolds = [clean_text(_TAG_RE.sub(" ", bold)) for bold in _BOLD_RE.findall(body)]
        text = clean_text(_TAG_RE.sub(" ", body))
        if not text:
            continue
        bold = bolds[0] if len(bolds) == 1 else None
        found.append((text, bold))
    return found


def _is_church_name(text: str, bold: str | None) -> bool:
    return bool(bold) and text == bold


def _parse_block(
    name: str, rows: list[tuple[str, str | None]], index: int
) -> tuple[dict | None, int]:
    pastor = ""
    phone = ""
    website = ""
    email = ""
    address_lines: list[str] = []
    city = ""
    state = ""
    zip_code = ""
    saw_city = False
    while index < len(rows):
        text, bold = rows[index]
        if _is_church_name(text, bold):
            break
        lower = text.lower()
        if lower.startswith("pastor:"):
            pastor = _blank_none(text.split(":", 1)[1])
        elif lower.startswith("phone:"):
            phone = _blank_none(text.split(":", 1)[1])
        elif lower.startswith("church web site:"):
            website = _blank_none(text.split(":", 1)[1])
        elif lower.startswith("church email"):
            email = _blank_none(text.split(":", 1)[1])
        else:
            city_match = _CITY_RE.match(text)
            if city_match and not saw_city:
                city = clean_text(city_match.group(1))
                state = city_match.group(2).upper()
                zip_code = city_match.group(3)
                saw_city = True
            elif not saw_city:
                address_lines.append(text)
        index += 1
    if not zip_code:
        return None, index
    return (
        {
            "name": name,
            "pastor": pastor,
            "address1": address_lines[0] if address_lines else "",
            "address2": ", ".join(address_lines[1:]) if len(address_lines) > 1 else "",
            "city": city,
            "state": state,
            "zip": zip_code,
            "phone": phone,
            "website": website,
            "email": email,
        },
        index,
    )


def parse_churches(html: str) -> list[dict]:
    """Parse one locator page into contact records, without coordinates."""
    rows = paragraphs(html)
    churches: list[dict] = []
    index = 0
    while index < len(rows):
        text, bold = rows[index]
        if not _is_church_name(text, bold):
            index += 1
            continue
        church, index = _parse_block(text, rows, index + 1)
        if church:
            churches.append(church)
    return churches


def page_counts(html: str) -> tuple[int, int, int] | None:
    match = _RESULTS_RE.search(html)
    if not match:
        return None
    start, end, total = (int(part.replace(",", "")) for part in match.groups())
    return start, end, total


def in_bbox(lat: float, lng: float) -> bool:
    return LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX


def keep_church(church: dict) -> bool:
    if church.get("county") in TARGET_COUNTIES:
        return True
    return in_bbox(church["lat"], church["lng"])


def make_record(church: dict, lat: float, lng: float, approx: bool, county: str) -> dict:
    values = {key: church[key] for key in CONTACT_KEYS}
    values.update(
        {
            "lat": lat,
            "lng": lng,
            "approx": approx,
            "county": county,
            "city_group": city_group_for(church["city"]),
        }
    )
    return {key: values[key] for key in SCHEMA_KEYS}


def resolve_locations(
    churches: list[dict],
    existing: list[dict],
    census_by_key: dict[tuple[str, str, str, str, str], tuple[float, float, str]],
    centroids: dict[str, tuple[float, float]],
) -> list[dict]:
    cache: dict[tuple[str, str, str, str, str], dict] = {}
    for old in existing:
        if isinstance(old.get("lat"), (int, float)) and isinstance(old.get("lng"), (int, float)):
            cache.setdefault(address_key(old), old)
    resolved: list[dict] = []
    for church in churches:
        key = address_key(church)
        old = cache.get(key)
        if old is not None:
            resolved.append(
                make_record(
                    church,
                    old["lat"],
                    old["lng"],
                    bool(old.get("approx")),
                    old.get("county") or "",
                )
            )
            continue
        hit = census_by_key.get(key)
        if hit is not None:
            lat, lng, county = hit
            resolved.append(make_record(church, lat, lng, False, county))
            continue
        center = centroids.get(church["zip"])
        if center is None:
            continue
        lat, lng = center
        resolved.append(make_record(church, lat, lng, True, ""))
    return resolved


def order_churches(churches: list[dict], existing: list[dict]) -> list[dict]:
    """Keep churches that are already listed in their current order.

    Churches the locator added are appended, sorted by name and address.
    """
    buckets: dict[tuple[str, str, str, str, str], list[dict]] = defaultdict(list)
    for church in churches:
        buckets[order_key(church)].append(church)
    ordered: list[dict] = []
    used: dict[tuple[str, str, str, str, str], int] = defaultdict(int)
    for old in existing:
        key = order_key(old)
        index = used[key]
        group = buckets.get(key, [])
        if index < len(group):
            ordered.append(group[index])
            used[key] = index + 1
    extras: list[dict] = []
    for key, group in buckets.items():
        extras.extend(group[used[key] :])
    extras.sort(key=order_key)
    return ordered + extras


def render_json(churches: list[dict]) -> str:
    return json.dumps(churches, indent=1)


def render_js(churches: list[dict]) -> str:
    return "const CHURCHES=" + json.dumps(churches) + ";"


def parse_census_batch(text: str) -> dict[str, tuple[float, float, str]]:
    """Map a Census batch id to (lat, lng, county) for Florida matches.

    Columns, when a row matches, are: id, input address, status, match type,
    matched address, lon,lat, tiger line id, side, state FIPS, county FIPS.
    """
    if "Match" not in text and "No_Match" not in text:
        raise RuntimeError("Census geocoder returned an unexpected response")
    hits: dict[str, tuple[float, float, str]] = {}
    reader = csv.reader(io.StringIO(text.lstrip("\ufeff")))
    for row in reader:
        if len(row) < 10 or row[2].strip() != "Match":
            continue
        if row[8].strip().zfill(2) != "12":
            continue
        lon_text, lat_text = row[5].split(",")
        county = FL_COUNTY_FIPS.get(row[9].strip().zfill(3), "")
        hits[row[0].strip()] = (float(lat_text), float(lon_text), county)
    return hits


def census_csv(churches: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for index, church in enumerate(churches, start=1):
        street = church["address1"]
        if church["address2"]:
            street = f"{street} {church['address2']}"
        writer.writerow([index, street, church["city"], church["state"], church["zip"]])
    return buffer.getvalue().encode("utf-8")


def parse_gazetteer(text: str) -> dict[str, tuple[float, float]]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return {}
    delimiter = "|" if "|" in lines[0] else "\t"
    columns = [column.strip() for column in lines[0].split(delimiter)]
    id_index = columns.index("GEOID")
    lat_index = columns.index("INTPTLAT")
    lng_index = columns.index("INTPTLONG")
    needed = max(id_index, lat_index, lng_index)
    centroids: dict[str, tuple[float, float]] = {}
    for line in lines[1:]:
        parts = [part.strip() for part in line.split(delimiter)]
        if len(parts) <= needed:
            continue
        zip_code = parts[id_index]
        if not (len(zip_code) == 5 and zip_code.isdigit()):
            tail = zip_code[-5:]
            zip_code = tail if len(tail) == 5 and tail.isdigit() else ""
        if not zip_code:
            continue
        centroids[zip_code] = (float(parts[lat_index]), float(parts[lng_index]))
    return centroids


def parse_gazetteer_zip(blob: bytes) -> dict[str, tuple[float, float]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        name = next(item for item in archive.namelist() if item.lower().endswith(".txt"))
        text = archive.read(name).decode("utf-8", "replace")
    return parse_gazetteer(text)


def parse_geonames(text: str) -> dict[str, tuple[float, float]]:
    centroids: dict[str, tuple[float, float]] = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 11:
            continue
        postal = parts[1].strip()
        if len(postal) != 5 or not postal.isdigit() or postal in centroids:
            continue
        try:
            centroids[postal] = (float(parts[9]), float(parts[10]))
        except ValueError:
            continue
    return centroids


def parse_geonames_zip(blob: bytes) -> dict[str, tuple[float, float]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        name = next(
            item
            for item in archive.namelist()
            if item.lower().endswith(".txt") and "readme" not in item.lower()
        )
        text = archive.read(name).decode("utf-8", "replace")
    return parse_geonames(text)


def request_bytes(
    url: str,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> bytes:
    extra = {"User-Agent": USER_AGENT}
    if headers:
        extra.update(headers)
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, data=data, headers=extra)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise
            last_error = error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
        if attempt < 3:
            time.sleep(2**attempt)
    if last_error is None:
        raise RuntimeError(f"Request failed for {url}")
    raise last_error


def decode_html(raw: bytes) -> str:
    head = raw[:1000].decode("ascii", "ignore")
    match = re.search(r"charset=([\w-]+)", head, re.IGNORECASE)
    encoding = match.group(1) if match else "iso-8859-1"
    return raw.decode(encoding, "replace")


def fetch_churches(delay: float) -> list[dict]:
    offset = 0
    churches: list[dict] = []
    seen_offsets: set[int] = set()
    for _ in range(200):
        if offset in seen_offsets:
            break
        seen_offsets.add(offset)
        url = (
            f"{LOCATOR_URL}?state=FL&int_cur_position={offset}"
            "&mode=citystate_search&searchtext="
        )
        print(f"Fetching offset {offset}", flush=True)
        html = decode_html(request_bytes(url, timeout=60))
        churches.extend(parse_churches(html))
        counts = page_counts(html)
        if counts is None:
            raise RuntimeError("Locator page did not include a result count")
        start, end, total = counts
        print(f"  results {start}–{end} of {total}", flush=True)
        if end >= total:
            return churches
        offset = end
        time.sleep(delay)
    raise RuntimeError("Stopped after too many locator pages")


def dedupe(churches: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    unique: list[dict] = []
    for church in churches:
        key = (_norm(church["name"]),) + address_key(church)
        if key in seen:
            continue
        seen.add(key)
        unique.append(church)
    return unique


def _post_census(churches: list[dict]) -> str:
    boundary = "----tampaChurchesBoundary7f3a"
    payload = census_csv(churches)
    body = b"".join(
        [
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="benchmark"\r\n\r\n'
                "Public_AR_Current\r\n"
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="vintage"\r\n\r\n'
                "Current_Current\r\n"
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="addressFile"; filename="addresses.csv"\r\n'
                "Content-Type: text/csv\r\n\r\n"
            ).encode(),
            payload,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    raw = request_bytes(
        CENSUS_BATCH_URL,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        timeout=180,
    )
    return raw.decode("utf-8", "replace")


def geocode_addresses(
    churches: list[dict],
) -> dict[tuple[str, str, str, str, str], tuple[float, float, str]]:
    unique: list[dict] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for church in churches:
        key = address_key(church)
        if key in seen:
            continue
        seen.add(key)
        unique.append(church)
    hits: dict[tuple[str, str, str, str, str], tuple[float, float, str]] = {}
    chunk_size = 5000
    for start in range(0, len(unique), chunk_size):
        chunk = unique[start : start + chunk_size]
        parsed = parse_census_batch(_post_census(chunk))
        for index, church in enumerate(chunk, start=1):
            hit = parsed.get(str(index))
            if hit is not None:
                hits[address_key(church)] = hit
        if start + chunk_size < len(unique):
            time.sleep(REQUEST_INTERVAL_SECONDS)
    return hits


def gazetteer_urls() -> list[str]:
    year = time.gmtime().tm_year
    return [
        "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
        f"{candidate}_Gazetteer/{candidate}_Gaz_zcta_national.zip"
        for candidate in range(year, 2023, -1)
    ]


def load_zcta_centroids() -> dict[str, tuple[float, float]]:
    errors: list[str] = []
    for url in gazetteer_urls():
        try:
            blob = request_bytes(url, timeout=120)
        except urllib.error.HTTPError as error:
            errors.append(f"{url} ({error.code})")
            continue
        except urllib.error.URLError as error:
            errors.append(f"{url} ({error.reason})")
            continue
        centroids = parse_gazetteer_zip(blob)
        if centroids:
            print(f"Loaded {len(centroids)} ZIP centers from the Census gazetteer", flush=True)
            return centroids
    detail = "; ".join(errors) or "no gazetteer responded"
    raise RuntimeError(f"Could not download a Census ZIP gazetteer: {detail}")


def load_postal_centroids(needed: set[str]) -> dict[str, tuple[float, float]]:
    centroids = load_zcta_centroids()
    missing = sorted(zip_code for zip_code in needed if zip_code not in centroids)
    if not missing:
        return centroids
    try:
        extra = parse_geonames_zip(request_bytes(GEONAMES_URL, timeout=120))
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        print(
            f"GeoNames ZIP centers unavailable ({error}). {len(missing)} ZIPs have no center.",
            file=sys.stderr,
        )
        return centroids
    filled = 0
    for zip_code in missing:
        center = extra.get(zip_code)
        if center is None:
            continue
        centroids[zip_code] = center
        filled += 1
    print(f"Filled {filled} of {len(missing)} non-ZCTA ZIPs from GeoNames", flush=True)
    return centroids


def load_existing(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("churches.json is not a list")
    return data


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_outputs(json_path: Path, js_path: Path, churches: list[dict]) -> None:
    atomic_write(json_path, render_json(churches))
    atomic_write(js_path, render_js(churches))


def main() -> None:
    json_path = ROOT / "churches.json"
    js_path = ROOT / "churches.js"
    existing = load_existing(json_path)
    print("Downloading Florida churches from churchofgod.org", flush=True)
    parsed = dedupe(fetch_churches(REQUEST_INTERVAL_SECONDS))
    print(f"Parsed {len(parsed)} Florida churches", flush=True)
    if len(parsed) < MIN_STATEWIDE:
        raise SystemExit(
            f"Parsed only {len(parsed)} churches; leaving the directory files unchanged"
        )

    cached = {
        address_key(church)
        for church in existing
        if isinstance(church.get("lat"), (int, float)) and isinstance(church.get("lng"), (int, float))
    }
    needs_geocode = [church for church in parsed if address_key(church) not in cached]
    print(
        f"Geocoding {len({address_key(church) for church in needs_geocode})} new or changed addresses; "
        f"reusing saved locations for the rest",
        flush=True,
    )
    census_hits = geocode_addresses(needs_geocode) if needs_geocode else {}
    unresolved = {
        church["zip"]
        for church in needs_geocode
        if address_key(church) not in census_hits and church.get("zip")
    }
    centroids = load_postal_centroids(unresolved) if unresolved else {}
    located = resolve_locations(parsed, existing, census_hits, centroids)
    selected = order_churches([church for church in located if keep_church(church)], existing)
    located_keys = {order_key(church) for church in located}
    unlocated = [church for church in parsed if order_key(church) not in located_keys]
    approx = sum(1 for church in selected if church["approx"])
    print(
        f"Keeping {len(selected)} Tampa Bay churches ({approx} approximate); "
        f"{len(located) - len(selected)} outside the area; {len(unlocated)} could not be located",
        flush=True,
    )
    for church in unlocated[:15]:
        print(f"  no location: {church['name']} ({church['city']} {church['zip']})", flush=True)
    if not selected:
        raise SystemExit("Refusing to write an empty directory")
    write_outputs(json_path, js_path, selected)
    print(f"Wrote {json_path.name} and {js_path.name}", flush=True)


if __name__ == "__main__":
    main()
