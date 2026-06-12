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
