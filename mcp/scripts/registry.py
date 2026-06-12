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
