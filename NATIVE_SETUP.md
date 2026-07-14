# Нативная сборка (Android) — что осталось сделать тебе

Вся кодовая часть готова: Capacitor-проект (`android/`), нативный мост (`src/native.js` →
`web/native.js`), плагины рекламы (AdMob) и покупок (RevenueCat) подключены к игре, иконки и
splash сгенерированы, манифест настроен. Ниже — **только твои шаги**: вписать ключи, собрать, залить.

---

## Шаг 0. Установить инструменты (один раз)
- **Android Studio** (включает JDK и Android SDK): https://developer.android.com/studio
- Node.js уже есть (проект собран на нём).

## Шаг 1. Ключи — ✅ УЖЕ ВПИСАНЫ
| Поле | Значение | Статус |
|---|---|---|
| `packageId` / `appId` | `com.snakepremium.game` | ✅ |
| `revenueCatApiKey` | `goog_…` (публичный Android-ключ RevenueCat) | ✅ |
| AdMob **App ID** (в `AndroidManifest.xml`) | `ca-app-pub-7978127632650379~7654152943` | ✅ |
| `rewardedAdUnitId` | `ca-app-pub-7978127632650379/5662982647` | ✅ |
| `interstitialAdUnitId` | `ca-app-pub-7978127632650379/9077402484` | ✅ |
| `PRODUCTS` | `premium`, `noads`, `coins_1000`, `coins_6000`, `skin_aurora` | ⏳ создать в Play Console |

Если что-то менял в `src/native.js` — пересобери мост:
```
npm run build:native   # esbuild src/native.js -> web/native.js
npx cap sync android
```

**Реклама** заработает сразу после сборки. **Покупки** включатся автоматически, как только
в Play Console появятся товары и в RevenueCat будет достроена Play Store конфигурация
(нужен Service Account JSON — выдаёт Play Console, т.е. после оплаты $25).

## Шаг 2. Товары и подписки
В **Google Play Console → Monetize → Products → In-app products** создай товары с id из `PRODUCTS`:
`premium`, `noads`, `coins_1000`, `coins_6000`, `skin_aurora` (цены на твоё усмотрение).
Эти же товары подключи в **RevenueCat** (он проксирует покупки и валидирует чеки — свой бэкенд не нужен).

## Шаг 3. Собрать приложение
```
npx cap open android        # откроет проект в Android Studio
```
В Android Studio:
1. Дай ему скачать Gradle/SDK при первом открытии.
2. Запусти на эмуляторе/телефоне (кнопка ▶) — проверь, что игра, реклама (тестовая) и покупки работают.
3. Собери релиз: **Build → Generate Signed Bundle / APK → Android App Bundle (.aab)**,
   создай keystore (сохрани его и пароли!), собери подписанный `.aab`.
   Версию меняй в `android/app/build.gradle` (`versionCode` / `versionName`).

## Шаг 4. Google Play Console
- Аккаунт разработчика — **$25** разово.
- Создай приложение, залей `.aab` во **внутреннее тестирование**, потом в продакшн.
- **Листинг:** иконка 512×512 (`assets/icon.png`), feature graphic
  (`store-screenshots/feature-graphic-1024x500.png`), минимум 2 скриншота
  (`store-screenshots/`), описание (можно из `README`/ниже).
- **Политики:** URL политики (`privacy.html`, размести на своём хостинге или рядом с веб-версией).
- Заполни анкеты (см. подсказки ниже).

---

## Ответы для форм Play Console (подсказки)

**Data safety (безопасность данных):**
- Собираете ли вы данные? Игра сама по себе данных на сервер не шлёт (прогресс — локально).
  Но **AdMob и RevenueCat** собирают данные для рекламы/покупок — укажи их:
  - Device or other IDs (advertising id) — да, для рекламы (AdMob).
  - Purchase history — да (RevenueCat/биллинг).
  - Данные шифруются при передаче — да.
  - Можно ли запросить удаление — по политике сторов/провайдеров.
- Ссылки на политики AdMob/Google и RevenueCat приложи, если попросят.

**Ads declaration:** приложение **содержит рекламу** — да.

**Content rating:** пройди анкету (аркада без насилия → обычно рейтинг для всех / PEGI 3).
Если реклама может быть не для детей — не помечай как «для детей» (иначе ограничения на рекламу).

**Target audience:** укажи возраст 13+ (проще с рекламой), если не таргетируешь детей.

---

## iOS (если будешь делать)
На Mac: `npm i @capacitor/ios && npx cap add ios && npx cap open ios`, далее Xcode +
Apple Developer ($99/год). Тот же мост и плагины работают; ключ RevenueCat для iOS — `appl_...`.

## Короткое описание для стора (можно править)
> **Snake — Premium Edition.** Классическая змейка нового уровня: 4 режима (Classic, Obstacles,
> Hardcore, Time Attack), усилители (щит, ×2 очки, магнит), скины и магазин, ежедневные задания,
> достижения, таблица рекордов и темы оформления. Собирай комбо, побивай рекорд, открывай скины!
