// Enregistrement du service worker + abonnement aux notifications push.
// Ce script est chargé sur toutes les pages une fois le médecin connecté.

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? match[2] : null;
}

async function activerNotifications() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    alert("Les notifications ne sont pas disponibles sur ce navigateur.");
    return;
  }

  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    alert("Notifications refusées. Tu peux les réactiver dans les réglages du navigateur.");
    return;
  }

  const registration = await navigator.serviceWorker.ready;
  const { vapidPublicKey } = await fetch("/notifications/cle-publique/").then((r) => r.json());

  let subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
    });
  }

  await fetch("/notifications/abonner/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(subscription),
  });

  return subscription;
}

async function testerNotifications() {
  const reponse = await fetch("/notifications/tester/", {
    method: "POST",
    headers: { "X-CSRFToken": getCookie("csrftoken") },
  }).then((r) => r.json());

  if (!reponse.ok) {
    alert(reponse.erreur || "Échec de l'envoi du test.");
  }
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js", { scope: "/" });
  });
}
