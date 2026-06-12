#!/usr/bin/env bash
# Paigaldab ravimus-lead-pipeline'i cron-kirjed (wp4, disaini samm 8):
#   - pipeline tick iga 30 min:  claude -p "/tick"
#   - discovery kord nädalas (E 07:00): scripts/discovery.py (wp1)
#
# Idempotentne: vanad kirjed (markeriga "# ravimus-pipeline")
# asendatakse. Kasutus:
#   scripts/install-cron.sh            # paigalda/uuenda
#   scripts/install-cron.sh --show     # näita praegusi kirjeid
#   scripts/install-cron.sh --uninstall

set -euo pipefail

MARKER="# ravimus-pipeline"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

show() { crontab -l 2>/dev/null | grep -F "$MARKER" || echo "(kirjeid pole)"; }

strip() { crontab -l 2>/dev/null | grep -vF "$MARKER" || true; }

case "${1:-install}" in
  --show) show; exit 0 ;;
  --uninstall)
    strip | crontab -
    echo "ravimus-pipeline cron-kirjed eemaldatud."
    exit 0 ;;
  install) ;;
  *) echo "tundmatu valik: $1 (kasuta --show või --uninstall)" >&2; exit 1 ;;
esac

CLAUDE_BIN="$(command -v claude || true)"
if [ -z "$CLAUDE_BIN" ]; then
  echo "VIGA: 'claude' pole PATH-is. Cron vajab täisteed." >&2
  exit 1
fi

mkdir -p "$REPO/logs"

# Croni PATH on minimaalne (/usr/bin:/bin); claude'i hook'id vajavad
# node'i jm. Anna kirjetele kaasa paigaldusaegne tööriistade PATH.
NODE_BIN="$(command -v node || true)"
CRON_PATH="$(dirname "$CLAUDE_BIN")${NODE_BIN:+:$(dirname "$NODE_BIN")}:/usr/bin:/bin"

TICK="*/30 * * * * cd $REPO && PATH=$CRON_PATH $CLAUDE_BIN -p \"/tick\" >> $REPO/logs/cron-tick.log 2>&1 $MARKER"
DISCOVERY="0 7 * * 1 cd $REPO && [ -f scripts/discovery.py ] && PATH=$CRON_PATH .venv/bin/python scripts/discovery.py >> $REPO/logs/cron-discovery.log 2>&1 $MARKER"

{ strip; echo "$TICK"; echo "$DISCOVERY"; } | crontab -

echo "Paigaldatud:"
show
