import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refresh

PUBLISHED = ("FL", "GA", "AL", "SC", "NC", "TN", "MS", "LA", "AR", "OK", "TX", "VA", "WV", "KY")
STATE_FIPS = {
    "FL": "12",
    "GA": "13",
    "AL": "01",
    "SC": "45",
    "NC": "37",
    "TN": "47",
    "MS": "28",
    "LA": "22",
    "AR": "05",
    "OK": "40",
    "TX": "48",
    "VA": "51",
    "WV": "54",
    "KY": "21",
}
STATE_LABEL = {
    "FL": "Florida",
    "GA": "Georgia",
    "AL": "Alabama",
    "SC": "South Carolina",
    "NC": "North Carolina",
    "TN": "Tennessee",
    "MS": "Mississippi",
    "LA": "Louisiana",
    "AR": "Arkansas",
    "OK": "Oklahoma",
    "TX": "Texas",
    "VA": "Virginia",
    "WV": "West Virginia",
    "KY": "Kentucky",
}
# south, north, west, east — padded past the state line so ZIP-center pins still fit.
BOXES = {
    "FL": (24.3, 31.2, -87.9, -79.7),
    "GA": (30.2, 35.2, -85.9, -80.5),
    "AL": (30.0, 35.2, -88.7, -84.7),
    "SC": (31.9, 35.4, -83.6, -78.4),
    "NC": (33.6, 36.8, -84.5, -75.3),
    "TN": (34.8, 36.8, -90.5, -81.5),
    "MS": (30.0, 35.2, -91.9, -87.9),
    "LA": (28.5, 33.4, -94.5, -88.4),
    "AR": (32.6, 36.9, -95.0, -89.2),
    "OK": (33.2, 37.4, -103.4, -94.0),
    "TX": (25.4, 37.0, -107.2, -93.0),
    "VA": (36.2, 39.8, -84.1, -74.9),
    "WV": (36.9, 40.9, -83.0, -77.4),
    "KY": (36.2, 39.4, -89.9, -81.6),
}


def _load():
    return json.loads((ROOT / "churches.json").read_text(encoding="utf-8"))


class SoutheastPageTests(unittest.TestCase):
    def test_map_covers_florida_and_the_southeast(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            "<title>Church of God Map — Florida, the Southeast, South-Central, and the Upper South</title>",
            index,
        )
        self.assertIn(">Church of God Map</h3>", index)
        self.assertIn(
            "Florida, Georgia, Alabama, South Carolina, North Carolina, Tennessee, Mississippi, Louisiana, Arkansas, Oklahoma, Texas, Virginia, West Virginia, and Kentucky",
            index,
        )
        self.assertIn('id="st"', index)
        self.assertIn("All states", index)
        self.assertIn("BOUNDS.ALL", index)
        self.assertIn("-106.65", index)
        self.assertIn("ALL:[[24.4,-106.65],[40.8,-75.1]]", index)
        self.assertIn("VA:[[36.4,-83.9],[39.6,-75.1]]", index)
        self.assertIn("WV:[[37.0,-82.8],[40.8,-77.5]]", index)
        self.assertIn("KY:[[36.4,-89.8],[39.3,-81.8]]", index)
        self.assertNotIn("const FL=", index)
        self.assertNotIn("viewbox=-87.7,31.1,-79.8,24.4", index)
        self.assertNotIn("Florida and Georgia</title>", index)
        self.assertNotIn("Florida and the Southeast</title>", index)
        self.assertIn("function inState", index)
        self.assertIn('src="churches.js"', index)
        for code, label in STATE_LABEL.items():
            self.assertIn(f"{code}:'{label}'", index)
            self.assertIn(f"{code}:[[", index)

    def test_directory_state_filter_keeps_counties_and_cities_apart(self):
        directory = (ROOT / "directory.html").read_text(encoding="utf-8")
        self.assertIn(
            "<title>Church of God Directory — Florida, the Southeast, South-Central, and the Upper South</title>",
            directory,
        )
        self.assertIn("Church of God Directory — Florida, the Southeast, South-Central, and the Upper South", directory)
        self.assertIn("first.state==='LA'?'Parish':'County'", directory)
        self.assertIn("/ city$/.test(first.county||'')", directory)
        self.assertNotIn("/ city$/i", directory)
        self.assertIn("All parishes", directory)
        self.assertIn("All counties", directory)
        self.assertIn("All regions", directory)
        self.assertIn('id="st"', directory)
        self.assertIn('aria-label="State"', directory)
        self.assertIn('aria-label="Region"', directory)
        self.assertIn('aria-label="City"', directory)
        self.assertIn("countyValue", directory)
        self.assertIn("c.state+'|'+c.county", directory)
        self.assertIn("citiesNeedState", directory)
        self.assertIn("c.state+'|'+grp(c)", directory)
        self.assertIn('href="index.html"', directory)
        self.assertIn('src="churches.js"', directory)
        self.assertNotIn("Florida and Georgia", directory)
        self.assertNotIn("Florida and the Southeast</title>", directory)
        for code, label in STATE_LABEL.items():
            self.assertIn(f"{code}:'{label}'", directory)

    def test_monthly_job_refreshes_every_published_state(self):
        workflow = (ROOT / ".github/workflows/refresh.yml").read_text(encoding="utf-8")
        self.assertIn("python scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX VA WV KY", workflow)
        self.assertIn("timeout-minutes: 90", workflow)
        self.assertNotIn("python scripts/refresh.py FL\n", workflow)
        self.assertNotIn("python scripts/refresh.py FL GA\n", workflow)
        self.assertNotIn("python scripts/refresh.py FL GA AL SC NC TN MS\n", workflow)
        self.assertNotIn("python scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX\n", workflow)
        self.assertIn(
            "Refresh Florida, Georgia, Alabama, South Carolina, North Carolina, Tennessee, Mississippi, Louisiana, Arkansas, Oklahoma, Texas, Virginia, West Virginia, and Kentucky church directory",
            workflow,
        )


class SoutheastDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.churches = _load()
        cls.counts = Counter(church["state"] for church in cls.churches)

    def test_published_directory_keeps_florida_georgia_and_the_new_states(self):
        self.assertEqual(set(self.counts), set(PUBLISHED))
        self.assertGreaterEqual(self.counts["FL"], 100)
        self.assertGreaterEqual(self.counts["GA"], 100)
        for code in ("AL", "SC", "NC", "TN", "MS"):
            self.assertGreaterEqual(self.counts[code], 50, code)
        # Locator binding for this batch is LA 56, AR 77, OK 57, TX 258.
        # Floors sit a little under that so a few-record drift still passes.
        self.assertGreaterEqual(self.counts["LA"], 50)
        self.assertGreaterEqual(self.counts["AR"], 70)
        self.assertGreaterEqual(self.counts["OK"], 50)
        self.assertGreaterEqual(self.counts["TX"], 240)
        # Locator binding for this batch is VA 191, WV 154, KY 213.
        # Floors sit a little under that so a few-record drift still passes.
        self.assertGreaterEqual(self.counts["VA"], 180)
        self.assertGreaterEqual(self.counts["WV"], 140)
        self.assertGreaterEqual(self.counts["KY"], 200)
        self.assertGreaterEqual(len(self.churches), 3600)
        refresh.require_complete_download(list(PUBLISHED), self.churches)

    def test_records_keep_the_schema_and_own_state_counties(self):
        allowed = {
            code: set(refresh.COUNTY_FIPS_BY_STATE[STATE_FIPS[code]].values()) for code in PUBLISHED
        }
        for church in self.churches:
            self.assertEqual(list(church), list(refresh.SCHEMA_KEYS))
            self.assertIn(church["state"], allowed)
            self.assertIsInstance(church["approx"], bool)
            if church["county"]:
                self.assertIn(church["county"], allowed[church["state"]])
            if not refresh.has_pin(church):
                self.assertIsNone(church["lat"])
                self.assertIsNone(church["lng"])
                continue
            south, north, west, east = BOXES[church["state"]]
            self.assertGreaterEqual(church["lat"], south, church["name"])
            self.assertLessEqual(church["lat"], north, church["name"])
            self.assertGreaterEqual(church["lng"], west, church["name"])
            self.assertLessEqual(church["lng"], east, church["name"])

    def test_po_box_only_pins_stay_approximate(self):
        checked = 0
        for church in self.churches:
            if refresh.street_candidates(church) or not refresh.has_pin(church):
                continue
            checked += 1
            self.assertTrue(church["approx"], church["name"])
        self.assertGreater(checked, 0)

    def test_shared_county_names_stay_on_their_own_state(self):
        names = {
            code: set(refresh.COUNTY_FIPS_BY_STATE[STATE_FIPS[code]].values()) for code in PUBLISHED
        }
        shared = set.intersection(*(names[code] for code in ("FL", "GA", "TN", "NC")))
        self.assertIn("Polk", shared)
        seen = Counter()
        for church in self.churches:
            if church["county"] != "Polk":
                continue
            seen[church["state"]] += 1
            self.assertIn("Polk", names[church["state"]])
        self.assertGreater(seen["FL"], 0)
        self.assertGreater(seen["GA"], 0)

    def test_jefferson_and_shared_cities_stay_on_their_own_state(self):
        names = {
            code: set(refresh.COUNTY_FIPS_BY_STATE[STATE_FIPS[code]].values()) for code in PUBLISHED
        }
        seen = Counter()
        for church in self.churches:
            if church["county"] != "Jefferson":
                continue
            seen[church["state"]] += 1
            self.assertIn("Jefferson", names[church["state"]])
        self.assertGreater(seen["KY"], 0)
        self.assertGreater(len(seen), 1)
        cities: dict[str, set[str]] = {}
        for church in self.churches:
            cities.setdefault(church["city_group"], set()).add(church["state"])
        self.assertGreaterEqual(len(cities["Cleveland"]), 2)
        self.assertTrue(cities["Cleveland"] & {"AL", "GA", "MS", "SC", "TN"})

    def test_numberless_pins_stay_approximate(self):
        checked = 0
        for church in self.churches:
            if refresh.has_house_number(church) or not refresh.has_pin(church):
                continue
            checked += 1
            self.assertTrue(church["approx"], church["name"] + " " + church["address1"])
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
