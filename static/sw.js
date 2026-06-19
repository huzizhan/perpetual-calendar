// ═══════════════════════════════════════════════════════════
// 万年历 Service Worker — PWA 核心
// 版本号递增即可触发全量更新
// ═══════════════════════════════════════════════════════════

const VERSION = "v1.0.0";
const STATIC_CACHE = `calendar-static-${VERSION}`;
const API_CACHE = `calendar-api-${VERSION}`;
const IMAGE_CACHE = `calendar-images-${VERSION}`;

// ── 安装：预缓存关键静态资源 ─────────────────────────────
const PRE_CACHE = [
  "/",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/offline.html",
];

self.addEventListener("install", (event) => {
  console.log(`[SW] Installing ${VERSION}...`);
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRE_CACHE))
      .then(() => self.skipWaiting())
  );
});

// ── 激活：清理旧版本缓存 ─────────────────────────────────
self.addEventListener("activate", (event) => {
  console.log(`[SW] Activating ${VERSION}...`);
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k.startsWith("calendar-") && k !== STATIC_CACHE && k !== API_CACHE && k !== IMAGE_CACHE)
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ── 请求拦截：分层缓存策略 ─────────────────────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 跳过非 GET 请求
  if (request.method !== "GET") return;

  // API 请求 → Network First，失败降级到缓存
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(networkFirst(request, API_CACHE));
    return;
  }

  // 图片 / 图标 → Cache First（变更少）
  if (url.pathname.match(/\.(png|jpg|svg|ico|webp)$/) || url.pathname.includes("/icons/")) {
    event.respondWith(cacheFirst(request, IMAGE_CACHE));
    return;
  }

  // HTML / 页面 → Network First，离线回退
  if (request.mode === "navigate" || url.pathname === "/") {
    event.respondWith(
      networkFirst(request, STATIC_CACHE).catch(() =>
        caches.match("/static/offline.html")
      )
    );
    return;
  }

  // 其他静态资源 → Cache First
  event.respondWith(cacheFirst(request, STATIC_CACHE));
});

// ── 策略函数 ──────────────────────────────────────────────

/** Cache First：优先读缓存，未命中才请求网络并缓存 */
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    return new Response("Offline", { status: 503 });
  }
}

/** Network First：优先请求网络，失败时读缓存 */
async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    const cached = await caches.match(request);
    return cached || new Response("Offline", { status: 503 });
  }
}

// ── 消息通道：允许页面触发缓存更新 ────────────────────────
self.addEventListener("message", (event) => {
  if (event.data === "SKIP_WAITING") {
    self.skipWaiting();
  }
  if (event.data === "CLEAR_CACHES") {
    caches.keys().then((keys) => keys.forEach((k) => caches.delete(k)));
  }
});
