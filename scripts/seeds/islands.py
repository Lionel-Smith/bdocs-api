"""
BDOCS Seed Data - Bahamian Islands Reference

Official islands of The Bahamas with 2022 Census population data.
Used for inmate demographic analysis and realistic test data generation.

Source: Bahamas Census 2022
Reference: Department of Statistics, The Bahamas

Population weights are used to generate realistic distribution of
inmates by island of origin. ~75% from New Providence, ~12% from
Grand Bahama, remainder from Family Islands.

Note: Inmate model has `island_of_origin` field (String) that references
these island names.
"""

# Official Bahamian Islands with 2022 Census data
BAHAMAS_ISLANDS = [
    {
        "code": "NP",
        "name": "New Providence",
        "capital": "Nassau",
        "population_2022": 289746,
        "population_weight": 0.745,
        "area_sq_mi": 80,
        "is_capital_island": True,
        "region": "Central Bahamas",
        "prison_population_estimate": 1011,  # ~74.5% of 1357
        "phone_prefix": ["322", "323", "324", "325", "326", "327", "328", "341", "361", "364", "376"],
        "notes": "Capital island, location of Fox Hill Prison",
    },
    {
        "code": "GB",
        "name": "Grand Bahama",
        "capital": "Freeport",
        "population_2022": 46357,
        "population_weight": 0.119,
        "area_sq_mi": 530,
        "is_capital_island": False,
        "region": "Northern Bahamas",
        "prison_population_estimate": 161,
        "phone_prefix": ["350", "351", "352", "353", "373", "374"],
        "notes": "Second most populous island, industrial hub",
    },
    {
        "code": "AB",
        "name": "Abaco",
        "capital": "Marsh Harbour",
        "population_2022": 16330,
        "population_weight": 0.042,
        "area_sq_mi": 649,
        "is_capital_island": False,
        "region": "Northern Bahamas",
        "prison_population_estimate": 57,
        "phone_prefix": ["365", "366", "367"],
        "notes": "Third largest population, recovering from Hurricane Dorian (2019)",
    },
    {
        "code": "EL",
        "name": "Eleuthera",
        "capital": "Governor's Harbour",
        "population_2022": 8942,
        "population_weight": 0.023,
        "area_sq_mi": 187,
        "is_capital_island": False,
        "region": "Central Bahamas",
        "prison_population_estimate": 31,
        "phone_prefix": ["332", "333", "334", "335"],
        "notes": "Includes settlements: Governor's Harbour, Rock Sound, Tarpum Bay",
    },
    {
        "code": "AN",
        "name": "Andros",
        "capital": "Fresh Creek",
        "population_2022": 7792,
        "population_weight": 0.020,
        "area_sq_mi": 2300,
        "is_capital_island": False,
        "region": "Central Bahamas",
        "prison_population_estimate": 27,
        "phone_prefix": ["329", "368", "369"],
        "notes": "Largest island by area, includes North, Central, and South Andros",
    },
    {
        "code": "EX",
        "name": "Exuma",
        "capital": "George Town",
        "population_2022": 7008,
        "population_weight": 0.018,
        "area_sq_mi": 72,
        "is_capital_island": False,
        "region": "Central Bahamas",
        "prison_population_estimate": 24,
        "phone_prefix": ["336", "345", "357", "358"],
        "notes": "Includes Great Exuma, Little Exuma, and Exuma Cays",
    },
    {
        "code": "LI",
        "name": "Long Island",
        "capital": "Clarence Town",
        "population_2022": 3082,
        "population_weight": 0.008,
        "area_sq_mi": 230,
        "is_capital_island": False,
        "region": "Southern Bahamas",
        "prison_population_estimate": 11,
        "phone_prefix": ["337", "338"],
        "notes": "Known for agriculture and fishing communities",
    },
    {
        "code": "CI",
        "name": "Cat Island",
        "capital": "Arthur's Town",
        "population_2022": 1410,
        "population_weight": 0.004,
        "area_sq_mi": 150,
        "is_capital_island": False,
        "region": "Central Bahamas",
        "prison_population_estimate": 5,
        "phone_prefix": ["342", "354"],
        "notes": "Birthplace of Sir Sidney Poitier, highest elevation in Bahamas",
    },
    {
        "code": "SS",
        "name": "San Salvador",
        "capital": "Cockburn Town",
        "population_2022": 900,
        "population_weight": 0.002,
        "area_sq_mi": 63,
        "is_capital_island": False,
        "region": "Central Bahamas",
        "prison_population_estimate": 3,
        "phone_prefix": ["331"],
        "notes": "Historic landing site of Columbus, Club Med resort",
    },
    {
        "code": "IN",
        "name": "Inagua",
        "capital": "Matthew Town",
        "population_2022": 913,
        "population_weight": 0.002,
        "area_sq_mi": 599,
        "is_capital_island": False,
        "region": "Southern Bahamas",
        "prison_population_estimate": 3,
        "phone_prefix": ["339"],
        "notes": "Morton Salt operations, flamingo sanctuary",
    },
    {
        "code": "BI",
        "name": "Bimini",
        "capital": "Alice Town",
        "population_2022": 1988,
        "population_weight": 0.005,
        "area_sq_mi": 9,
        "is_capital_island": False,
        "region": "Northern Bahamas",
        "prison_population_estimate": 7,
        "phone_prefix": ["347"],
        "notes": "Closest to Florida, fishing tourism",
    },
    {
        "code": "AC",
        "name": "Acklins",
        "capital": "Spring Point",
        "population_2022": 409,
        "population_weight": 0.001,
        "area_sq_mi": 192,
        "is_capital_island": False,
        "region": "Southern Bahamas",
        "prison_population_estimate": 1,
        "phone_prefix": ["344"],
        "notes": "Part of Acklins and Crooked Island district",
    },
    {
        "code": "CR",
        "name": "Crooked Island",
        "capital": "Colonel Hill",
        "population_2022": 229,
        "population_weight": 0.001,
        "area_sq_mi": 93,
        "is_capital_island": False,
        "region": "Southern Bahamas",
        "prison_population_estimate": 1,
        "phone_prefix": ["344"],
        "notes": "Part of Acklins and Crooked Island district",
    },
    {
        "code": "MY",
        "name": "Mayaguana",
        "capital": "Abraham's Bay",
        "population_2022": 277,
        "population_weight": 0.001,
        "area_sq_mi": 110,
        "is_capital_island": False,
        "region": "Southern Bahamas",
        "prison_population_estimate": 1,
        "phone_prefix": ["339"],
        "notes": "Least developed of major islands",
    },
    {
        "code": "RI",
        "name": "Ragged Island",
        "capital": "Duncan Town",
        "population_2022": 72,
        "population_weight": 0.0002,
        "area_sq_mi": 14,
        "is_capital_island": False,
        "region": "Southern Bahamas",
        "prison_population_estimate": 0,
        "phone_prefix": ["339"],
        "notes": "Heavily impacted by Hurricane Irma (2017), rebuilding",
    },
    {
        "code": "BE",
        "name": "Berry Islands",
        "capital": "Bullocks Harbour",
        "population_2022": 807,
        "population_weight": 0.002,
        "area_sq_mi": 12,
        "is_capital_island": False,
        "region": "Northern Bahamas",
        "prison_population_estimate": 3,
        "phone_prefix": ["359"],
        "notes": "Private islands, fishing industry",
    },
    {
        "code": "HI",
        "name": "Harbour Island",
        "capital": "Dunmore Town",
        "population_2022": 1762,
        "population_weight": 0.005,
        "area_sq_mi": 3,
        "is_capital_island": False,
        "region": "Central Bahamas",
        "prison_population_estimate": 7,
        "phone_prefix": ["333"],
        "notes": "Part of Eleuthera district, pink sand beaches",
    },
    {
        "code": "SW",
        "name": "Spanish Wells",
        "capital": "Spanish Wells",
        "population_2022": 1750,
        "population_weight": 0.005,
        "area_sq_mi": 0.5,
        "is_capital_island": False,
        "region": "Central Bahamas",
        "prison_population_estimate": 7,
        "phone_prefix": ["333"],
        "notes": "Fishing community, part of Eleuthera district",
    },
    {
        "code": "RUM",
        "name": "Rum Cay",
        "capital": "Port Nelson",
        "population_2022": 99,
        "population_weight": 0.0003,
        "area_sq_mi": 30,
        "is_capital_island": False,
        "region": "Central Bahamas",
        "prison_population_estimate": 0,
        "phone_prefix": ["331"],
        "notes": "Small fishing community",
    },
    {
        "code": "FN",
        "name": "Foreign National",
        "capital": None,
        "population_2022": None,
        "population_weight": 0.050,  # ~5% of prison population
        "area_sq_mi": None,
        "is_capital_island": False,
        "region": None,
        "prison_population_estimate": 68,
        "phone_prefix": None,
        "notes": "Non-Bahamian nationals (Haiti, Jamaica, USA, etc.)",
        "is_foreign_national_category": True,
    },
]

# Normalize population weights to sum to exactly 1.0
# This ensures random.choices() works correctly for test data generation
_total_weight = sum(i["population_weight"] for i in BAHAMAS_ISLANDS)
for island in BAHAMAS_ISLANDS:
    island["population_weight"] = island["population_weight"] / _total_weight

# Summary statistics
ISLAND_STATS = {
    "total_islands": len([i for i in BAHAMAS_ISLANDS if not i.get("is_foreign_national_category")]),
    "total_population_2022": sum(i["population_2022"] for i in BAHAMAS_ISLANDS if i["population_2022"]),
    "total_prison_estimate": sum(i["prison_population_estimate"] for i in BAHAMAS_ISLANDS),
    "capital_islands": len([i for i in BAHAMAS_ISLANDS if i["is_capital_island"]]),
    "family_islands": len([i for i in BAHAMAS_ISLANDS if not i["is_capital_island"] and not i.get("is_foreign_national_category") and i["name"] != "Grand Bahama"]),
    "foreign_national_weight": next((i["population_weight"] for i in BAHAMAS_ISLANDS if i.get("is_foreign_national_category")), 0),
}


def get_island_by_code(code: str) -> dict | None:
    """Get island by code for lookups."""
    return next((i for i in BAHAMAS_ISLANDS if i["code"] == code), None)


def get_island_by_name(name: str) -> dict | None:
    """Get island by name for lookups."""
    return next((i for i in BAHAMAS_ISLANDS if i["name"].lower() == name.lower()), None)


def get_islands_by_region(region: str) -> list:
    """Get all islands in a specific region."""
    return [i for i in BAHAMAS_ISLANDS if i.get("region") == region]


def get_weighted_random_island(include_foreign: bool = True) -> str:
    """
    Get a random island name weighted by population.
    Used for generating realistic inmate test data.
    """
    import random

    islands = BAHAMAS_ISLANDS if include_foreign else [
        i for i in BAHAMAS_ISLANDS if not i.get("is_foreign_national_category")
    ]

    weights = [i["population_weight"] for i in islands]
    names = [i["name"] for i in islands]

    return random.choices(names, weights=weights, k=1)[0]
