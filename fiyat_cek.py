"""IAR Platform'dan guncel gram altin fiyatini alir, fiyat.json ve fiyat_gecmisi.json'u gunceller.

GitHub Actions icinde calisir. Erisim anahtari depoda TUTULMAZ: IAR'in kendi sitesinin
herkese acik on yuz dosyasindan calisma aninda okunur (siteyi acan herkesin tarayicisinin yaptigi is).
"""
import json, os, re, ssl, sys, urllib.request
from datetime import datetime, timedelta, timezone

TR = timezone(timedelta(hours=3))
SITE = "https://www.iarplatform.com/"
API = "https://tstapi.iarplatform.com/api/ForInvest/GetAll?groupId=1"
SARRAFIYE_API = "https://tstapi.iarplatform.com/api/ForInvest/GetAll?groupId=13"   # Ziynet grubu

# Uygulamadaki cins anahtari -> IAR kodunun sadelestirilmis hali (ilk bulunan kullanilir).
# "Yeni" basim once denenir; piyasada standart kotasyon odur.
CINS_KODLARI = {
    "ceyrek": ["YENI CEYREK", "ESKI CEYREK"],
    "yarim":  ["YENI YARIM", "ESKI YARIM"],
    "tam":    ["YENI TAM", "ESKI TAM"],
    "ata":    ["YENI ATA", "ESKI ATA"],
}
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


gizli = anahtar()
veri = json.loads(cek(API, {"X-Api-Key": gizli}))
bul = lambda kod: next(x for x in veri if x.get("code") == kod)
kg, ons, kur = bul("ALTIN KG/TRY"), bul("ALTIN ONS/USD"), bul("USD/TRY")
simdi = datetime.now(TR)


def sadelestir(s):
    """Kod adini eslestirilebilir hale getirir: 'YENİ ÇEYREK' -> 'YENI CEYREK'."""
    cev = str.maketrans("ÇĞİIÖŞÜçğıiöşü", "CGIIOSUCGIIOSU")
    return re.sub(r"[^A-Z0-9]+", " ", str(s).translate(cev).upper()).strip()


def sarrafiye_cek():
    """Ziynet grubundan (groupId=13) tam/yarim/ceyrek/ata fiyatlarini adet basina TL olarak alir.

    Kod adlari degisirse eslesme bos doner; o zaman sarrafiye alani hic yazilmaz ve
    uygulama gram fiyatindan tahmine duser. Eslesmeyen durumda butun kodlar loga basilir.
    """
    try:
        ham = json.loads(cek(SARRAFIYE_API, {"X-Api-Key": gizli}))
        if not isinstance(ham, list):
            print("sarrafiye: liste bekleniyordu, gelen:", str(ham)[:200])
            return None
        return _sarrafiye_ayristir(ham)
    except Exception as e:
        print("sarrafiye alinamadi:", e)
        return None


def _sarrafiye_ayristir(ham):
    esleme = {x.get("code"): x for x in ham if isinstance(x, dict)}
    sade = {sadelestir(k): v for k, v in esleme.items()}
    out = {}
    for anahtar_ad, adaylar in CINS_KODLARI.items():
        for aday in adaylar:
            kayit = sade.get(aday)
            if kayit and kayit.get("bidPrice") and kayit.get("askPrice"):
                out[anahtar_ad] = {"alis": round(kayit["bidPrice"], 2),
                                   "satis": round(kayit["askPrice"], 2), "kod": kayit.get("code")}
                break
    if not out:
        print("sarrafiye eslesmedi · gelen kodlar:", sorted(sade))
        return None
    eksik = [k for k in CINS_KODLARI if k not in out]
    if eksik:
        print("sarrafiyede eslesmeyen cins:", eksik, "· gelen kodlar:", sorted(sade))
    out["zaman"] = simdi.isoformat(timespec="seconds")
    out["kaynak"] = "IAR Platform · Ziynet"
    return out


fiyat = {
    "alis": round(kg["bidPrice"] / 1000, 2),      # IAR'in senden aldigi (bozdurma)
    "satis": round(kg["askPrice"] / 1000, 2),     # senin odedigin
    "ons": round((ons["askPrice"] + ons["bidPrice"]) / 2, 2),
    "kur": round((kur["askPrice"] + kur["bidPrice"]) / 2, 4),
    "zaman": simdi.isoformat(timespec="seconds"),
    "kaynak": "IAR Platform · ALTIN KG/TRY",
}
sarrafiye = sarrafiye_cek()
if sarrafiye:
    fiyat["sarrafiye"] = sarrafiye
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
