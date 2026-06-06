self.addEventListener('push', function(event) {
  let data = { title: 'PowerMind', body: 'Nova venda!', url: '/afiliada' };
  try { data = JSON.parse(event.data.text()); } catch(e) {}

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/logo.png',
      badge: '/logo.png',
      tag: 'pm-venda',
      data: { url: data.url }
    })
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/afiliada';
  event.waitUntil(clients.openWindow(url));
});
