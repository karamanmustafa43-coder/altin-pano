"""IAR Platform'dan guncel gram altin fiyatini alir, fiyat.json ve fiyat_gecmisi.json'u gunceller.

GitHub Actions icinde calisir. Erisim anahtari depoda TUTULMAZ: IAR'in kendi sitesinin
herkese acik on yuz dosyasindan calisma aninda okunur (siteyi acan herkesin tarayicisinin yaptigi is).
"""
import json, os, re, ssl, sys, urllib.request
from datetime import datetime, timedelta, timezone

TR = timezone(timedelta(hours=3))
SITE = "https://www.iarplatform.com/"
API = "https://tstapi.iarplatform.com/api/ForInvest/GetAll?groupId=1"
KLASOR = os.path.dirname(os.path.abspath(__file__))
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE  # sitenin sertifika zinciri eksik

sys.stdout.reconfigure(encoding="utf-8")


def cek(url, basliklar=None):
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", **(basliklar or {})})
    with urllib.request.urlopen(r, context=CTX, timeout=60) as y:
        return y.read().decode("utf-8", "ignore")


def anahtar():
    """Sitenin on yuz dosyasindaki acik X-Api-Key degerini bulur."""
    ana = cek(SITE)
    for yol in re.findall(r'"(/assets/[^"]+\.js)"', ana) + re.findall(r'src="(/assets/[^"]+\.js)"', ana):
        try:
            js = cek(SITE.rstrip("/") + yol)
        except Exception:
            continue
        for alt in re.findall(r'"\./([^"]+\.js)"', js):
            try:
                js += cek(SITE.rstrip("/") + "/assets/" + alt)
            except Exception:
                pass
        m = re.search(r'X-Api-Key"?\]?\s*=\s*([A-Za-z_$][\w$]*)', js)
        if m:
            d = re.search(r'\b' + re.escape(m.group(1)) + r'\s*=\s*"([A-Za-z0-9]{16,})"', js)
            if d:
                return d.group(1)
        d = re.search(r'=\s*"([A-Za-z0-9]{32})"\s*;\s*function[^}]*X-Api-Key', js)
        if d:
            return d.group(1)
    raise RuntimeError("Erisim anahtari sitede bulunamadi")


veri = json.loads(cek(API, {"X-Api-Key": anahtar()}))
bul = lambda kod: next(x for x in veri if x.get("code") == kod)
kg, ons, kur = bul("ALTIN KG/TRY"), bul("ALTIN ONS/USD"), bul("USD/TRY")
simdi = datetime.now(TR)

fiyat = {
    "alis": round(kg["bidPrice"] / 1000, 2),      # IAR'in senden aldigi (bozdurma)
    "satis": round(kg["askPrice"] / 1000, 2),     # senin odedigin
    "ons": round((ons["askPrice"] + ons["bidPrice"]) / 2, 2),
    "kur": round((kur["askPrice"] + kur["bidPrice"]) / 2, 4),
    "zaman": simdi.isoformat(timespec="seconds"),
    "kaynak": "IAR Platform · ALTIN KG/TRY",
}
with open(os.path.join(KLASOR, "fiyat.json"), "w", encoding="utf-8") as f:
    json.dump(fiyat, f, ensure_ascii=False, indent=1)

yol = os.path.join(KLASOR, "fiyat_gecmisi.json")
with open(yol, encoding="utf-8") as f:
    gecmis = json.load(f)
bugun = simdi.strftime("%Y-%m-%d")
satir = {"t": bugun, "a": fiyat["alis"], "o": fiyat["ons"], "k": fiyat["kur"], "s": "IAR"}
gecmis["gunler"] = [g for g in gecmis["gunler"] if g["t"] != bugun] + [satir]
gecmis["gunler"].sort(key=lambda g: g["t"])
with open(yol, "w", encoding="utf-8") as f:
    json.dump(gecmis, f, ensure_ascii=False, indent=1)

print(f"{fiyat['zaman']} · gram alis {fiyat['alis']} · satis {fiyat['satis']} · kur {fiyat['kur']}")
