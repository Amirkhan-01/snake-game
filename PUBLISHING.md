# Публикация веб-версии

Веб-версия (`web/`) — статический сайт (HTML5 + JavaScript, PWA). Никакой сборки не нужно:
залей содержимое папки `web/` на любой статический хостинг.

## Что внутри `web/`
- `index.html` — сама игра
- `privacy.html` — политика конфиденциальности (нужна для сторов)
- `manifest.webmanifest`, `sw.js` — PWA (установка на телефон + офлайн)
- `icon-*.png`, `apple-touch-icon.png`, `favicon-32.png` — иконки
- `og-image.png` — превью при шеринге в соцсети
- `_headers`, `.nojekyll` — служебные файлы для хостинга

## Вариант 1 — GitHub Pages (бесплатно)
1. Создай репозиторий, положи содержимое `web/` в корень (или в папку `docs/`).
2. Settings → Pages → Source: ветка `main`, папка `/ (root)` или `/docs`.
3. Через минуту игра будет на `https://<username>.github.io/<repo>/`.
4. Файл `.nojekyll` уже есть — он нужен, чтобы GitHub не ломал раздачу.

## Вариант 2 — Netlify / Vercel (бесплатно, свой домен)
1. Перетащи папку `web/` на https://app.netlify.com/drop — готово.
2. Или подключи Git-репозиторий, publish directory = `web`.
3. `_headers` подхватится автоматически.

## Вариант 3 — itch.io (как HTML-игра)
1. Заархивируй содержимое `web/` в `.zip` (файл `index.html` должен быть в корне архива).
2. На itch.io: New project → Kind = HTML → загрузи zip → отметь «This file will be played in the browser».
3. Укажи размер вьюпорта ~500×800, «mobile friendly».

## После деплоя (важно)
- **Абсолютный og:image.** Для красивого превью в соцсетях замени в `index.html`
  `og-image.png` на полный URL, например `https://твой-домен/og-image.png`
  (в тегах `og:image` и `twitter:image`).
- **HTTPS обязателен** для установки PWA и service worker — все хостинги выше дают его из коробки.
- Проверь установку: открой на телефоне в Chrome → меню → «Установить приложение».

## Store-скриншоты
Готовые скриншоты для страницы магазина/itch.io лежат в `store-screenshots/`.

## Путь в настоящие сторы (Play Market / App Store) — уже подготовлено

**Capacitor-проект уже создан** (`android/`), с рекламой (AdMob) и покупками (RevenueCat),
иконками и splash. Тебе остаётся вписать ключи и собрать AAB — пошагово в
**[NATIVE_SETUP.md](NATIVE_SETUP.md)**.

Быстрая шпаргалка:
```
# после правок в web/ или src/native.js:
npm run build:native      # собрать нативный мост
npx cap sync android      # скопировать web + плагины в android/
npx cap open android      # открыть в Android Studio -> собрать .aab
```
- **App Store (iOS):** на Mac `npm i @capacitor/ios && npx cap add ios && npx cap open ios`,
  Xcode + Apple Developer ($99/год). Тот же код и мост.
- Альтернатива без нативных покупок: TWA через [PWABuilder](https://www.pwabuilder.com/).
