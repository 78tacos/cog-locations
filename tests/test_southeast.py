import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refresh

PUBLISHED = ("FL", "GA", "AL", "SC", "NC", "TN", "MS", "LA", "AR", "OK", "TX", "VA", "WV", "KY", "OH", "IN", "IL", "MI", "WI", "MN", "IA", "MO", "PA", "MD", "DE", "NJ", "NY", "CT", "RI", "MA", "VT", "NH", "ME", "ND", "SD", "NE", "KS", "MT", "WY", "CO", "ID", "UT", "AZ", "NM", "NV", "CA", "OR", "WA", "AK", "HI")
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
    "OH": "39",
    "IN": "18",
    "IL": "17",
    "MI": "26",
    "WI": "55",
    "MN": "27",
    "IA": "19",
    "MO": "29",
    "PA": "42",
    "MD": "24",
    "DE": "10",
    "NJ": "34",
    "NY": "36",
    "CT": "09",
    "RI": "44",
    "MA": "25",
    "VT": "50",
    "NH": "33",
    "ME": "23",
    "ND": "38",
    "SD": "46",
    "NE": "31",
    "KS": "20",
    "MT": "30",
    "WY": "56",
    "CO": "08",
    "ID": "16",
    "UT": "49",
    "AZ": "04",
    "NM": "35",
    "NV": "32",
    "CA": "06",
    "OR": "41",
    "WA": "53",
    "AK": "02",
    "HI": "15",
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
    "OH": "Ohio",
    "IN": "Indiana",
    "IL": "Illinois",
    "MI": "Michigan",
    "WI": "Wisconsin",
    "MN": "Minnesota",
    "IA": "Iowa",
    "MO": "Missouri",
    "PA": "Pennsylvania",
    "MD": "Maryland",
    "DE": "Delaware",
    "NJ": "New Jersey",
    "NY": "New York",
    "CT": "Connecticut",
    "RI": "Rhode Island",
    "MA": "Massachusetts",
    "VT": "Vermont",
    "NH": "New Hampshire",
    "ME": "Maine",
    "ND": "North Dakota",
    "SD": "South Dakota",
    "NE": "Nebraska",
    "KS": "Kansas",
    "MT": "Montana",
    "WY": "Wyoming",
    "CO": "Colorado",
    "ID": "Idaho",
    "UT": "Utah",
    "AZ": "Arizona",
    "NM": "New Mexico",
    "NV": "Nevada",
    "CA": "California",
    "OR": "Oregon",
    "WA": "Washington",
    "AK": "Alaska",
    "HI": "Hawaii",
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
    "OH": (38.2, 42.2, -85.1, -80.3),
    "IN": (37.5, 42.0, -88.4, -84.6),
    "IL": (36.8, 42.7, -91.8, -86.8),
    "MI": (41.5, 48.5, -90.7, -82.2),
    "WI": (42.4, 47.2, -93.0, -86.7),
    "MN": (43.4, 49.5, -97.3, -89.4),
    "IA": (40.3, 43.6, -96.7, -90.0),
    "MO": (35.9, 40.7, -95.9, -89.0),
    "PA": (39.6, 42.4, -80.7, -74.5),
    "MD": (37.8, 39.9, -79.6, -74.9),
    "DE": (38.3, 40.0, -75.9, -74.8),
    "NJ": (38.8, 41.5, -75.7, -73.7),
    "NY": (40.3, 45.2, -79.9, -71.7),
    "CT": (40.8, 42.2, -73.9, -71.6),
    "RI": (41.0, 42.2, -72.0, -71.0),
    "MA": (41.1, 43.0, -73.6, -69.8),
    "VT": (42.6, 45.2, -73.6, -71.3),
    "NH": (42.6, 45.4, -72.7, -70.5),
    "ME": (42.8, 47.6, -71.2, -66.8),
    "ND": (45.8, 49.1, -104.2, -96.4),
    "SD": (42.3, 46.1, -104.2, -96.3),
    "NE": (39.8, 43.2, -104.2, -95.1),
    "KS": (36.8, 40.2, -102.2, -94.4),
    "MT": (44.2, 49.1, -116.2, -103.9),
    "WY": (40.8, 45.2, -111.2, -103.9),
    "CO": (36.8, 41.2, -109.2, -101.9),
    "ID": (41.8, 49.1, -117.4, -110.9),
    "UT": (36.8, 42.2, -114.2, -108.9),
    "AZ": (31.2, 37.2, -115.0, -108.9),
    "NM": (31.2, 37.2, -109.2, -102.9),
    "NV": (34.8, 42.2, -120.2, -113.9),
    "CA": (32.3, 42.2, -124.6, -114.0),
    "OR": (41.8, 46.4, -124.7, -116.3),
    "WA": (45.4, 49.1, -124.9, -116.8),
    "AK": (51.0, 71.6, -180.0, -129.7),
    "HI": (18.7, 22.4, -160.4, -154.6),
}


def _load():
    return json.loads((ROOT / "churches.json").read_text(encoding="utf-8"))


class SoutheastPageTests(unittest.TestCase):
    def test_map_covers_florida_and_the_southeast(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            "<title>Church of God Map — Florida, the Southeast, South-Central, the Upper South, the Midwest, the Mid-Atlantic, the Northeast, northern New England, the Plains, the Mountain West, the Southwest, and the Pacific</title>",
            index,
        )
        self.assertIn(">Church of God Map</h3>", index)
        self.assertIn(
            "Florida, Georgia, Alabama, South Carolina, North Carolina, Tennessee, Mississippi, Louisiana, Arkansas, Oklahoma, Texas, Virginia, West Virginia, Kentucky, Ohio, Indiana, Illinois, Michigan, Wisconsin, Minnesota, Iowa, Missouri, Pennsylvania, Maryland, Delaware, New Jersey, New York, Connecticut, Rhode Island, Massachusetts, Vermont, New Hampshire, Maine, North Dakota, South Dakota, Nebraska, Kansas, Montana, Wyoming, Colorado, Idaho, Utah, Arizona, New Mexico, Nevada, California, Oregon, Washington, Alaska, and Hawaii",
            index,
        )
        self.assertIn('id="st"', index)
        self.assertIn("All states", index)
        self.assertIn("BOUNDS.ALL", index)
        self.assertIn("-106.65", index)
        self.assertIn("ALL:[[18.91,-179.15],[71.39,-66.95]]", index)
        self.assertNotIn("ALL:[[24.4,-106.65],[49.4,-73.9]]", index)
        self.assertIn("VA:[[36.4,-83.9],[39.6,-75.1]]", index)
        self.assertIn("WV:[[37.0,-82.8],[40.8,-77.5]]", index)
        self.assertIn("KY:[[36.4,-89.8],[39.3,-81.8]]", index)
        self.assertIn("OH:[[38.3,-84.9],[42.1,-80.4]]", index)
        self.assertIn("IN:[[37.7,-88.2],[41.9,-84.7]]", index)
        self.assertIn("IL:[[36.9,-91.6],[42.6,-86.9]]", index)
        self.assertIn("MI:[[41.6,-90.5],[48.4,-82.3]]", index)
        self.assertIn("WI:[[42.5,-92.9],[47.1,-86.8]]", index)
        self.assertIn("MN:[[43.5,-97.2],[49.4,-89.5]]", index)
        self.assertIn("IA:[[40.4,-96.6],[43.5,-90.1]]", index)
        self.assertIn("MO:[[36.0,-95.8],[40.6,-89.1]]", index)
        self.assertIn("PA:[[39.72,-80.52],[42.27,-74.69]]", index)
        self.assertIn("MD:[[37.91,-79.49],[39.72,-75.05]]", index)
        self.assertIn("DE:[[38.45,-75.79],[39.84,-75.05]]", index)
        self.assertIn("NJ:[[38.93,-75.56],[41.36,-73.89]]", index)
        self.assertIn("NY:[[40.50,-79.76],[45.02,-71.86]]", index)
        self.assertIn("CT:[[40.95,-73.73],[42.05,-71.79]]", index)
        self.assertIn("RI:[[41.15,-71.86],[42.02,-71.12]]", index)
        self.assertIn("MA:[[41.24,-73.51],[42.89,-69.93]]", index)
        self.assertIn("VT:[[42.73,-73.44],[45.02,-71.46]]", index)
        self.assertIn("NH:[[42.70,-72.56],[45.31,-70.61]]", index)
        self.assertIn("ME:[[42.98,-71.08],[47.46,-66.95]]", index)
        self.assertIn("ND:[[45.93,-104.05],[49.00,-96.55]]", index)
        self.assertIn("SD:[[42.48,-104.06],[45.95,-96.44]]", index)
        self.assertIn("NE:[[40.00,-104.05],[43.00,-95.31]]", index)
        self.assertIn("KS:[[36.99,-102.05],[40.00,-94.59]]", index)
        self.assertIn("MT:[[44.36,-116.05],[49.00,-104.04]]", index)
        self.assertIn("WY:[[41.00,-111.06],[45.01,-104.05]]", index)
        self.assertIn("CO:[[36.99,-109.06],[41.00,-102.04]]", index)
        self.assertIn("ID:[[41.99,-117.24],[49.00,-111.04]]", index)
        self.assertIn("UT:[[37.00,-114.05],[42.00,-109.04]]", index)
        self.assertIn("AZ:[[31.33,-114.82],[37.00,-109.05]]", index)
        self.assertIn("NM:[[31.33,-109.05],[37.00,-103.00]]", index)
        self.assertIn("NV:[[35.00,-120.01],[42.00,-114.04]]", index)
        self.assertIn("CA:[[32.53,-124.41],[42.01,-114.13]]", index)
        self.assertIn("OR:[[41.99,-124.57],[46.29,-116.46]]", index)
        self.assertIn("WA:[[45.54,-124.76],[49.00,-116.92]]", index)
        self.assertIn("AK:[[51.21,-179.15],[71.39,-129.98]]", index)
        self.assertIn("HI:[[18.91,-160.25],[22.24,-154.81]]", index)
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
            "<title>Church of God Directory — Florida, the Southeast, South-Central, the Upper South, the Midwest, the Mid-Atlantic, the Northeast, northern New England, the Plains, the Mountain West, the Southwest, and the Pacific</title>",
            directory,
        )
        self.assertIn("Church of God Directory — Florida, the Southeast, South-Central, the Upper South, the Midwest, the Mid-Atlantic, the Northeast, northern New England, the Plains, the Mountain West, the Southwest, and the Pacific", directory)
        self.assertIn("state==='LA'?'Parish':'County'", directory)
        self.assertIn("function countyKind", directory)
        self.assertIn("City and Borough|Census Area|Municipality|Borough|Parish|County", directory)
        self.assertIn("/ city$/.test(name)", directory)
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
        self.assertIn("python scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX VA WV KY OH IN IL MI WI MN IA MO PA MD DE NJ NY CT RI MA VT NH ME ND SD NE KS MT WY CO ID UT AZ NM NV CA OR WA AK HI", workflow)
        self.assertIn("timeout-minutes: 90", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("::warning::Held", workflow)
        self.assertIn("GITHUB_STEP_SUMMARY", workflow)
        self.assertIn('Monthly refresh held states', workflow)
        self.assertIn("gh issue create --title", workflow)
        self.assertIn("gh issue comment", workflow)
        self.assertNotIn("python scripts/refresh.py FL\n", workflow)
        self.assertNotIn("python scripts/refresh.py FL GA\n", workflow)
        self.assertNotIn("python scripts/refresh.py FL GA AL SC NC TN MS\n", workflow)
        self.assertNotIn("python scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX\n", workflow)
        self.assertNotIn("python scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX VA WV KY OH IN IL MI WI MN IA MO\n", workflow)
        self.assertNotIn("python scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX VA WV KY OH IN IL MI WI MN IA MO PA MD DE NJ\n", workflow)
        self.assertIn(
            "Refresh Florida, Georgia, Alabama, South Carolina, North Carolina, Tennessee, Mississippi, Louisiana, Arkansas, Oklahoma, Texas, Virginia, West Virginia, Kentucky, Ohio, Indiana, Illinois, Michigan, Wisconsin, Minnesota, Iowa, Missouri, Pennsylvania, Maryland, Delaware, New Jersey, New York, Connecticut, Rhode Island, Massachusetts, Vermont, New Hampshire, Maine, North Dakota, South Dakota, Nebraska, Kansas, Montana, Wyoming, Colorado, Idaho, Utah, Arizona, New Mexico, Nevada, California, Oregon, Washington, Alaska, and Hawaii church directory",
            workflow,
        )
        self.assertNotIn(
            "Refresh Florida, Georgia, Alabama, South Carolina, North Carolina, Tennessee, Mississippi, Louisiana, Arkansas, Oklahoma, Texas, Virginia, West Virginia, Kentucky, Ohio, Indiana, Illinois, Michigan, Wisconsin, Minnesota, Iowa, Missouri, Pennsylvania, Maryland, Delaware, and New Jersey church directory",
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
        # Locator binding for this batch is OH 173, IN 105, IL 120, MI 94.
        # Floors sit a little under that so a few-record drift still passes.
        self.assertGreaterEqual(self.counts["OH"], 160)
        self.assertGreaterEqual(self.counts["IN"], 95)
        self.assertGreaterEqual(self.counts["IL"], 110)
        self.assertGreaterEqual(self.counts["MI"], 85)
        # Locator binding for this batch is WI 18, MN 20, IA 15, MO 58.
        # Floors sit on that complete count. Iowa is the smallest published state.
        self.assertGreaterEqual(self.counts["WI"], 15)
        self.assertGreaterEqual(self.counts["MN"], 18)
        self.assertGreaterEqual(self.counts["IA"], 15)
        self.assertGreaterEqual(self.counts["MO"], 50)
        # Locator binding for this batch is PA 107, MD 120, DE 22, NJ 98.
        # Floors sit a little under that so a few-record drift still passes.
        self.assertGreaterEqual(self.counts["PA"], 100)
        self.assertGreaterEqual(self.counts["MD"], 110)
        self.assertGreaterEqual(self.counts["DE"], 20)
        self.assertGreaterEqual(self.counts["NJ"], 90)
        # Locator binding for NE-1 is NY 236, CT 72, RI 22, MA 70.
        # Floors sit a little under that so a few-record drift still passes.
        self.assertGreaterEqual(self.counts["NY"], 220)
        self.assertGreaterEqual(self.counts["CT"], 65)
        self.assertGreaterEqual(self.counts["RI"], 20)
        self.assertGreaterEqual(self.counts["MA"], 65)
        # Locator binding for NE-2 is VT 1, NH 6, ME 25.
        # Floors sit under the locator total. They are not an exact count.
        self.assertGreaterEqual(self.counts["VT"], 1)
        self.assertGreaterEqual(self.counts["NH"], 1)
        self.assertGreaterEqual(self.counts["ME"], 22)
        # Locator binding for PL-1 is ND 12, SD 9, NE 12, KS 21.
        self.assertGreaterEqual(self.counts["ND"], 1)
        self.assertGreaterEqual(self.counts["SD"], 1)
        self.assertGreaterEqual(self.counts["NE"], 1)
        self.assertGreaterEqual(self.counts["KS"], 18)
        # Locator binding for MT-1 is MT 6, WY 1, CO 31, ID 13, UT 14.
        self.assertGreaterEqual(self.counts["MT"], 1)
        self.assertGreaterEqual(self.counts["WY"], 1)
        self.assertGreaterEqual(self.counts["CO"], 28)
        self.assertGreaterEqual(self.counts["ID"], 1)
        self.assertGreaterEqual(self.counts["UT"], 1)
        # Locator binding for SW-1 is AZ 77, NM 53, NV 13.
        self.assertGreaterEqual(self.counts["AZ"], 70)
        self.assertGreaterEqual(self.counts["NM"], 48)
        self.assertGreaterEqual(self.counts["NV"], 1)
        # Locator binding for PC-1 is CA 261, OR 35, WA 44, AK 21, HI 21.
        # Floors sit a little under that so a few-record drift still passes.
        self.assertGreaterEqual(self.counts["CA"], 240)
        self.assertGreaterEqual(self.counts["OR"], 30)
        self.assertGreaterEqual(self.counts["WA"], 40)
        self.assertGreaterEqual(self.counts["AK"], 18)
        self.assertGreaterEqual(self.counts["HI"], 18)
        self.assertGreaterEqual(len(self.churches), 4600)
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
