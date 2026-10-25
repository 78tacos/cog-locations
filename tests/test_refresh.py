import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refresh

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_page.html"
JOSEPH_README = """# Church of God Map — Florida, the Southeast, and South-Central

A project I made because the official Church of God website is really not great when trying to find a location.

Updated monthly.

**Live map:** https://78tacos.github.io/cog-locations/
"""

# Snapshot of the Florida county names the directory already uses.
FLORIDA_COUNTY_FIPS = {
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
        counties_by_state = {
            "FL": set(refresh.FL_COUNTY_FIPS.values()),
            "GA": set(refresh.COUNTY_FIPS_BY_STATE["13"].values()),
            "AL": set(refresh.COUNTY_FIPS_BY_STATE["01"].values()),
            "SC": set(refresh.COUNTY_FIPS_BY_STATE["45"].values()),
            "NC": set(refresh.COUNTY_FIPS_BY_STATE["37"].values()),
            "TN": set(refresh.COUNTY_FIPS_BY_STATE["47"].values()),
            "MS": set(refresh.COUNTY_FIPS_BY_STATE["28"].values()),
            "LA": set(refresh.COUNTY_FIPS_BY_STATE["22"].values()),
            "AR": set(refresh.COUNTY_FIPS_BY_STATE["05"].values()),
            "OK": set(refresh.COUNTY_FIPS_BY_STATE["40"].values()),
            "TX": set(refresh.COUNTY_FIPS_BY_STATE["48"].values()),
        }
        for church in churches:
            self.assertEqual(refresh.city_group_for(church["city"]), church["city_group"])
            if church.get("county"):
                self.assertIn(church["county"], counties_by_state[church["state"]])
        self.assertEqual(refresh.city_group_for("St Petersburg"), "Saint Petersburg")
        self.assertEqual(refresh.city_group_for("St. Petersburg"), "Saint Petersburg")
        self.assertEqual(refresh.city_group_for("Brandenton"), "Bradenton")
        self.assertEqual(refresh.city_group_for("Tampa"), "Tampa")

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
        self.assertEqual(refresh.county_from_fips("12", "057"), "Hillsborough")
        self.assertEqual(refresh.county_from_fips("12", "086"), "Miami-Dade")
        self.assertEqual(refresh.county_from_fips("12", "109"), "St. Johns")
        self.assertEqual(refresh.county_from_fips("12", "027"), "DeSoto")
        self.assertEqual(refresh.county_from_fips("13", "121"), "Fulton")
        self.assertEqual(refresh.county_from_fips("13", "051"), "Chatham")
        self.assertEqual(refresh.county_from_fips("01", "001"), "Autauga")
        self.assertEqual(refresh.county_from_fips("22", "071"), "Orleans")
        self.assertEqual(refresh.county_from_fips("05", "119"), "Pulaski")
        self.assertEqual(refresh.county_from_fips("40", "109"), "Oklahoma")
        self.assertEqual(refresh.county_from_fips("48", "201"), "Harris")
        self.assertNotIn("Parish", refresh.county_from_fips("22", "071"))
        self.assertEqual(refresh.FL_COUNTY_FIPS, FLORIDA_COUNTY_FIPS)

    def test_parse_national_county_snippet(self):
        text = "GA,13,121,Fulton County,H1\nFL,12,057,Hillsborough County,H1\nLA,22,071,Orleans Parish,H6\n"
        states, counties = refresh.parse_national_county(text)
        self.assertEqual(states, {"GA": "13", "FL": "12", "LA": "22"})
        self.assertEqual(counties["13"]["121"], "Fulton")
        self.assertEqual(counties["12"]["057"], "Hillsborough")
        self.assertEqual(counties["22"]["071"], "Orleans")


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
        hits = refresh.parse_census_batch(text, {"12"})
        self.assertEqual(set(hits), {"1", "4"})
        self.assertEqual(hits["1"], (27.930365515933, -82.271565015116, "Hillsborough"))
        self.assertEqual(hits["4"][2], "Hillsborough")

    def test_census_batch_requires_an_explicit_state_filter(self):
        text = '"3","1 Peachtree St, Atlanta, GA, 30303","Match","Exact","1 PEACHTREE ST, ATLANTA, GA, 30303","-84.3,33.7","1","L","13","121","000100","1000"'
        with self.assertRaises(TypeError):
            refresh.parse_census_batch(text)
        with self.assertRaises(TypeError):
            refresh.parse_census_batch(text, None)
        with self.assertRaises(TypeError):
            refresh.geocode_addresses([], None)

    def test_geocode_addresses_drops_a_hit_outside_the_church_state(self):
        florida = _church(name="Florida Chapel", address1="1 Florida St")
        georgia = _church(
            name="Georgia Chapel",
            state="GA",
            address1="1 Peachtree St",
            city="Atlanta",
            zip="30303",
        )
        allow_lists: list[set[str]] = []

        def fake_post(churches):
            rows = []
            for index, _church_row in enumerate(churches, start=1):
                rows.append(
                    f'"{index}","x","Match","Exact","x","-84.3,33.7","1","L","13","121","0","1"'
                )
            return "\n".join(rows)

        original_post = refresh._post_census
        original_parse = refresh.parse_census_batch

        def spy_parse(text, state_fips):
            allow_lists.append(set(state_fips))
            return original_parse(text, state_fips)

        refresh._post_census = fake_post
        refresh.parse_census_batch = spy_parse
        try:
            hits = refresh.geocode_addresses(
                [florida, georgia],
                refresh.state_fips_for(["FL", "GA"]),
                sleep=lambda _seconds: None,
            )
        finally:
            refresh._post_census = original_post
            refresh.parse_census_batch = original_parse
        self.assertEqual(allow_lists, [{"12"}, {"13"}])
        self.assertNotIn(refresh.address_key(florida), hits)
        self.assertEqual(hits[refresh.address_key(georgia)], (33.7, -84.3, "Fulton"))

    def test_census_batch_parser_keeps_requested_non_florida_matches(self):
        text = "\n".join(
            [
                '"1","913 Dew Bloom Road, Brandon, FL, 33511","Match","Exact","913 DEW BLOOM RD, BRANDON, FL, 33511","-82.271565015116,27.930365515933","651206055","R","12","057","013312","3026"',
                '"3","1 Peachtree St, Atlanta, GA, 30303","Match","Exact","1 PEACHTREE ST, ATLANTA, GA, 30303","-84.3,33.7","1","L","13","121","000100","1000"',
            ]
        )
        florida_only = refresh.parse_census_batch(text, refresh.state_fips_for(["FL"]))
        both = refresh.parse_census_batch(text, refresh.state_fips_for(["FL", "GA"]))
        self.assertEqual(set(florida_only), {"1"})
        self.assertEqual(set(both), {"1", "3"})
        self.assertEqual(both["3"], (33.7, -84.3, "Fulton"))

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
        self.assertIn("https://78tacos.github.io/cog-locations/", text)
        self.assertIn("scripts/refresh.py", text)
        self.assertIn(
            "A project I made because the official Church of God website is really not great when trying to find a location.",
            text,
        )
        self.assertIn(
            "The published directory now includes Florida, the Southeast states (Georgia, Alabama, South Carolina, North Carolina, Tennessee, and Mississippi), and the South-Central states (Louisiana, Arkansas, Oklahoma, and Texas).",
            text,
        )
        self.assertIn("`python3 scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX` rebuilds it.", text)
        self.assertIn(
            "```bash\npython3 scripts/refresh.py FL GA AL SC NC TN MS LA AR OK TX\n```",
            text,
        )
        self.assertNotIn("```bash\npython3 scripts/refresh.py\n```", text)
        self.assertIn("https://78tacos.github.io/cog-locations/", text)
        self.assertNotIn("stay Florida-only", text)
        self.assertNotIn("Florida and Georgia (pilot)", text)
        self.assertNotIn("https://78tacos.github.io/florida-churches/", text)


class FallbackGeocodeTests(unittest.TestCase):
    def _chain(self, census=None, nominatim=None, arcgis=None):
        def wrap(value):
            def geocoder(church, street):
                if isinstance(value, Exception):
                    raise value
                return value
            return geocoder
        return (("census", wrap(census), 0), ("nominatim", wrap(nominatim), 0), ("arcgis", wrap(arcgis), 0))

    def _run(self, church, **kw):
        original = refresh.GEOCODER_CHAIN
        refresh.GEOCODER_CHAIN = self._chain(**kw)
        try:
            return refresh.fallback_geocode(church, sleep=lambda _: None)
        finally:
            refresh.GEOCODER_CHAIN = original

    def test_street_candidates(self):
        self.assertEqual(refresh.street_candidates(_church(address1="PO Box 476")), [])
        self.assertEqual(
            refresh.street_candidates(_church(address1="2523 US Hwy 27 S Suite 202")),
            ["2523 US Hwy 27 S Suite 202", "2523 US Hwy 27 S"],
        )
        self.assertEqual(
            refresh.street_candidates(_church(address1="PO Box 1", address2="12 Oak Street")),
            ["12 Oak Street"],
        )
        self.assertEqual(refresh.street_candidates(_church(address1="Grace Chapel")), [])

    def test_city_spelling_fixed(self):
        self.assertEqual(refresh.clean_city("Brandenton"), "Bradenton")

    def test_first_exact_match_wins(self):
        hit = self._run(_church(), census=None, nominatim=(27.0, -82.0, "Pasco"), arcgis=(1.0, 1.0, "X"))
        self.assertEqual(hit, (27.0, -82.0, "Pasco", "nominatim", False))

    def test_po_box_only_is_not_geocoded(self):
        self.assertIsNone(self._run(_church(address1="PO Box 9"), census=(27.0, -82.0, "Pasco")))

    def test_ambiguous_matches_stay_approximate_at_middle(self):
        points = [(27.7199, -82.4366, "Hillsborough"), (27.7202, -82.4321, "Hillsborough")]
        hit = self._run(_church(), census=refresh.Ambiguous(points))
        self.assertTrue(hit[4])
        self.assertEqual(hit[3], "ambiguous-street")
        self.assertAlmostEqual(hit[0], 27.72005, places=4)

    def test_pick_rejects_distant_matches(self):
        with self.assertRaises(refresh.Ambiguous):
            refresh._pick([(27.7199, -82.4366, ""), (27.7202, -82.4321, "")])
        self.assertEqual(refresh._pick([(27.0, -82.0, "A"), (27.0001, -82.0, "A")]), (27.0, -82.0, "A"))

    def test_same_place_requires_zip_or_city(self):
        church = _church(city="Brandenton", zip="34207")
        self.assertTrue(refresh._same_place(church, "34207", ""))
        self.assertTrue(refresh._same_place(church, "", "Bradenton"))
        self.assertFalse(refresh._same_place(church, "33602", "Tampa"))

    def test_numberless_address_stays_at_the_zip_center(self):
        church = _church(
            address1="Church Street at Cain Avenue",
            city="Russellville",
            state="AR",
            zip="72802",
        )
        old = refresh.make_record(church, 35.3036, -93.1224, False, "Pope")
        hits = {refresh.address_key(church): (35.3036, -93.1224, "Pope", False)}
        centroids = {"72802": (35.2781, -93.1334)}
        [record] = refresh.resolve_locations([church], [old], hits, centroids)
        self.assertTrue(record["approx"])
        self.assertEqual(record["lat"], 35.2781)
        self.assertEqual(record["lng"], -93.1334)
        self.assertEqual(record["county"], "")
        [kept] = refresh.resolve_locations([church], [old], hits, {})
        self.assertFalse(kept["approx"])
        self.assertEqual(kept["lat"], 35.3036)

    def test_saved_approx_pin_is_replaced_by_new_exact_hit(self):
        church = _church()
        old = dict(refresh.make_record(church, 1.0, 2.0, True, ""))
        hits = {refresh.address_key(church): (27.5, -82.5, "Hillsborough", False)}
        [record] = refresh.resolve_locations([church], [old], hits, {})
        self.assertEqual((record["lat"], record["approx"], record["county"]), (27.5, False, "Hillsborough"))


class StatewideTests(unittest.TestCase):
    def test_every_county_is_kept_and_unplaced_records_stay_listed(self):
        churches = [
            _church(name="Miami", city="Miami", zip="33101", address1="1 A St"),
            _church(name="Nowhere", city="Gone", zip="99999", address1="PO Box 1"),
        ]
        hits = {refresh.address_key(churches[0]): (25.77, -80.19, "Miami-Dade", False)}
        records = refresh.resolve_locations(churches, [], hits, {})
        self.assertEqual([r["name"] for r in records], ["Miami", "Nowhere"])
        self.assertEqual(records[0]["county"], "Miami-Dade")
        self.assertIsNone(records[1]["lat"])
        self.assertFalse(refresh.has_pin(records[1]))
        self.assertFalse(hasattr(refresh, "keep_church"))

    def test_missing_county_filled_from_point_lookup_only_for_pins(self):
        pinned = refresh.make_record(_church(), 28.0, -82.0, True, "")
        unpinned = refresh.make_record(_church(), None, None, False, "")
        known = refresh.make_record(_church(), 28.3, -82.4, False, "Pasco")
        calls = []
        refresh.fill_missing_counties(
            [pinned, unpinned, known],
            lookup=lambda lat, lng, allowed=None: calls.append((lat, lng, set(allowed))) or "Polk",
            sleep=lambda _: None,
        )
        self.assertEqual([pinned["county"], unpinned["county"], known["county"]], ["Polk", "", "Pasco"])
        self.assertEqual(calls, [(28.0, -82.0, {"12"})])

    def test_missing_georgia_county_uses_georgia_fips(self):
        pinned = refresh.make_record(
            _church(state="GA", city="Atlanta", zip="30303"), 33.7, -84.3, False, ""
        )
        calls = []
        refresh.fill_missing_counties(
            [pinned],
            lookup=lambda lat, lng, allowed=None: calls.append(set(allowed)) or "Fulton",
            sleep=lambda _: None,
        )
        self.assertEqual(calls, [{"13"}])
        self.assertEqual(pinned["county"], "Fulton")

    def test_missing_louisiana_county_uses_louisiana_fips(self):
        pinned = refresh.make_record(
            _church(state="LA", city="New Orleans", zip="70112"), 29.95, -90.07, False, ""
        )
        calls = []
        refresh.fill_missing_counties(
            [pinned],
            lookup=lambda lat, lng, allowed=None: calls.append(set(allowed)) or "Orleans",
            sleep=lambda _: None,
        )
        self.assertEqual(calls, [{"22"}])
        self.assertEqual(pinned["county"], "Orleans")

    def test_short_zip4_still_parses_city_state_and_five_digit_zip(self):
        html = (
            "<p><b>Cornerstone Church of God</b></p><p>Pastor: Chad Edward Balentine</p>"
            "<p>804 Lake Road</p><p>Dyersburg, TN, 38025-152</p>"
            "<p>Phone: (731) 285-1577</p>"
            "<p><b>The Carpenters House</b></p><p>Pastor: Robert E Coburn</p>"
            "<p>3055 US Hwy 31 North</p><p>Marbury, AL, 36051-302</p>"
            "<p>Phone: (205) 217-2600</p>"
        )
        churches = refresh.parse_churches(html)
        self.assertEqual(
            [(c["name"], c["city"], c["state"], c["zip"], c["address2"]) for c in churches],
            [
                ("Cornerstone Church of God", "Dyersburg", "TN", "38025", ""),
                ("The Carpenters House", "Marbury", "AL", "36051", ""),
            ],
        )

    def test_record_without_zip_is_kept_when_it_has_contact_data(self):
        html = (
            "<p><b>North Miami Avenue</b></p><p>Pastor: Jane Doe</p>"
            "<p>Phone: (305) 555-0100</p><p><b>Next</b></p><p>1 Main St</p><p>Miami, FL, 33101</p>"
        )
        names = [c["name"] for c in refresh.parse_churches(html)]
        self.assertEqual(names, ["North Miami Avenue", "Next"])


class CensusStateFilterTests(unittest.TestCase):
    def _response(self, counties, zip_code="33602", city="Tampa", lat=27.95, lng=-82.45):
        payload = {
            "result": {
                "addressMatches": [
                    {
                        "addressComponents": {"zip": zip_code, "city": city},
                        "coordinates": {"x": lng, "y": lat},
                        "geographies": {"Counties": counties},
                    }
                ],
                "geographies": {"Counties": counties},
            }
        }
        return json.dumps(payload).encode()

    def test_point_lookup_skips_other_states_unless_asked(self):
        raw = self._response(
            [
                {"STATE": "13", "COUNTY": "121"},
                {"STATE": "12", "COUNTY": "057"},
            ]
        )
        original = refresh.request_bytes
        refresh.request_bytes = lambda url, **kwargs: raw
        try:
            self.assertEqual(refresh.county_for_point(27.95, -82.45), "Hillsborough")
            self.assertEqual(refresh.county_for_point(33.7, -84.3, {"13"}), "Fulton")
            self.assertEqual(
                refresh.county_for_point(33.7, -84.3, refresh.state_fips_for(["GA"])),
                "Fulton",
            )
        finally:
            refresh.request_bytes = original

    def test_oneline_county_follows_the_church_state(self):
        def fake(url, **kwargs):
            if "Peachtree" in url:
                return self._response(
                    [{"STATE": "13", "COUNTY": "121"}],
                    zip_code="30303",
                    city="Atlanta",
                    lat=33.7,
                    lng=-84.3,
                )
            if "Other" in url:
                return self._response([{"STATE": "12", "COUNTY": "57"}])
            return self._response([{"STATE": "13", "COUNTY": "121"}])

        original = refresh.request_bytes
        refresh.request_bytes = fake
        try:
            florida_hit = refresh.census_oneline(_church(), "9 Other Road")
            outside = refresh.census_oneline(_church(), "1 Main Street")
            georgia = refresh.census_oneline(
                _church(state="GA", city="Atlanta", zip="30303", address1="1 Peachtree St"),
                "1 Peachtree St",
            )
        finally:
            refresh.request_bytes = original
        self.assertEqual(florida_hit, (27.95, -82.45, "Hillsborough"))
        self.assertEqual(outside, (27.95, -82.45, ""))
        self.assertEqual(georgia, (33.7, -84.3, "Fulton"))


class MultiStateCliTests(unittest.TestCase):
    def test_default_is_florida(self):
        self.assertEqual(refresh.parse_states([]), ["FL"])
        self.assertEqual(refresh.region_label(["FL"]), "Florida")
        self.assertEqual(refresh.min_expected_count(["FL"]), refresh.MIN_STATEWIDE)
        self.assertEqual(refresh.state_fips_for(["FL"]), {"12"})

    def test_normalizes_dedupes_and_keeps_order(self):
        self.assertEqual(refresh.parse_states(["fl"]), ["FL"])
        self.assertEqual(refresh.parse_states(["fl", "GA", "FL"]), ["FL", "GA"])
        self.assertEqual(refresh.region_label(["FL", "GA"]), "FL and GA")
        self.assertEqual(refresh.min_expected_count(["FL", "GA"]), refresh.MIN_STATEWIDE)
        self.assertEqual(refresh.min_expected_count(["FL", "GA", "AL"]), refresh.MIN_STATEWIDE)
        self.assertEqual(refresh.state_fips_for(["FL", "GA"]), {"12", "13"})

    def test_rejects_unknown_state_codes(self):
        with self.assertRaises(SystemExit):
            refresh.parse_states(["FX"])
        with self.assertRaises(SystemExit):
            refresh.parse_states(["FL", "ZZ"])

    def test_locator_url_uses_the_requested_state(self):
        florida = refresh.locator_page_url("FL", 0)
        georgia = refresh.locator_page_url("GA", 10)
        self.assertIn("state=FL", florida)
        self.assertIn("int_cur_position=0", florida)
        self.assertIn("mode=citystate_search", florida)
        self.assertIn("state=GA", georgia)
        self.assertIn("int_cur_position=10", georgia)
        self.assertTrue(florida.startswith(refresh.LOCATOR_URL))

    def test_fetch_churches_requests_the_given_state(self):
        urls: list[str] = []

        def fake_request(url, **kwargs):
            urls.append(url)
            return b"<html>Results 1 to 1 of 1</html>"

        original = refresh.request_bytes
        refresh.request_bytes = fake_request
        try:
            refresh.fetch_churches(0, "GA")
            refresh.fetch_churches(0, "FL")
        finally:
            refresh.request_bytes = original
        self.assertIn("state=GA", urls[0])
        self.assertIn("state=FL", urls[1])

    def test_fetch_states_combines_and_pauses_between_states(self):
        calls: list[tuple[float, str]] = []
        sleeps: list[float] = []

        def fake_fetch(delay, state="FL"):
            calls.append((delay, state))
            return [_church(name=state, state=state, address1=f"1 {state} Street")]

        original = refresh.fetch_churches
        refresh.fetch_churches = fake_fetch
        try:
            combined = refresh.fetch_states(3, ["FL", "GA"], sleep=sleeps.append)
        finally:
            refresh.fetch_churches = original
        self.assertEqual(calls, [(3, "FL"), (3, "GA")])
        self.assertEqual(sleeps, [3])
        self.assertEqual([church["state"] for church in combined], ["FL", "GA"])
        self.assertEqual(len(refresh.dedupe(combined)), 2)

    def test_empty_state_fails_even_when_the_combined_total_clears_the_floor(self):
        florida = [_church(name=f"FL {i}", address1=f"{i} Main Street") for i in range(1, 201)]
        with self.assertRaises(SystemExit) as caught:
            refresh.require_complete_download(["FL", "TX"], florida)
        self.assertIn("TX 0", str(caught.exception))
        self.assertIn(str(refresh.MIN_PER_STATE), str(caught.exception))

    def test_near_empty_state_fails_before_the_combined_floor(self):
        florida = [_church(name=f"FL {i}", address1=f"{i} Main Street") for i in range(1, 201)]
        texas = [
            _church(name=f"TX {i}", state="TX", city="Houston", address1=f"{i} Texas Ave", zip="77002")
            for i in range(1, refresh.MIN_PER_STATE)
        ]
        self.assertGreaterEqual(len(florida) + len(texas), refresh.MIN_STATEWIDE)
        with self.assertRaises(SystemExit) as caught:
            refresh.require_complete_download(["FL", "TX"], florida + texas)
        self.assertIn(f"TX {refresh.MIN_PER_STATE - 1}", str(caught.exception))

    def test_per_state_floor_still_requires_the_combined_minimum(self):
        # Enough for one state, not enough for the combined floor of 100.
        florida = [
            _church(name=f"FL {i}", address1=f"{i} Main Street")
            for i in range(1, refresh.MIN_PER_STATE + 1)
        ]
        self.assertGreaterEqual(len(florida), refresh.MIN_PER_STATE)
        self.assertLess(len(florida), refresh.MIN_STATEWIDE)
        with self.assertRaises(SystemExit) as caught:
            refresh.require_complete_download(["FL"], florida)
        self.assertIn(f"Parsed only {len(florida)} churches", str(caught.exception))

    def test_states_at_both_floors_are_accepted(self):
        florida = [_church(name=f"FL {i}", address1=f"{i} Main Street") for i in range(1, 101)]
        texas = [
            _church(name=f"TX {i}", state="TX", city="Houston", address1=f"{i} Texas Ave", zip="77002")
            for i in range(1, refresh.MIN_PER_STATE + 1)
        ]
        refresh.require_complete_download(["FL", "TX"], florida + texas)

    def test_main_does_not_write_when_one_requested_state_is_empty(self):
        florida = [_church(name=f"FL {i}", address1=f"{i} Main Street") for i in range(1, 201)]

        def continued(*args, **kwargs):
            raise AssertionError("refresh continued after an empty state")

        original_fetch = refresh.fetch_states
        original_geocode = refresh.geocode_addresses
        original_write = refresh.write_outputs
        refresh.fetch_states = lambda delay, states: list(florida)
        refresh.geocode_addresses = continued
        refresh.write_outputs = continued
        try:
            with self.assertRaises(SystemExit) as caught:
                refresh.main(["FL", "TX"])
        finally:
            refresh.fetch_states = original_fetch
            refresh.geocode_addresses = original_geocode
            refresh.write_outputs = original_write
        self.assertIn("TX 0", str(caught.exception))

    def test_fetch_states_single_state_does_not_sleep(self):
        sleeps: list[float] = []
        original = refresh.fetch_churches
        refresh.fetch_churches = lambda delay, state="FL": [_church(state=state)]
        try:
            refresh.fetch_states(3, ["FL"], sleep=sleeps.append)
        finally:
            refresh.fetch_churches = original
        self.assertEqual(sleeps, [])


if __name__ == "__main__":
    unittest.main()
