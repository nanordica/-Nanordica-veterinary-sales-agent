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
