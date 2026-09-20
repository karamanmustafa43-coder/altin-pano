/* Delta — çevrimdışı katmanı.
   Strateji: aynı kaynaktaki dosyalarda önce ağ, olmazsa önbellek (network-first).
   Böylece çevrimiçiyken hep güncel sürüm gelir, internet yokken uygulama yine açılır.
   Supabase ve IAR istekleri (farklı kaynak) hiç önbelleğe alınmaz. */
const AD = "delta-v1";
const ONBELLEK = [
  "./", "./index.html", "./manifest.json",
  "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./favicon.png",
  "./fiyat.json", "./fiyat_gecmisi.json", "./enflasyon.json"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(AD).then(c => c.addAll(ONBELLEK)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(adlar => Promise.all(adlar.filter(a => a !== AD).map(a => caches.delete(a))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const istek = e.request;
  if (istek.method !== "GET") return;
  const url = new URL(istek.url);
  if (url.origin !== location.origin) return;            // Supabase / IAR: dokunma

  e.respondWith(
    fetch(istek)
      .then(yanit => {
        if (yanit && yanit.ok) {
          const kopya = yanit.clone();
          caches.open(AD).then(c => c.put(istek, kopya));
        }
        return yanit;
      })
      .catch(async () => {
        const c = await caches.open(AD);
        return (await c.match(istek)) || (await c.match("./index.html")) ||
               new Response("Çevrimdışı", {status: 503, headers: {"Content-Type": "text/plain; charset=utf-8"}});
      })
  );
});
