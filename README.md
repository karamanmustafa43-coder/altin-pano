# Altın Panosu

IAR Platform verisiyle çalışan tek sayfalık gram altın takip uygulaması.

- **Kişisel veri içermez.** Portföy (alım/satım kayıtları) yalnızca kullanıcının tarayıcısında (localStorage) durur, sunucuya gönderilmez.
- `fiyat.json` ve `fiyat_gecmisi.json` piyasa verisidir; GitHub Actions 15 dakikada bir tazeler.
- Erişim anahtarı depoda tutulmaz; IAR'ın kendi açık web sayfasından çalışma anında okunur.
- Kâr/zarar bozdurma (alış) fiyatıyla hesaplanır. Bilgilendirme amaçlıdır, yatırım tavsiyesi değildir.

## Yayınlama
Her değişiklikten sonra:

    python surum_bas.py && git add -A && git commit -m "..." && git push

`surum_bas.py`, `index.html` içindeki `SURUM` damgasını ve `surum.json`'u tazeler.
Uygulama açılışta (ve 5 dakikada bir) `surum.json`'u önbelleksiz okur; damga değişmişse kendini yeniden yükler.
Yani kullanıcının elle önbellek temizlemesi gerekmez.
