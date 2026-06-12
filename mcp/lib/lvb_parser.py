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
