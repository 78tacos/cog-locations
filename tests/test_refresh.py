import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refresh

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_page.html"
JOSEPH_README = """# Tampa Bay Church of God Map

A project I made because the official Church of God website is really not great when trying to find a location.

Updated monthly.

**Live map:** https://78tacos.github.io/tampa-churches/
"""


def _church(**overrides):
    record = {
        "name": "Example",
        "pastor": "A Pastor",
        "address1": "1 Main Street",
        "address2": "",
        "city": "Tampa",
        "state": "FL",
        "zip": "33602",
        "phone": "(813) 555-0100",
        "website": "",
        "email": "office@example.com",
    }
    record.update(overrides)
    return record


class ParseSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.churches = refresh.parse_churches(cls.html)
        cls.by_name = {}
        for church in cls.churches:
            cls.by_name.setdefault(church["name"], []).append(church)

    def test_saved_sample_parses_locator_fields(self):
        self.assertEqual(len(self.churches), 13)
        self.assertEqual(refresh.page_counts(self.html), (1, 10, 629))
        names = {church["name"] for church in self.churches}
        self.assertNotIn("FL", names)
        self.assertNotIn("629", names)

        first = self.by_name["103rd Street Church of God Corp"][0]
        self.assertEqual(first["pastor"], "Roger D Bolman Jr")
        self.assertEqual(first["address1"], "10356 103rd Street")
        self.assertEqual(first["address2"], "")
        self.assertEqual(first["city"], "Jacksonville")
        self.assertEqual(first["state"], "FL")
        self.assertEqual(first["zip"], "32210")
        self.assertEqual(first["phone"], "(904) 771-3045")
        self.assertEqual(first["website"], "103churchofgod.com")
        self.assertEqual(first["email"], "church103cog@gmail.com")

        temple = self.by_name["5th Avenue Temple"][0]
        self.assertEqual(temple["website"], "")
        self.assertEqual(temple["email"], "fifthavetemple@gmail.com")
        self.assertEqual(temple["address1"], "211 NW 5th Avenue")
        self.assertEqual(temple["address2"], "")
        self.assertEqual(temple["city"], "Fort Lauderdale")
        self.assertEqual(temple["zip"], "33311")

        abide = self.by_name["Abide Church"][0]
        self.assertEqual(abide["pastor"], "Giovanni Angel Munoz")
        self.assertEqual(abide["address1"], "913 Dew Bloom Road")
        self.assertEqual(abide["address2"], "")
        self.assertEqual(abide["city"], "Brandon")
        self.assertEqual(abide["state"], "FL")
        self.assertEqual(abide["zip"], "33511")
        self.assertEqual(abide["phone"], "(813) 681-6503")
        self.assertEqual(abide["website"], "")
        self.assertEqual(abide["email"], "abidechurchfl@gmail.com")

        altha = self.by_name["Altha"][0]
        self.assertEqual(altha["address1"], "26000 NE Fugua Circle")
        self.assertEqual(altha["address2"], "")
        self.assertEqual(altha["city"], "Altha")
        self.assertEqual(altha["zip"], "32421")

        alton = self.by_name["Alton"][0]
        self.assertEqual(alton["email"], "")
        self.assertEqual(alton["website"], "www.altonchurchofgod.org")
        self.assertEqual(alton["pastor"], "Jeremy Kyle Davis")

        largo = next(church for church in self.by_name["Abundant Life"] if church["city"] == "Largo")
        self.assertEqual(largo["pastor"], "Kirk A Carey")
        self.assertEqual(largo["address1"], "1550 S Belcher Road")
        self.assertEqual(largo["zip"], "33771")
        self.assertEqual(largo["phone"], "(727) 210-5433")
        self.assertEqual(largo["website"], "ALM.TV")
        self.assertEqual(largo["email"], "finance@alm.tv")

        nine = self.by_name["Nine Digit Chapel"][0]
        self.assertEqual(nine["pastor"], "Ada Example")
        self.assertEqual(nine["address1"], "1 Zip Road")
        self.assertEqual(nine["city"], "Tampa")
        self.assertEqual(nine["state"], "FL")
        self.assertEqual(nine["zip"], "33602")
        self.assertEqual(nine["phone"], "(813) 555-0199")
        self.assertEqual(nine["email"], "nine@example.com")

        quiet = self.by_name["Quiet Chapel"][0]
        self.assertEqual(quiet["pastor"], "")
        self.assertEqual(quiet["address1"], "15 Oak Street")
        self.assertEqual(quiet["address2"], "")
        self.assertEqual(quiet["city"], "Tampa")
        self.assertEqual(quiet["zip"], "33602")
        self.assertEqual(quiet["phone"], "(813) 555-0100")
        self.assertEqual(quiet["website"], "")
        self.assertEqual(quiet["email"], "")

        rock = self.by_name["Rock & River"][0]
        self.assertEqual(rock["pastor"], "")
        self.assertEqual(rock["address1"], "100 Main Street")
        self.assertEqual(rock["address2"], "Suite 4")
        self.assertEqual(rock["city"], "St Petersburg")
        self.assertEqual(rock["state"], "FL")
        self.assertEqual(rock["zip"], "33701")
        self.assertEqual(rock["phone"], "")
        self.assertEqual(rock["website"], "https://example.org/path")
        self.assertEqual(rock["email"], "")

        for church in self.churches:
            self.assertEqual(list(church), list(refresh.CONTACT_KEYS))
            self.assertEqual(church["state"], "FL")
            self.assertRegex(church["zip"], r"^\d{5}$")


class DirectoryRuleTests(unittest.TestCase):
    def test_city_groups_match_the_current_directory(self):
        churches = json.loads((ROOT / "churches.json").read_text(encoding="utf-8"))
        for church in churches:
            self.assertEqual(refresh.city_group_for(church["city"]), church["city_group"])
        self.assertEqual(refresh.city_group_for("St Petersburg"), "Saint Petersburg")
        self.assertEqual(refresh.city_group_for("St. Petersburg"), "Saint Petersburg")
        self.assertEqual(refresh.city_group_for("Brandenton"), "Bradenton")
        self.assertEqual(refresh.city_group_for("Tampa"), "Tampa")

    def test_filter_keeps_target_counties_and_the_bounding_box(self):
        hillsborough_north = _church(county="Hillsborough", lat=29.2, lng=-82.4, approx=False)
        pasco = _church(county="Pasco", lat=28.6, lng=-82.5, approx=False)
        polk_inside = _church(county="Polk", lat=27.8, lng=-82.0, approx=False)
        polk_outside = _church(county="Polk", lat=28.0, lng=-81.5, approx=False)
        miami = _church(county="Miami-Dade", lat=25.8, lng=-80.2, approx=False)
        zip_inside = _church(county="", lat=26.9, lng=-82.95, approx=True)
        zip_corner = _church(county="", lat=28.5, lng=-81.9, approx=True)
        zip_outside = _church(county="", lat=26.89, lng=-82.5, approx=True)
        self.assertTrue(refresh.keep_church(hillsborough_north))
        self.assertTrue(refresh.keep_church(pasco))
        self.assertTrue(refresh.keep_church(polk_inside))
        self.assertFalse(refresh.keep_church(polk_outside))
        self.assertFalse(refresh.keep_church(miami))
        self.assertTrue(refresh.keep_church(zip_inside))
        self.assertTrue(refresh.keep_church(zip_corner))
        self.assertFalse(refresh.keep_church(zip_outside))

    def test_unchanged_address_reuses_saved_coordinates(self):
        existing = [
            {
                **_church(pastor="Old Name"),
                "lat": 27.930365515933,
                "lng": -82.271565015116,
                "approx": False,
                "county": "Hillsborough",
                "city_group": "Tampa",
            }
        ]
        parsed = [_church(pastor="New Name", phone="(813) 555-0199")]
        census = {refresh.address_key(parsed[0]): (1.0, 2.0, "Polk")}
        resolved = refresh.resolve_locations(parsed, existing, census, {})
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["pastor"], "New Name")
        self.assertEqual(resolved[0]["phone"], "(813) 555-0199")
        self.assertEqual(resolved[0]["lat"], 27.930365515933)
        self.assertEqual(resolved[0]["lng"], -82.271565015116)
        self.assertFalse(resolved[0]["approx"])
        self.assertEqual(resolved[0]["county"], "Hillsborough")
        self.assertEqual(list(resolved[0]), list(refresh.SCHEMA_KEYS))

    def test_zip_center_fallback_is_approximate(self):
        parsed = [_church(address1="PO Box 1", zip="33572", city="Apollo Beach")]
        centroids = {"33572": (27.766168, -82.400285)}
        resolved = refresh.resolve_locations(parsed, [], {}, centroids)
        self.assertEqual(resolved[0]["lat"], 27.766168)
        self.assertEqual(resolved[0]["lng"], -82.400285)
        self.assertTrue(resolved[0]["approx"])
        self.assertEqual(resolved[0]["county"], "")
        self.assertEqual(resolved[0]["city_group"], "Apollo Beach")

    def test_census_match_sets_county_and_is_not_approximate(self):
        parsed = [_church()]
        key = refresh.address_key(parsed[0])
        resolved = refresh.resolve_locations(parsed, [], {key: (27.95, -82.46, "Hillsborough")}, {})
        self.assertEqual(resolved[0]["lat"], 27.95)
        self.assertEqual(resolved[0]["lng"], -82.46)
        self.assertFalse(resolved[0]["approx"])
        self.assertEqual(resolved[0]["county"], "Hillsborough")

    def test_new_churches_append_after_the_existing_order(self):
        existing = [
            _church(name="Zulu", address1="9 Zulu Road"),
            _church(name="Alpha", address1="1 Alpha Road"),
        ]
        incoming = [
            _church(name="Alpha", address1="1 Alpha Road", pastor="Updated"),
            _church(name="Bravo", address1="2 Bravo Road"),
            _church(name="Cedar", address1="3 Cedar Road"),
        ]
        ordered = refresh.order_churches(incoming, existing)
        self.assertEqual([church["name"] for church in ordered], ["Alpha", "Bravo", "Cedar"])
        self.assertEqual(ordered[0]["pastor"], "Updated")

    def test_target_county_fips(self):
        self.assertEqual(refresh.FL_COUNTY_FIPS["057"], "Hillsborough")
        self.assertEqual(refresh.FL_COUNTY_FIPS["103"], "Pinellas")
        self.assertEqual(refresh.FL_COUNTY_FIPS["101"], "Pasco")
        self.assertEqual(refresh.FL_COUNTY_FIPS["081"], "Manatee")
        self.assertEqual(refresh.FL_COUNTY_FIPS["115"], "Sarasota")


class FormatTests(unittest.TestCase):
    def test_census_batch_parser_keeps_florida_matches(self):
        text = "\n".join(
            [
                '"1","913 Dew Bloom Road, Brandon, FL, 33511","Match","Exact","913 DEW BLOOM RD, BRANDON, FL, 33511","-82.271565015116,27.930365515933","651206055","R","12","057","013312","3026"',
                '"2","PO Box 3226, Apollo Beach, FL, 33572","No_Match"',
                '"3","1 Peachtree St, Atlanta, GA, 30303","Match","Exact","1 PEACHTREE ST, ATLANTA, GA, 30303","-84.3,33.7","1","L","13","121","000100","1000"',
                '"4","1 Main, Tampa, FL, 33602","Match","Non_Exact","1 MAIN, TAMPA, FL, 33602","-82.45,27.95","9","L","12","57","000100","1000"',
            ]
        )
        hits = refresh.parse_census_batch(text)
        self.assertEqual(set(hits), {"1", "4"})
        self.assertEqual(hits["1"], (27.930365515933, -82.271565015116, "Hillsborough"))
        self.assertEqual(hits["4"][2], "Hillsborough")

    def test_census_csv_quotes_commas(self):
        encoded = refresh.census_csv([_church(address1="100 Main Street, Apt 2", address2="Suite 4")])
        self.assertIn(b'"100 Main Street, Apt 2 Suite 4"', encoded)

    def test_gazetteer_pipe_and_tab(self):
        piped = "GEOID|GEOIDFQ|INTPTLAT|INTPTLONG\n33511|860Z200US33511|27.909778|-82.295738\n"
        tabbed = "GEOID\tALAND\tINTPTLAT\tINTPTLONG\n33572\t1\t27.766168\t-82.400285\n"
        self.assertEqual(refresh.parse_gazetteer(piped)["33511"], (27.909778, -82.295738))
        self.assertEqual(refresh.parse_gazetteer(tabbed)["33572"], (27.766168, -82.400285))

    def test_geonames_uses_the_first_postal_coordinate(self):
        text = (
            "US\t34272\tLaurel\tFlorida\tFL\tSarasota\t115\t\t\t27.147\t-82.4255\t4\n"
            "US\t34272\tOther\tFlorida\tFL\tSarasota\t115\t\t\t1\t2\t4\n"
        )
        self.assertEqual(refresh.parse_geonames(text)["34272"], (27.147, -82.4255))

    def test_writers_match_the_pages_files(self):
        churches = json.loads((ROOT / "churches.json").read_text(encoding="utf-8"))
        self.assertEqual(refresh.render_json(churches), (ROOT / "churches.json").read_text(encoding="utf-8"))
        self.assertEqual(refresh.render_js(churches), (ROOT / "churches.js").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "churches.js").read_text(encoding="utf-8").startswith("const CHURCHES="))
        self.assertTrue((ROOT / "churches.js").read_text(encoding="utf-8").endswith("];"))

    def test_pages_entrypoints_stay_at_the_repo_root(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        directory = (ROOT / "directory.html").read_text(encoding="utf-8")
        self.assertIn('src="churches.js"', index)
        self.assertIn('src="churches.js"', directory)
        self.assertIn('href="directory.html"', index)
        self.assertIn('href="index.html"', directory)

    def test_readme_keeps_josephs_opening(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith(JOSEPH_README))
        self.assertIn("https://78tacos.github.io/tampa-churches/", text)
        self.assertIn("scripts/refresh.py", text)


if __name__ == "__main__":
    unittest.main()
