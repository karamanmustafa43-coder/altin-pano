"""Her yayindan once calistirilir: index.html icindeki SURUM damgasini ve surum.json'u tazeler.
Uygulama acilista surum.json'u onbelleksiz okur; damga degismisse kendini yeniden yukler.

    python surum_bas.py
"""
import json, os, re, sys
from datetime import datetime, timedelta, timezone

KLASOR = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")
damga = datetime.now(timezone(timedelta(hours=3))).strftime("%d.%m %H:%M")

yol = os.path.join(KLASOR, "index.html")
s = open(yol, encoding="utf-8").read()
yeni, n = re.subn(r'const SURUM = "[^"]*";', f'const SURUM = "{damga}";', s)
if not n:
    raise SystemExit("index.html icinde SURUM bulunamadi")
open(yol, "w", encoding="utf-8").write(yeni)

with open(os.path.join(KLASOR, "surum.json"), "w", encoding="utf-8") as f:
    json.dump({"surum": damga}, f, ensure_ascii=False)
print("surum:", damga)
