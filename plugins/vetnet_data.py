"""Expose data/*.yml to Jinja templates as ``data.<filename>``.

Also validates the data (a bad entry fails the build with a message naming the
file and entry) and computes the "live" counts as ``data.stats``.
"""

import datetime
from pathlib import Path

import yaml
from pelican import signals

DATA_DIR = Path("data")

PERSON_ROLES = {"pi", "collaborator"}
PERSON_SECTORS = {"Academia", "Industry", "Clinical & public"}
PARTNER_TYPES = {"University", "Industry", "Clinical", "Nonprofit", "Government"}
PARTNER_GROUPS = {
    "University": "universities",
    "Industry": "industry",
    "Clinical": "clinical",
    "Nonprofit": "clinical",
    "Government": "clinical",
}
TEAM_IDS = {"mvp", "repos", "governance", "stakeholder"}
ACCESS_LEVELS = {"open", "restricted"}

REQUIRED_FILES = [
    "site",
    "nav",
    "people",
    "partners",
    "teams",
    "datasets",
    "publications",
    "join_options",
    "timeline",
    "faq",
    "member_preview",
]


class DataError(Exception):
    pass


def _fail(file, entry, message):
    raise DataError(f"data/{file}.yml: {entry}: {message}")


def _require(file, entry, item, fields):
    for field in fields:
        if item.get(field) in (None, "", []):
            _fail(file, entry, f"missing required field '{field}'")


def _label(item, index):
    name = item.get("name") or item.get("id") or item.get("label") or ""
    return f"entry {index + 1}" + (f" ({name})" if name else "")


def _last_word(name):
    return name.replace("(", "").replace(")", "").split()[-1]


def _validate_people(people):
    seen = set()
    for i, p in enumerate(people):
        where = _label(p, i)
        _require("people", where, p, ["name", "role", "title", "org", "sector"])
        if p["role"] not in PERSON_ROLES:
            _fail("people", where, f"role must be one of {sorted(PERSON_ROLES)}")
        if p["sector"] not in PERSON_SECTORS:
            _fail("people", where, f"sector must be one of {sorted(PERSON_SECTORS)}")
        if p.get("team") and p["team"] not in TEAM_IDS:
            _fail("people", where, f"team must be empty or one of {sorted(TEAM_IDS)}")
        if p["role"] == "pi" and not p.get("pi_label"):
            _fail("people", where, "PIs need 'pi_label' (Contact PI or Co-PI)")
        if p["name"] in seen:
            _fail("people", where, "duplicate name")
        seen.add(p["name"])
        p.setdefault("sort_name", _last_word(p["name"]))
        p.setdefault("author_name", p["name"])
        p.setdefault("founding_member", True)
        p.setdefault("data_donor", False)
        p.setdefault("team", None)
        p["initials"] = "".join(
            w[0] for w in p["author_name"].replace("-", " ").split()[:1] + [p["sort_name"]]
        ).upper()


def _validate_partners(partners):
    for i, p in enumerate(partners):
        where = _label(p, i)
        _require("partners", where, p, ["name", "type", "country"])
        if p["type"] not in PARTNER_TYPES:
            _fail("partners", where, f"type must be one of {sorted(PARTNER_TYPES)}")
        p["group"] = PARTNER_GROUPS[p["type"]]


def _validate_teams(teams, people):
    names = {p["name"] for p in people}
    ids = set()
    for i, t in enumerate(teams):
        where = _label(t, i)
        _require("teams", where, t, ["id", "name"])
        if t["id"] not in TEAM_IDS:
            _fail("teams", where, f"id must be one of {sorted(TEAM_IDS)}")
        ids.add(t["id"])
        t.setdefault("focus", None)
        t.setdefault("leaders", [])
        for leader in t["leaders"] or []:
            if leader not in names:
                _fail("teams", where, f"leader '{leader}' is not in people.yml")
        t["leaders"] = t["leaders"] or []
    return ids


def _validate_datasets(datasets):
    seen = set()
    for i, d in enumerate(datasets):
        where = _label(d, i)
        _require("datasets", where, d, ["id", "name", "access", "data_types", "description"])
        if d["access"] not in ACCESS_LEVELS:
            _fail("datasets", where, f"access must be one of {sorted(ACCESS_LEVELS)}")
        if d["id"] in seen:
            _fail("datasets", where, "duplicate id")
        seen.add(d["id"])
        d.setdefault("example", False)
        d.setdefault("species", [])


def _validate_publications(pubs):
    for i, p in enumerate(pubs):
        where = _label(p, i)
        _require("publications", where, p, ["id", "type", "title", "date_label"])
        p.setdefault("citations", None)


def _validate_join_options(options):
    if len(options) != 10:
        _fail("join_options", "list", f"expected 10 options, found {len(options)}")
    for i, o in enumerate(options):
        _require(
            "join_options",
            _label(o, i),
            o,
            ["id", "label", "short_label", "description", "next_step"],
        )


def _stats(data):
    people = data["people"]
    partners = data["partners"]
    datasets = [d for d in data["datasets"] if not d["example"]]
    citations = [p["citations"] for p in data["publications"] if p["citations"] is not None]
    universities = sum(1 for p in partners if p["type"] == "University")
    groups = {"universities": 0, "industry": 0, "clinical": 0}
    for p in partners:
        groups[p["group"]] += 1
    return {
        "collaborators_total": len(people),
        "collaborators": sum(1 for p in people if p["role"] == "collaborator"),
        "pis": sum(1 for p in people if p["role"] == "pi"),
        "working_groups": len(data["teams"]),
        "organizations": len(partners),
        "universities": universities,
        "industry_other": len(partners) - universities,
        "partner_groups": groups,
        "datasets": len(datasets),
        "datasets_open": sum(1 for d in datasets if d["access"] == "open"),
        "datasets_restricted": sum(1 for d in datasets if d["access"] == "restricted"),
        "publications": len(data["publications"]),
        "citations": sum(citations) if citations else None,
        "donors": sum(1 for p in people if p["data_donor"]),
    }


def _derive(data):
    people = data["people"]
    pis = [p for p in people if p["role"] == "pi"]
    collaborators = sorted(
        (p for p in people if p["role"] == "collaborator"),
        key=lambda p: p["sort_name"].lower(),
    )
    data["pis"] = pis
    data["collaborators"] = collaborators
    data["authors"] = [p["author_name"] for p in pis + collaborators]
    species = sorted({s for d in data["datasets"] for s in d["species"]})
    types = sorted({t for d in data["datasets"] for t in d["data_types"]})
    data["dataset_filters"] = {"species": species, "types": types}


def load_data():
    data = {}
    for name in REQUIRED_FILES:
        path = DATA_DIR / f"{name}.yml"
        if not path.exists():
            raise DataError(f"{path}: file is missing")
        try:
            data[name] = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise DataError(f"{path}: invalid YAML: {exc}") from exc
        if data[name] is None:
            raise DataError(f"{path}: file is empty")

    _validate_people(data["people"])
    _validate_partners(data["partners"])
    _validate_teams(data["teams"], data["people"])
    _validate_datasets(data["datasets"])
    _validate_publications(data["publications"])
    _validate_join_options(data["join_options"])
    _derive(data)
    data["stats"] = _stats(data)
    data["build_year"] = datetime.date.today().year
    return data


def _on_init(generator):
    generator.context["data"] = load_data()


def register():
    signals.generator_init.connect(_on_init)
