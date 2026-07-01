// Service worker AVCare
// Rôle : (1) permettre l'installation de l'appli (PWA),
//        (2) recevoir et afficher les notifications push,
//        (3) mettre en cache quelques ressources statiques pour un
//            démarrage plus rapide (pas de mode hors-ligne complet,
//            les données patients doivent rester à jour).

const CACHE_NAME = "avcare-cache-v1";
const RESSOURCES_STATIQUES = [
  "/static/css/style.css",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(RESSOURCES_STATIQUES))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((noms) =>
      Promise.all(
        noms
          .filter((nom) => nom !== CACHE_NAME)
          .map((nom) => caches.delete(nom))
      )
    )
  );
  self.clients.claim();
});

// Sert le cache uniquement pour les fichiers statiques (CSS, icônes).
// Toutes les pages (patients, consultations...) passent toujours par
// le réseau pour ne jamais afficher des données médicales périmées.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(event.request).then((reponse) => reponse || fetch(event.request))
    );
  }
});

// Réception d'une notification push envoyée par le serveur Django.
self.addEventListener("push", (event) => {
  let data = { title: "AVCare", body: "Nouvelle notification", url: "/" };
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/static/icons/icon-192.png",
      badge: "/static/icons/icon-192.png",
      data: { url: data.url || "/" },
    })
  );
});

// Clic sur la notification : ouvre (ou remet au premier plan) l'appli.
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const cible = event.notification.data?.url || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window" }).then((clientsArr) => {
      for (const client of clientsArr) {
        if (client.url.includes(cible) && "focus" in client) {
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(cible);
      }
    })
  );
});
