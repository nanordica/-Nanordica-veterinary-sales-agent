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
