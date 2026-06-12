# LV Vet Registry Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministic discovery: load both Latvian vet registries (LVB certified-vets HTML table + PVD practitioners XLSX), merge into `cache/registry.csv`, and create a Pipedrive person + deal in stage Discovered for every e-mail-bearing record, deduplicated by `registry_id`, all writes DRY_RUN-guarded.

**Architecture:** Pure, unit-tested parsing/merge/planning logic lives in `mcp/lib/` (mirrors the existing `setup_plan.py` pattern); `mcp/scripts/registry.py` and `mcp/scripts/discovery.py` are thin orchestrators that do network I/O and printing. Discovery writes go through the existing `lib/pipedrive_client` + `lib/dryrun`; deal metadata goes into the single JSON state field via `lib/deal_state`.

**Tech Stack:** Python 3.11+, stdlib `html.parser`/`urllib`/`csv`, openpyxl (PVD XLSX), pytest.

**Spec:** `docs/superpowers/specs/2026-06-12-lv-vet-registry-discovery-design.md`

---

## Source facts (verified 2026-06-12)

- **LVB** (primary, has e-mails): `https://lvb.lv/veterinarmedicinas-prakses-saraksts/` — server-rendered TablePress table `id="tablepress-3"`, 9 columns: `ID | Uzvārds | Vārds | Sertifikāta Nr. | Piešķiršanas datums | Derīguma termiņš | Protokola Nr. | Prakses veids | E-pasts`. 957 rows, 664 with e-mail. Dates look like `30.03.2022.`. Cert no. like `V-1058-27` = our `registry_id`.
- **PVD** (enrichment, NO e-mails): data.gov.lv XLSX
  `https://data.gov.lv/dati/dataset/d9a75cce-fb62-4f61-b516-9ddca718927c/resource/9b7d169d-1814-41f2-9b66-89d6b6b4a412/download/veterinrmedicnisko-pakalpojumu-sniedzji.xlsx`
  — stale (2024-03) but fine for clinic/address enrichment. Header row ~4; relevant headers contain: `Vārds, uzvārds` (name, "First Last" order), `Juridiskā persona` (clinic), `prakses vieta` (address), `veids` (practice type). Contains region section rows that must be skipped.
- Join: name only (ID systems differ). Exact normalized match, unique-or-nothing.

## File structure

```
mcp/
  lib/
    lvb_parser.py        # parse LVB HTML -> list[dict]            (new)
    pvd_parser.py        # parse PVD XLSX -> list[dict]            (new)
    registry_merge.py    # name-join + registry.csv read/write     (new)
    discovery_plan.py    # email filter + dedup -> creation plan   (new)
    constants.py         # add state keys                          (modify)
  scripts/
    registry.py          # fetch both registries -> cache/registry.csv  (new)
    discovery.py         # CSV -> Pipedrive persons+deals (DRY_RUN)     (new)
  tests/
    test_lvb_parser.py   (new)
    test_pvd_parser.py   (new)
    test_registry_merge.py (new)
    test_discovery_plan.py (new)
  requirements.txt       # + openpyxl                              (modify)
```

All commands below run from `mcp/`: `cd mcp` first. Tests: `python -m pytest tests/ -v`.

---

### Task 1: Dependency + state keys

**Files:**
- Modify: `mcp/requirements.txt`
- Modify: `mcp/lib/constants.py:18-23`

- [ ] **Step 1: Add openpyxl to requirements and install**

`mcp/requirements.txt` becomes:

```
fastmcp<3
uvicorn
starlette
pytest
openpyxl
```

Run: `pip install openpyxl`
Expected: `Successfully installed openpyxl-...` (or already satisfied).

- [ ] **Step 2: Add the three new documented state keys**

In `mcp/lib/constants.py`, change `STATE_KEYS` to:

```python
STATE_KEYS = [
    "registry_id", "email", "clinic", "specialization", "network",
    "decision_style", "score", "ab_variant", "personal_link",
    "discount_code", "sample_claimed_at", "emails_sent",
    "last_contact_at", "lost_reason",
    "valid_until", "practice_scope", "source",
]
```

- [ ] **Step 3: Run the existing test suite to confirm nothing broke**

Run: `python -m pytest tests/ -v`
Expected: all existing tests PASS.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt lib/constants.py
git commit -m "chore(mcp): add openpyxl dep and discovery state keys"
```

---

### Task 2: LVB HTML parser

**Files:**
- Create: `mcp/lib/lvb_parser.py`
- Test: `mcp/tests/test_lvb_parser.py`

- [ ] **Step 1: Write the failing tests**

`mcp/tests/test_lvb_parser.py`:

```python
from lib.lvb_parser import parse_lvb_html

FIXTURE = """
<html><body>
<p>muu sisu</p>
<table id="tablepress-3"><thead>
<tr><th>ID</th><th>Uzvārds</th><th>Vārds</th><th>Sertifikāta Nr.</th>
<th>Piešķiršanas datums</th><th>Derīguma termiņš</th><th>Protokola Nr.</th>
<th>Prakses veids</th><th>E-pasts</th></tr></thead><tbody>
<tr><td>4</td><td>Gabrišs</td><td>Gunārs</td><td>V-1058-27</td>
<td>30.03.2022.</td><td>04.07.2027.</td><td>3</td>
<td>lauksaimn. dzīvn., mājas dzīvn., aptiekā</td><td>gabrisi@inbox.lv</td></tr>
<tr><td>5</td><td>Zemnieks</td><td>Ilmārs</td><td>V-0001-27</td>
<td>30.03.2022.</td><td>04.07.2027.</td><td>3</td>
<td>mājas dzīvn.</td><td></td></tr>
<tr><td>6</td><td>Bērziņa</td><td>Līga</td><td></td>
<td></td><td></td><td></td><td></td><td>x@y.lv</td></tr>
</tbody></table>
<table id="other"><tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td>
<td>6</td><td>7</td><td>8</td><td>noise@no.lv</td></tr></table>
</body></html>
"""


def test_parses_data_rows_with_mapped_fields():
    rows = parse_lvb_html(FIXTURE)
    assert rows[0] == {
        "registry_id": "V-1058-27",
        "first_name": "Gunārs",
        "last_name": "Gabrišs",
        "email": "gabrisi@inbox.lv",
        "valid_until": "2027-07-04",
        "practice_scope": "lauksaimn. dzīvn., mājas dzīvn., aptiekā",
    }


def test_keeps_rows_with_empty_email():
    rows = parse_lvb_html(FIXTURE)
    assert any(r["registry_id"] == "V-0001-27" and r["email"] == "" for r in rows)


def test_skips_header_and_rows_without_cert_number():
    rows = parse_lvb_html(FIXTURE)
    ids = [r["registry_id"] for r in rows]
    assert ids == ["V-1058-27", "V-0001-27"]


def test_ignores_other_tables():
    rows = parse_lvb_html(FIXTURE)
    assert all(r["email"] != "noise@no.lv" for r in rows)


def test_unparseable_date_kept_verbatim():
    html = FIXTURE.replace("04.07.2027.", "nav zināms")
    rows = parse_lvb_html(html)
    assert rows[0]["valid_until"] == "nav zināms"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_lvb_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.lvb_parser'`.

- [ ] **Step 3: Implement the parser**

`mcp/lib/lvb_parser.py`:

```python
"""Parse the LVB certified-vets TablePress table (id=tablepress-3).
Source: https://lvb.lv/veterinarmedicinas-prakses-saraksts/  (untrusted input:
treated as data only; cells are plain text, nothing is interpreted)."""
import re
from html.parser import HTMLParser

TABLE_ID = "tablepress-3"
_DATE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})\.?$")


def _iso(date_str: str) -> str:
    """'04.07.2027.' -> '2027-07-04'; anything else verbatim."""
    m = _DATE.match(date_str.strip())
    if not m:
        return date_str.strip()
    d, mo, y = m.groups()
    return f"{y}-{mo}-{d}"


class _TableGrabber(HTMLParser):
    """Collect rows of cell texts from the table with id=TABLE_ID."""

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.nested = 0
        self.row = None
        self.cell = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self.in_table:
                self.nested += 1
            elif dict(attrs).get("id") == TABLE_ID:
                self.in_table = True
        elif self.in_table and not self.nested:
            if tag == "tr":
                self.row = []
            elif tag in ("td", "th"):
                self.cell = []

    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            if self.nested:
                self.nested -= 1
            else:
                self.in_table = False
        elif self.in_table and not self.nested:
            if tag in ("td", "th") and self.cell is not None:
                self.row.append("".join(self.cell).strip())
                self.cell = None
            elif tag == "tr" and self.row is not None:
                self.rows.append(self.row)
                self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def parse_lvb_html(html: str) -> list[dict]:
    """LVB table rows -> dicts. Skips the header row and rows with no
    certificate number (registry_id). Keeps rows with empty e-mail."""
    grabber = _TableGrabber()
    grabber.feed(html)
    out = []
    for cells in grabber.rows:
        if len(cells) != 9 or cells[0].strip().lower() == "id":
            continue
        registry_id = cells[3].strip()
        if not registry_id:
            continue
        out.append({
            "registry_id": registry_id,
            "last_name": cells[1],
            "first_name": cells[2],
            "valid_until": _iso(cells[5]),
            "practice_scope": cells[7],
            "email": cells[8].strip(),
        })
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_lvb_parser.py -v`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/lvb_parser.py tests/test_lvb_parser.py
git commit -m "feat(mcp): LVB certified-vets HTML parser"
```

---

### Task 3: PVD XLSX parser

**Files:**
- Create: `mcp/lib/pvd_parser.py`
- Test: `mcp/tests/test_pvd_parser.py`

- [ ] **Step 1: Write the failing tests** (fixture XLSX built with openpyxl in tmp_path)

`mcp/tests/test_pvd_parser.py`:

```python
import openpyxl
import pytest
from lib.pvd_parser import parse_pvd_xlsx


@pytest.fixture
def xlsx(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Veterinārmedicīnisko pakalpojumu sniedzēji"])
    ws.append([])
    ws.append(["aktualizēts: 11.03.2024"])
    ws.append(["N.p.k.", "Vārds, uzvārds", "Sertifikāta numurs (derīgs līdz)",
               "Numurs PVD reģistrā", "Juridiskā persona, vienotais reģistrācijas numurs",
               "Veterinārmedicīniskās prakses vieta", "Prakses vietas veids"])
    ws.append(["Bauskas novads"])  # section row
    ws.append([1, "Līga Truntika", "V-0010-27", "059694",
               "Līga-vet, SIA, VRN 43603061144",
               "Zaļā iela 11 k-7, Bauska, Bauskas novads", "ambulatora"])
    ws.append([2, "Gunārs Gabrišs", None, "042678", None,
               "Brīvības 1, Rīga", "kabinets"])
    path = tmp_path / "pvd.xlsx"
    wb.save(path)
    return path


def test_parses_records_after_header(xlsx):
    recs = parse_pvd_xlsx(xlsx)
    assert recs[0] == {
        "name": "Līga Truntika",
        "clinic": "Līga-vet, SIA, VRN 43603061144",
        "address": "Zaļā iela 11 k-7, Bauska, Bauskas novads",
        "practice_type": "ambulatora",
    }
    assert len(recs) == 2


def test_skips_section_rows_and_preamble(xlsx):
    names = [r["name"] for r in parse_pvd_xlsx(xlsx)]
    assert "Bauskas novads" not in names
    assert "aktualizēts: 11.03.2024" not in names


def test_missing_clinic_becomes_empty_string(xlsx):
    recs = parse_pvd_xlsx(xlsx)
    assert recs[1]["clinic"] == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pvd_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.pvd_parser'`.

- [ ] **Step 3: Implement the parser**

`mcp/lib/pvd_parser.py`:

```python
"""Parse the PVD practitioners XLSX (data.gov.lv open data, CC0).
Header row is found by its column titles; region section rows (only a
region name, no address/clinic) are skipped. Untrusted input: data only."""
import openpyxl

_HDR_NAME = "uzvārds"          # in "Vārds, uzvārds"
_HDR_CLINIC = "juridiskā"      # in "Juridiskā persona, ..."
_HDR_ADDRESS = "prakses vieta" # in "Veterinārmedicīniskās prakses vieta"
_HDR_TYPE = "veids"            # in "Prakses vietas veids"


def _header_index(cells: list[str]) -> dict | None:
    idx = {}
    for i, c in enumerate(cells):
        low = c.lower()
        if _HDR_NAME in low:
            idx["name"] = i
        elif _HDR_CLINIC in low:
            idx["clinic"] = i
        elif _HDR_ADDRESS in low and _HDR_TYPE not in low:
            idx["address"] = i
        elif _HDR_TYPE in low:
            idx["practice_type"] = i
    return idx if {"name", "address"} <= idx.keys() else None


def _cell(cells: list[str], idx: dict, key: str) -> str:
    i = idx.get(key)
    return cells[i] if i is not None and i < len(cells) else ""


def parse_pvd_xlsx(path) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = []
    try:
        for ws in wb.worksheets:
            idx = None
            for row in ws.iter_rows(values_only=True):
                cells = ["" if v is None else str(v).strip() for v in row]
                if idx is None:
                    idx = _header_index(cells)
                    continue
                name = _cell(cells, idx, "name")
                clinic = _cell(cells, idx, "clinic")
                address = _cell(cells, idx, "address")
                if not name or (not clinic and not address):
                    continue  # blank or region section row
                out.append({"name": name, "clinic": clinic, "address": address,
                            "practice_type": _cell(cells, idx, "practice_type")})
    finally:
        wb.close()
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_pvd_parser.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/pvd_parser.py tests/test_pvd_parser.py
git commit -m "feat(mcp): PVD practitioners XLSX parser"
```

---

### Task 4: Merge + registry.csv read/write

**Files:**
- Create: `mcp/lib/registry_merge.py`
- Test: `mcp/tests/test_registry_merge.py`

- [ ] **Step 1: Write the failing tests**

`mcp/tests/test_registry_merge.py`:

```python
from lib.registry_merge import (merge_registries, write_registry_csv,
                                read_registry_csv, REGISTRY_COLUMNS)

LVB = [
    {"registry_id": "V-1", "first_name": "Līga", "last_name": "Truntika",
     "email": "l@t.lv", "valid_until": "2027-01-01", "practice_scope": "mājas dzīvn."},
    {"registry_id": "V-2", "first_name": "Jānis", "last_name": "Ozols",
     "email": "", "valid_until": "2026-01-01", "practice_scope": "zirgi"},
    {"registry_id": "V-3", "first_name": "Anna", "last_name": "Liepa",
     "email": "a@l.lv", "valid_until": "2025-01-01", "practice_scope": ""},
]
PVD = [
    {"name": "Līga  Truntika", "clinic": "Līga-vet, SIA", "address": "Bauska",
     "practice_type": "ambulatora"},
    {"name": "Anna Liepa", "clinic": "K1", "address": "Rīga", "practice_type": "kabinets"},
    {"name": "anna liepa", "clinic": "K2", "address": "Cēsis", "practice_type": "kabinets"},
]


def test_unique_name_match_brings_clinic_and_address():
    rows = merge_registries(LVB, PVD)
    assert rows[0]["clinic"] == "Līga-vet, SIA"
    assert rows[0]["address"] == "Bauska"
    assert rows[0]["pvd_match"] == "unique"


def test_no_match_leaves_blank():
    rows = merge_registries(LVB, PVD)
    assert rows[1]["clinic"] == "" and rows[1]["pvd_match"] == "none"


def test_ambiguous_match_leaves_blank():
    rows = merge_registries(LVB, PVD)
    assert rows[2]["clinic"] == "" and rows[2]["pvd_match"] == "ambiguous"


def test_lvb_order_preserved():
    assert [r["registry_id"] for r in merge_registries(LVB, PVD)] == ["V-1", "V-2", "V-3"]


def test_csv_roundtrip_utf8(tmp_path):
    rows = merge_registries(LVB, PVD)
    path = tmp_path / "registry.csv"
    write_registry_csv(rows, path)
    back = read_registry_csv(path)
    assert back[0]["first_name"] == "Līga"
    assert list(back[0].keys()) == REGISTRY_COLUMNS
    assert len(back) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_registry_merge.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.registry_merge'`.

- [ ] **Step 3: Implement merge + CSV io**

`mcp/lib/registry_merge.py`:

```python
"""Join LVB rows (primary, has e-mails) with PVD records (clinic/address) by
exact normalized full name; unique match or nothing (spec decision 3).
Reads/writes cache/registry.csv with a fixed column order."""
import csv
from pathlib import Path

REGISTRY_COLUMNS = ["registry_id", "first_name", "last_name", "email",
                    "valid_until", "practice_scope", "clinic", "address",
                    "pvd_match"]


def normalize_name(name: str) -> str:
    """Lowercase, collapse whitespace. Diacritics preserved."""
    return " ".join(name.split()).lower()


def merge_registries(lvb_rows: list[dict], pvd_records: list[dict]) -> list[dict]:
    by_name: dict[str, list[dict]] = {}
    for rec in pvd_records:
        by_name.setdefault(normalize_name(rec["name"]), []).append(rec)
    out = []
    for vet in lvb_rows:
        key = normalize_name(f"{vet['first_name']} {vet['last_name']}")
        matches = by_name.get(key, [])
        row = {**vet, "clinic": "", "address": "",
               "pvd_match": "none" if not matches else "ambiguous"}
        if len(matches) == 1:
            row.update(clinic=matches[0]["clinic"], address=matches[0]["address"],
                       pvd_match="unique")
        out.append({k: row.get(k, "") for k in REGISTRY_COLUMNS})
    return out


def write_registry_csv(rows: list[dict], path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_registry_csv(path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_registry_merge.py -v`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/registry_merge.py tests/test_registry_merge.py
git commit -m "feat(mcp): LVB+PVD name merge and registry.csv io"
```

---

### Task 5: Discovery plan (filter + dedup, pure)

**Files:**
- Create: `mcp/lib/discovery_plan.py`
- Test: `mcp/tests/test_discovery_plan.py`

- [ ] **Step 1: Write the failing tests**

`mcp/tests/test_discovery_plan.py`:

```python
from lib.discovery_plan import is_valid_email, plan_discovery


def _row(rid, email):
    return {"registry_id": rid, "first_name": "A", "last_name": "B", "email": email}


def test_email_validation():
    assert is_valid_email("a.b@example.lv")
    assert not is_valid_email("")
    assert not is_valid_email("nav e-pasta")
    assert not is_valid_email("a@b")          # no dot in domain
    assert not is_valid_email("a b@c.lv")     # whitespace


def test_plan_filters_and_counts():
    rows = [_row("V-1", "a@b.lv"), _row("V-2", ""), _row("V-3", "bad"),
            _row("V-4", "d@e.lv"), _row("V-5", "f@g.lv")]
    plan = plan_discovery(rows, existing_ids={"V-4"})
    assert [r["registry_id"] for r in plan["to_create"]] == ["V-1", "V-5"]
    assert plan["skipped"] == {"existing": 1, "no_email": 1, "bad_email": 1}


def test_duplicate_registry_id_within_csv_skipped():
    rows = [_row("V-1", "a@b.lv"), _row("V-1", "x@y.lv")]
    plan = plan_discovery(rows, existing_ids=set())
    assert len(plan["to_create"]) == 1
    assert plan["skipped"]["existing"] == 1


def test_expired_certificates_are_still_included():
    rows = [{**_row("V-1", "a@b.lv"), "valid_until": "2020-01-01"}]
    plan = plan_discovery(rows, existing_ids=set())
    assert len(plan["to_create"]) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_discovery_plan.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.discovery_plan'`.

- [ ] **Step 3: Implement**

`mcp/lib/discovery_plan.py`:

```python
"""Decide which registry rows become new deals: e-mail present and
syntactically valid, registry_id not seen before (in Pipedrive or earlier in
the same CSV). Expired certificates are included by design (user decision
2026-06-12); qualification scores them later."""
import re

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL.match(email or ""))


def plan_discovery(rows: list[dict], existing_ids: set[str]) -> dict:
    to_create = []
    skipped = {"existing": 0, "no_email": 0, "bad_email": 0}
    seen = set(existing_ids)
    for row in rows:
        email = (row.get("email") or "").strip()
        rid = (row.get("registry_id") or "").strip()
        if not email:
            skipped["no_email"] += 1
        elif not is_valid_email(email):
            skipped["bad_email"] += 1
        elif rid in seen:
            skipped["existing"] += 1
        else:
            seen.add(rid)
            to_create.append(row)
    return {"to_create": to_create, "skipped": skipped}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discovery_plan.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/discovery_plan.py tests/test_discovery_plan.py
git commit -m "feat(mcp): discovery plan — email filter and registry_id dedup"
```

---

### Task 6: scripts/registry.py (fetch + cache + CSV)

**Files:**
- Create: `mcp/scripts/registry.py`

Network orchestration only (logic already unit-tested); verified by a real run — both fetches are plain GETs of public data.

- [ ] **Step 1: Implement the script**

`mcp/scripts/registry.py`:

```python
"""Load both Latvian vet registries into cache/registry.csv.

Usage:
    cd mcp && python -m scripts.registry

LVB (certified vets, has e-mails) is required: failure aborts (exit 1).
PVD (clinic/address enrichment) is optional: failure warns and continues.
Raw downloads are cached (cache/lvb.html, cache/pvd.xlsx) for debuggability.
"""
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.lvb_parser import parse_lvb_html
from lib.pvd_parser import parse_pvd_xlsx
from lib.registry_merge import merge_registries, write_registry_csv

LVB_URL = "https://lvb.lv/veterinarmedicinas-prakses-saraksts/"
PVD_URL = ("https://data.gov.lv/dati/dataset/d9a75cce-fb62-4f61-b516-9ddca718927c/"
           "resource/9b7d169d-1814-41f2-9b66-89d6b6b4a412/download/"
           "veterinrmedicnisko-pakalpojumu-sniedzji.xlsx")


def _cache_dir() -> Path:
    return Path(os.getenv("CACHE_DIR", "./cache"))


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ravimus-discovery/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> int:
    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)

    try:
        lvb_raw = _fetch(LVB_URL)
    except Exception as e:
        print(f"ERROR: LVB fetch failed ({e}); aborting, nothing written")
        return 1
    (cache / "lvb.html").write_bytes(lvb_raw)
    lvb_rows = parse_lvb_html(lvb_raw.decode("utf-8", errors="replace"))
    if not lvb_rows:
        print("ERROR: LVB parse produced 0 rows (page layout changed?); aborting")
        return 1

    pvd_records = []
    try:
        pvd_raw = _fetch(PVD_URL)
        (cache / "pvd.xlsx").write_bytes(pvd_raw)
        pvd_records = parse_pvd_xlsx(cache / "pvd.xlsx")
    except Exception as e:
        print(f"WARNING: PVD fetch/parse failed ({e}); continuing without clinic data")

    rows = merge_registries(lvb_rows, pvd_records)
    out = cache / "registry.csv"
    write_registry_csv(rows, out)

    with_email = sum(1 for r in rows if r["email"])
    matched = sum(1 for r in rows if r["pvd_match"] == "unique")
    print(f"wrote {out}: {len(rows)} vets, {with_email} with e-mail, "
          f"{matched} with PVD clinic match (pvd records: {len(pvd_records)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run it for real (read-only GETs)**

Run: `cd mcp && python -m scripts.registry`
Expected: `wrote cache/registry.csv: ~957 vets, ~664 with e-mail, ...`
Sanity-check the CSV: `python -c "from lib.registry_merge import read_registry_csv; r=read_registry_csv('cache/registry.csv'); print(len(r), r[0])"` — Latvian diacritics intact.

- [ ] **Step 3: Ensure cache/ is gitignored**

Check repo `.gitignore` covers `cache/` (registry data contains personal e-mails; do not commit). If not covered, add `cache/` to `.gitignore`.

- [ ] **Step 4: Commit**

```bash
git add scripts/registry.py
git commit -m "feat(mcp): registry.py — load LVB+PVD into cache/registry.csv"
```

---

### Task 7: scripts/discovery.py (persons + deals, DRY_RUN-guarded)

**Files:**
- Create: `mcp/scripts/discovery.py`

- [ ] **Step 1: Implement the script**

`mcp/scripts/discovery.py`:

```python
"""Create a Pipedrive person + deal (stage Discovered) for every new
e-mail-bearing registry row. Dedup by registry_id against ALL existing deals
(including Lost: opted-out vets are never re-created).

Usage:
    cd mcp && python -m scripts.discovery          # DRY_RUN=1 by default
    DRY_RUN=0 python -m scripts.discovery          # live

Re-running is idempotent: existing registry_ids are skipped.
Writes a summary to logs/discovery-YYYY-MM-DD.log.
"""
import os
import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import pipedrive_client as pc
from lib import deal_state
from lib.discovery_plan import plan_discovery
from lib.dryrun import is_dry_run, dry_log
from lib.field_map import resolve_stage_id
from lib.registry_merge import read_registry_csv


def _existing_registry_ids(dry: bool) -> set[str]:
    """registry_id of every non-deleted deal (any stage/status)."""
    ids: set[str] = set()
    start = 0
    while True:
        res = pc.get("deals", {"start": start, "limit": 500,
                               "status": "all_not_deleted"})
        if res.get("error"):
            if dry:
                print(f"WARNING: cannot list deals ({res['error']}); "
                      "assuming none exist (DRY_RUN)")
                return ids
            raise SystemExit(f"ERROR: cannot list deals: {res['error']}")
        for deal in res.get("data") or []:
            rid = deal_state.read_state(deal).get("registry_id")
            if rid:
                ids.add(str(rid))
        pagination = (res.get("additional_data") or {}).get("pagination") or {}
        if not pagination.get("more_items_in_collection"):
            return ids
        start = pagination.get("next_start", start + 500)


def _state_for(row: dict) -> dict:
    return {
        "registry_id": row["registry_id"],
        "email": row["email"],
        "clinic": row.get("clinic", ""),
        "valid_until": row.get("valid_until", ""),
        "practice_scope": row.get("practice_scope", ""),
        "source": "lvb+pvd" if row.get("pvd_match") == "unique" else "lvb",
    }


def _create(row: dict, stage_id: int | None, dry: bool) -> bool:
    name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
    person_body = {"name": name,
                   "email": [{"value": row["email"], "primary": True}]}
    state = _state_for(row)
    if dry:
        dry_log("discovery_create", person=person_body, deal_title=name,
                stage="Discovered", state=state)
        return True
    pres = pc.post("persons", person_body)
    person_id = (pres.get("data") or {}).get("id")
    if person_id is None:
        print(f"  FAIL person {row['registry_id']}: {pres.get('error', pres)}")
        return False
    body = {"person_id": person_id, "title": name, "stage_id": stage_id}
    body.update(deal_state.encode_state(state))
    dres = pc.post("deals", body)
    if (dres.get("data") or {}).get("id") is None:
        print(f"  FAIL deal {row['registry_id']}: {dres.get('error', dres)}")
        return False
    return True


def main() -> int:
    dry = is_dry_run()
    csv_path = Path(os.getenv("CACHE_DIR", "./cache")) / "registry.csv"
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found; run scripts.registry first")
        return 1
    rows = read_registry_csv(csv_path)

    stage_id = resolve_stage_id("Discovered")
    if stage_id is None and not dry:
        print("ERROR: stage 'Discovered' unknown; run scripts.pipedrive_setup first")
        return 1

    existing = _existing_registry_ids(dry)
    plan = plan_discovery(rows, existing)
    created = failed = 0
    for row in plan["to_create"]:
        if _create(row, stage_id, dry):
            created += 1
        else:
            failed += 1

    skipped = plan["skipped"]
    summary = (f"DRY_RUN={dry} registry_rows={len(rows)} "
               f"existing_in_pipedrive={len(existing)} created={created} "
               f"failed={failed} skipped_existing={skipped['existing']} "
               f"no_email={skipped['no_email']} bad_email={skipped['bad_email']}")
    print(summary)

    logs = Path(os.getenv("LOGS_DIR", "./logs"))
    logs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    with (logs / f"discovery-{stamp}.log").open("a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {summary}\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the full suite once more**

Run: `python -m pytest tests/ -v`
Expected: all PASS (new modules import cleanly; scripts not imported by tests).

- [ ] **Step 3: Ensure logs/ is gitignored**

Check repo `.gitignore` covers `logs/`; add if missing.

- [ ] **Step 4: Commit**

```bash
git add scripts/discovery.py
git commit -m "feat(mcp): discovery.py — persons+deals from registry, DRY_RUN-guarded"
```

---

### Task 8: End-to-end DRY_RUN verification (WP1 "Valmis, kui" #2)

**Files:** none (verification only)

- [ ] **Step 1: Fresh registry load**

Run: `cd mcp && python -m scripts.registry`
Expected: `wrote cache/registry.csv: ~957 vets, ~664 with e-mail, ...`

- [ ] **Step 2: Discovery in DRY_RUN**

Run: `python -m scripts.discovery` (DRY_RUN defaults to ON)
Expected: summary line with `DRY_RUN=True`, `created≈664`, `failed=0`,
`no_email≈293`, `bad_email` small, no duplicate creations
(`created + skipped_existing + no_email + bad_email == registry_rows`).

- [ ] **Step 3: Idempotence signal**

Run discovery again: counts identical (DRY_RUN persists nothing, so the dedup
proof against Pipedrive itself lands in the live smoke-test later; within-CSV
dedup is already unit-tested).

- [ ] **Step 4: Check the summary log**

Run: `ls logs/` and view `logs/discovery-<today>.log` — two summary lines.

- [ ] **Step 5: Commit any leftovers and report**

```bash
git status   # cache/ and logs/ must NOT appear as trackable
```

Report the real counts (vets, e-mails, PVD matches, created) back to the user.
