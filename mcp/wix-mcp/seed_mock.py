"""Külva wix-mcp mock-olekusse testtellimusi (sales-detectori
integratsioonitestiks, vt docs/work-packages/wp4-sales-detection-launch/
sales-detector-integration-test.md).

    # päris ost (total > 0), seotakse ostja e-posti kaudu:
    .venv/bin/python mcp/wix-mcp/seed_mock.py purchase ostja@example.lv

    # näidise lunastus (total 0), seotakse kupongikoodi kaudu;
    # kupong peab olema enne loodud create_coupon'iga:
    .venv/bin/python mcp/wix-mcp/seed_mock.py sample ostja@example.lv RVET-42-AB12

    # olek nulli (NB: kustutab ka kupongid):
    .venv/bin/python mcp/wix-mcp/seed_mock.py reset
"""

import sys
from datetime import datetime, timezone

# Olekufaili asukoht ja vorming elavad AINULT serveris; siit tuleb ka
# WIX_MOCK_FILE override ja .env laadimine.
from server import MOCK_STATE, _read_mock, _write_mock


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("purchase", "sample", "reset"):
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    cmd = sys.argv[1]

    if cmd == "reset":
        _write_mock({"orders": [], "coupons": {}})
        print(f"mock-olek nullitud: {MOCK_STATE}")
        return

    email = sys.argv[2]
    state = _read_mock()
    n = len(state["orders"]) + 1
    order = {
        "order_id": f"mock-{n}",
        "number": str(10000 + n),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "buyer_email": email,
        "coupon_code": "",
        "total": "49.00",
        "currency": "EUR",
        "line_items": ["RavimusVET haavaside"],
    }

    if cmd == "sample":
        if len(sys.argv) < 4:
            print("sample vajab kupongikoodi", file=sys.stderr)
            sys.exit(2)
        code = sys.argv[3]
        coupon = state["coupons"].get(code)
        if not coupon:
            print(f"VIGA: kupongi {code} pole mock-olekus. Loo see enne "
                  "wix-mcp create_coupon tööriistaga (mock-režiim kirjutab "
                  "mock-olekusse).", file=sys.stderr)
            sys.exit(1)
        coupon["usage_count"] = int(coupon.get("usage_count", 0)) + 1
        order["coupon_code"] = code
        order["total"] = "0"
        order["line_items"] = ["RavimusVET näidis"]

    state["orders"].append(order)
    _write_mock(state)
    print(f"lisatud {cmd}-tellimus nr {order['number']} ({email}) -> "
          f"{MOCK_STATE}")


if __name__ == "__main__":
    main()
