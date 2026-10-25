import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "scripts"))

import refresh


def _load():
    return json.loads((ROOT / "churches.json").read_text(encoding="utf-8"))


class PilotPageTests(unittest.TestCase):
    def test_map_covers_florida_and_georgia(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Church of God Map — Florida and Georgia</title>", index)
        self.assertIn(">Church of God Map</h3>", index)
        self.assertIn("Florida and Georgia", index)
        self.assertIn('id="st"', index)
        self.assertIn("All states", index)
        self.assertIn("BOUNDS.ALL", index)
        self.assertIn("35.15", index)
        self.assertNotIn("const FL=", index)
        self.assertNotIn("viewbox=-87.7,31.1,-79.8,24.4", index)
        self.assertIn("function inState", index)
        self.assertIn('src="churches.js"', index)

    def test_directory_state_filter_keeps_counties_apart(self):
        directory = (ROOT / "directory.html").read_text(encoding="utf-8")
        self.assertIn("<title>Church of God Directory — Florida and Georgia</title>", directory)
        self.assertIn("Church of God Directory — Florida and Georgia", directory)
        self.assertIn('id="st"', directory)
        self.assertIn('aria-label="State"', directory)
        self.assertIn('aria-label="County"', directory)
        self.assertIn("countyValue", directory)
        self.assertIn("c.state+'|'+c.county", directory)
        self.assertIn("citiesNeedState", directory)
        self.assertIn('href="index.html"', directory)
        self.assertIn('src="churches.js"', directory)

    def test_monthly_job_refreshes_both_pilot_states(self):
        workflow = (ROOT / ".github/workflows/refresh.yml").read_text(encoding="utf-8")
        self.assertIn("python scripts/refresh.py FL GA", workflow)
        self.assertNotIn("python scripts/refresh.py FL\n", workflow)
        self.assertIn("Refresh Florida and Georgia church directory", workflow)


class PilotDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.churches = _load()
        cls.counts = Counter(church["state"] for church in cls.churches)

    def test_published_directory_is_florida_and_georgia(self):
        self.assertEqual(set(self.counts), {"FL", "GA"})
        self.assertGreaterEqual(self.counts["FL"], 100)
        self.assertGreaterEqual(self.counts["GA"], 100)
        self.assertGreaterEqual(len(self.churches), refresh.MIN_STATEWIDE)

    def test_records_keep_the_schema_and_own_state_counties(self):
        fl_counties = set(refresh.COUNTY_FIPS_BY_STATE["12"].values())
        ga_counties = set(refresh.COUNTY_FIPS_BY_STATE["13"].values())
        allowed = {"FL": fl_counties, "GA": ga_counties}
        boxes = {
            "FL": (24.3, 31.2, -87.9, -79.7),
            "GA": (30.2, 35.2, -85.9, -80.5),
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
            south, north, west, east = boxes[church["state"]]
            self.assertGreaterEqual(church["lat"], south)
            self.assertLessEqual(church["lat"], north)
            self.assertGreaterEqual(church["lng"], west)
            self.assertLessEqual(church["lng"], east)

    def test_po_box_only_pins_stay_approximate(self):
        checked = 0
        for church in self.churches:
            if refresh.street_candidates(church) or not refresh.has_pin(church):
                continue
            checked += 1
            self.assertTrue(church["approx"], church["name"])
        self.assertGreater(checked, 0)

    def test_shared_county_names_are_not_stored_on_the_wrong_state(self):
        fl_names = set(refresh.COUNTY_FIPS_BY_STATE["12"].values())
        ga_names = set(refresh.COUNTY_FIPS_BY_STATE["13"].values())
        shared = fl_names & ga_names
        self.assertIn("Polk", shared)
        seen = Counter()
        for church in self.churches:
            if church["county"] in shared:
                seen[church["state"]] += 1
                if church["state"] == "FL":
                    self.assertIn(church["county"], fl_names)
                else:
                    self.assertIn(church["county"], ga_names)
        self.assertGreater(seen["FL"], 0)
        self.assertGreater(seen["GA"], 0)


if __name__ == "__main__":
    unittest.main()
