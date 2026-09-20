# Altın Panosu

IAR Platform verisiyle çalışan tek sayfalık gram altın takip uygulaması.

- **Kişisel veri içermez.** Portföy (alım/satım kayıtları) yalnızca kullanıcının tarayıcısında (localStorage) durur, sunucuya gönderilmez.
- `fiyat.json` ve `fiyat_gecmisi.json` piyasa verisidir; GitHub Actions 15 dakikada bir tazeler.
- Erişim anahtarı depoda tutulmaz; IAR'ın kendi açık web sayfasından çalışma anında okunur.
- Kâr/zarar bozdurma (alış) fiyatıyla hesaplanır. Bilgilendirme amaçlıdır, yatırım tavsiyesi değildir.
