# HANDOFF

Snapshot for continuing this project in a fresh session. Written 2026-07-15.

Companion docs: **[CLAUDE.md](CLAUDE.md)** (how to work in the repo: commands, conventions,
gotchas) · **[ROADMAP.md](ROADMAP.md)** (live status + phases) · **[NATIVE_SETUP.md](NATIVE_SETUP.md)**
(keys, build, store forms) · **[PUBLISHING.md](PUBLISHING.md)** (web hosting).

---

## 1. Current status

The **web game is finished and live**; the **Android wrapper builds**; **store release is blocked on
the owner's paperwork**, not on code.

| Area | State |
|---|---|
| Web/PWA game | ✅ Complete, deployed: https://snake-game-tau-orcin.vercel.app/ |
| GitHub | ✅ Public: https://github.com/Amirkhan-01/snake-game (`master`) |
| Android project (Capacitor 8) | ✅ Compiles, debug APK builds (`dist/snake-debug.apk`, 12 MB) |
| AdMob (rewarded + interstitial) | ⚠️ Wired with real ids, **not yet seen working on device** |
| RevenueCat / purchases | ⏳ Wired; cannot function until Play Console exists |
| Play Store listing | ⏳ Blocked: needs legal entity → D-U-N-S → $25 account |
| Desktop Pygame game | 🟡 Works, unmaintained, separate from the web game |

The owner (Amirkhan-01) is registering a **Georgian legal entity** to obtain a D-U-N-S number for an
**Organization** Play account. That path is ~2–3 weeks. Everything code-side is done and waiting.

## 2. Completed work

**Game (web, `web/index.html`)** — 4 modes (Classic / Obstacles / Hardcore / Time Attack),
power-ups (shield, ×2 score, magnet with off-grid fly-in), combo system, levels, particles,
6 coin skins + 2 premium skins, store, local top-10 leaderboard, daily challenges, daily login
reward with streak, achievements, lifetime stats, 5 themes, procedural sound + music (WebAudio),
haptics, swipe/arrows/WASD input, onboarding, RU/EN localization with auto-detect, share score.

**PWA** — installable, offline (service worker), icons/splash all densities, manifest, OG/Twitter
preview, iOS "Add to Home Screen" instructions overlay.

**Native** — Capacitor 8 Android project, bridge (`src/native.js` → `web/native.js` via esbuild)
wiring AdMob (rewarded, interstitial, UMP consent), RevenueCat (purchase/restore), splash, Android
back button. Manifest: real AdMob App ID, portrait lock, `AD_ID` permission.

**Monetization** — Store UI (Full Version, Remove Ads, coin packs, premium skins), rewarded ad
revive + ×2 coins, interstitials with frequency capping, demo-purchase fallback.

**Ops/docs** — deployed to Vercel with GitHub auto-deploy, privacy policy, terms, store screenshots
+ feature graphic, CLAUDE.md, ROADMAP.md, NATIVE_SETUP.md, PUBLISHING.md.

**Notable fixes** — pygbag build abandoned after it never booted (rewrote in JS); WASD on non-Latin
keyboard layouts (`e.code`); magnet logic (twice); notification pile-up; iOS `100dvh` + safe areas;
black background from lighting/bloom in the Pygame version.

## 3. Pending tasks

### Blocked on the owner (cannot be done from code)
1. Register the Georgian legal entity.
2. Request **D-U-N-S** (free, ~1–2 weeks; do not pay for expedited).
3. Pay **$25** Google Play Console; create app with package `com.snakepremium.game`.
4. Create in-app products with exactly these ids:
   `premium`, `noads`, `coins_1000`, `coins_6000`, `skin_aurora`.
5. Finish RevenueCat's Play Store configuration (**Service Account JSON** — only Play Console issues it).
6. Create a **keystore** and build a signed AAB (passwords are the owner's; losing the keystore means
   never being able to update the app).
7. Host `privacy.html` at a public URL; fill Data Safety / content rating / ads declaration.
8. Optional: Firebase project → `google-services.json` for Crashlytics.

### Available code work (unblocked)
- Diagnose why ads don't show (see Known issues).
- Google Play Games leaderboards/achievements/cloud save (needs a Play Console game id first).
- Content: more skins, trails, player progression, seasons.
- Interstitial ad unit is real but the flow is unverified on device.

## 4. Architecture overview

**Two independent games live here.** `snake.py` (Pygame desktop, ~1340 lines) and
`web/index.html` (vanilla JS/Canvas, ~1600 lines) share **no code**. The web one is the product.

```
web/index.html      inline <style> + HTML overlays + ONE IIFE <script>   ← the whole web game
   └─ loads web/native.js (bundled bridge; the only compiled artifact)
src/native.js       ESM: Capacitor plugins (AdMob / RevenueCat / Splash / App)
   └─ esbuild → web/native.js        (npm run build:native)
capacitor.config.json  webDir: "web"
   └─ npx cap sync android → copies web/ into android/app/src/main/assets/public
android/            generated native project (committed; manifest hand-edited)
```

No framework, no bundler for the game itself, no backend. All state is `localStorage`.

Runtime split that matters:
- `frame(ts)` — always runs (menus, store, paused).
- `update(dt)` — **early-returns** when `!G.running || G.paused || G.over`.
- Anything that must tick outside gameplay belongs in `frame()`.

## 5. Important implementation details

- **Monetization seams** — `playAd()` and `IAP.purchase()` are the only bridges to money.
  Web → demo flows. Native + configured → real SDKs via `window.SnakeNative`.
- **`STORE_READY = /^goog_/.test(revenueCatApiKey)`** — a `test_` key deliberately does *not* count,
  so an unconfigured build falls back to the demo sheet instead of dead buttons.
- **`TEST_ADS`** auto-detects Google's test ad ids (`3940256099942544`) and flips
  `initializeForTesting`. Currently false — all ids are production.
- **AdMob App ID lives in two places conceptually**: `AndroidManifest.xml` (the one that counts) and
  `src/native.js` CONFIG (reference). They must match the same publisher or ads silently fail.
- **i18n needs two edits** — a key in `STRINGS` (en *and* ru) **and** wiring in `applyLang()`.
  Dynamic renderers (`updateHUD`, `renderShop`, `renderStats`, `gameOver`) must call `t()`;
  `applyLang()` re-runs them.
- **Service worker** — bump `CACHE = 'snake-vN'` in `web/sw.js` on **every** web change (now `v17`),
  and add new files to `ASSETS`.
- **Magnet** — during the effect, food leaves the grid: `food.fx/fy` fly at `MAGNET_SPEED` (9
  cells/s) straight to the head and `eatFood()` fires on arrival. Off-magnet, `fx/fy` track the grid.
- **Interstitials** — every 3rd replay, ≥90s apart, never for ad-free users, never on web, only at
  replay (Google policy).
- **iOS** — `100dvh` (not `100vh`) and `env(safe-area-inset-*)`; `viewport-fit=cover` is set. Safari
  has no `beforeinstallprompt`, so install is a manual instructions overlay gated on iOS detection.
- **Persistence** — `store` wraps `localStorage` with a `snake_` prefix + JSON. New keys must be
  added to the reset list in `setReset`.
- **Testing** — no framework. Extract the last `<script>` from `index.html`, inject
  `globalThis.__api={...}` before `})();`, stub the DOM in Node, drive a fake `clock`. See CLAUDE.md.

## 6. File map

```
CLAUDE.md / HANDOFF.md / ROADMAP.md          guidance, this handoff, live status
NATIVE_SETUP.md / PUBLISHING.md              store/build steps, web hosting
README.md                                    player-facing overview

web/                     ← deployed to Vercel (Root Directory = web)
  index.html             the entire web game (game + UI + i18n + store)
  native.js              GENERATED by esbuild — do not hand-edit
  sw.js                  service worker (bump CACHE!)
  manifest.webmanifest   PWA manifest
  privacy.html terms.html
  icon-*.png apple-touch-icon.png favicon-32.png og-image.png
  serve.py play_web.bat  local server helpers
  _headers .nojekyll     host config (Netlify / GitHub Pages)

src/native.js            native bridge source (KEYS LIVE HERE)
capacitor.config.json    appId com.snakepremium.game, webDir web
android/                 generated; AndroidManifest.xml hand-edited (AdMob id, portrait, AD_ID)
assets/                  icon/splash sources for @capacitor/assets
store-screenshots/       listing screenshots + feature-graphic-1024x500.png

snake.py                 standalone Pygame desktop game (separate codebase)
run_game.bat requirements.txt
dist/                    gitignored build output (snake-debug.apk, SnakeGame.exe)
```

## 7. Known issues

1. **Ads not showing on the Android test device** — *the main open item.* Installed the debug APK,
   played several rounds, no rewarded and no interstitial appeared. Undiagnosed by explicit request.
   Likely causes, in order: new AdMob units take **up to 24h** to start serving; ad load failing
   silently (all AdMob calls are wrapped in `try/catch` that only `console.warn`s); interstitial
   requires 3 replays + 90s so it is easy to miss. Next step: `adb logcat | grep -i ads`.
2. **Purchases unavailable** — expected and correct: no Play Console → no products → RevenueCat
   returns "not-found" and the game shows "Покупки пока недоступны".
3. **Square board leaves vertical gaps** on tall phones — accepted by the owner ("с размерами всё
   супер"). The board is width-bound (~96% of width). Filling the gaps requires splitting `GRID`
   into cols/rows (~15 call sites) and changes gameplay.
4. **Toast overlaps the store title** for ~2.6s — cosmetic, deliberate (toasts sit above overlays so
   purchases give feedback).
5. **`versionCode`/`versionName` still 1 / 1.0** in `android/app/build.gradle` — must be bumped
   before any store upload.
6. **Desktop `snake.py` has diverged** — it has none of the web features and is not maintained.
7. **Tooling artifacts (not bugs)**: headless Chrome clamps `innerWidth` to ~500px (small
   `--window-size` crops rather than reflows); CSS animations may not finish before capture; git
   prints harmless LF→CRLF warnings on Windows.

## 8. Next recommended steps

1. **Wait ~24h, reinstall the APK, re-test ads.** If still nothing → `adb logcat` and read the
   AdMob warnings the bridge swallows. Temporarily switching CONFIG to Google's test ids is the
   fastest way to prove the plumbing works (safe to tap those).
2. Owner continues entity → D-U-N-S → $25 → products → Service Account JSON.
3. Meanwhile, ad revenue works **without** the store — distribute the APK directly.
4. Before any upload: bump `versionCode`, build a **signed release** AAB.
5. Optional while waiting: Crashlytics, Play Games (needs console), more content.

## 9. Assumptions and design decisions

- **Rewrote the game in vanilla JS instead of shipping the Pygame code.** pygbag (Python→WASM) was
  tried and abandoned: the runtime loaded but never executed the app archive, reproducibly, across
  servers and browsers. A plain HTML5 rewrite removed the whole class of problem.
- **Single file, no framework, no bundler** (except the native bridge). Rationale: zero build step,
  trivial hosting, works offline, easy for one person to maintain. Cost: `index.html` is large and
  i18n needs manual wiring.
- **Capacitor, not TWA/PWABuilder.** Real AdMob and Google Play Billing need a native shell; a
  wrapped PWA cannot do IAP.
- **Demo-purchase fallback + `goog_`-only gate.** A build without production keys must stay fully
  testable rather than presenting buttons that silently do nothing.
- **Organization Play account over Personal.** Personal requires ~12 testers × 14 days before
  production and publishes the owner's home address; account type cannot be changed later.
- **Local leaderboard, no accounts, no backend.** Keeps privacy simple (nothing leaves the device),
  costs nothing, and makes cross-device fairness a non-issue — which is also why a per-device board
  shape would have been acceptable.
- **Rewarded + capped interstitials only; no banners.** Banners would eat scarce screen space on a
  square board and hurt feel.
- **Square 22×22 board** for consistent play across devices; accepted despite gaps on tall screens.
- **RU/EN only**, auto-detected from the browser locale.
- **`android/` is committed** because the manifest is hand-edited (AdMob id, portrait, AD_ID);
  regenerating it would silently drop those.
- **Keys in the repo are safe**: the RevenueCat `goog_` key and AdMob ids are *public by design*
  (they ship inside the app binary). Secret keys must never be added.
