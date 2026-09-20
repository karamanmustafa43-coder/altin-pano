"""Diyanet Isleri Baskanligi'nin Dayton (Ohio) namaz vakitlerini cekip namaz.json'a yazar.

Diyanet sitesi bugunden itibaren ~400 gun veriyor; gecmis gunler sitede yok, bu yuzden
dosyadaki eski kayitlar korunur (her calismada birlestirilir). 120 gunden eskiler duser.
GitHub Actions icinde calisir; tarayici Diyanet'e dogrudan erisemedigi icin veri boyle hazirlanir.
"""
import html, json, os, re, sys, urllib.request
from datetime import date, datetime, timedelta

KLASOR = os.path.dirname(os.path.abspath(__file__))
ILCE = 8922                     # DAYTON / OHIO / ABD
ADRES = f"https://namazvakitleri.diyanet.gov.tr/tr-TR/{ILCE}/dayton-icin-namaz-vakti"
AYLAR = {"Ocak":1, "Şubat":2, "Mart":3, "Nisan":4, "Mayıs":5, "Haziran":6,
         "Temmuz":7, "Ağustos":8, "Eylül":9, "Ekim":10, "Kasım":11, "Aralık":12}
ALANLAR = ["Imsak", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

sys.stdout.reconfigure(encoding="utf-8")


def cek():
    r = urllib.request.Request(ADRES, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(r, timeout=60) as y:
        return y.read().decode("utf-8", "ignore")


def ayikla(sayfa):
    gunler = {}
    for satir in re.findall(r"<tr>(.*?)</tr>", sayfa, re.S):
        h = [html.unescape(re.sub("<[^>]+>", "", c)).strip()
             for c in re.findall(r"<td[^>]*>(.*?)</td>", satir, re.S)]
        if len(h) < 8:
            continue
        parca = h[0].split()                       # "21 Eylül 2026 Pazartesi"
        if len(parca) < 3 or parca[1] not in AYLAR:
            continue
        t = date(int(parca[2]), AYLAR[parca[1]], int(parca[0])).isoformat()
        gunler[t] = dict(zip(ALANLAR, h[2:8]))
    return gunler


yol = os.path.join(KLASOR, "namaz.json")
eski = json.load(open(yol, encoding="utf-8"))["gunler"] if os.path.exists(yol) else {}
yeni = ayikla(cek())
if not yeni:
    raise SystemExit("Diyanet sayfasindan vakit okunamadi")

birlesik = {**eski, **yeni}                        # yeni veri gecerli, eski gunler korunur
sinir = (date.today() - timedelta(days=120)).isoformat()
birlesik = {t: v for t, v in sorted(birlesik.items()) if t >= sinir}

with open(yol, "w", encoding="utf-8") as f:
    json.dump({"kaynak": "Diyanet İşleri Başkanlığı · Dayton, Ohio",
               "guncellendi": datetime.now().isoformat(timespec="seconds"),
               "gunler": birlesik}, f, ensure_ascii=False)
ilk, son = min(birlesik), max(birlesik)
print(f"{len(birlesik)} gun ({ilk} … {son}) · yeni cekilen: {len(yeni)}")
