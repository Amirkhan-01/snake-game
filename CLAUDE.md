# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Snake game shipped as a **web/PWA game** (the actual product, deployed to Vercel and wrapped for
Google Play), plus an older **standalone Python/Pygame desktop game**.

**The two games share no code.** `snake.py` (Pygame) and `web/index.html` (vanilla JS/Canvas) are
independent implementations of the same idea. Changes to one do not affect the other. Almost all
active work happens in `web/`.

## Commands

```bash
# Web game — no build step; just serve the folder
cd web && python serve.py          # http://localhost:8000  (or: python -m http.server 8000)

# Native bridge — the ONLY thing that compiles (esbuild: src/native.js -> web/native.js)
npm run build:native               # required after ANY edit to src/native.js
npx cap sync android               # copies web/ into android/ + registers plugins
npm run sync                       # = build:native && cap sync

# Android APK (JDK 21 required; Android Studio ships one)
cd android && JAVA_HOME="/d/Android Studio/jbr" ./gradlew assembleDebug --no-daemon
# -> android/app/build/outputs/apk/debug/app-debug.apk
npx cap open android               # open in Android Studio (for signed release builds)

# Desktop Pygame game (unrelated to the web game)
python snake.py                    # deps: pip install -r requirements.txt
```

`android/local.properties` is gitignored and machine-specific; it must contain the SDK path using
**forward slashes** (`sdk.dir=C:/Users/.../Android/Sdk`) — backslashes are escape chars in
`.properties` files and cause `Invalid file path`.

## Architecture: the web game

`web/index.html` is the entire game in one file (~1600 lines): inline `<style>`, HTML overlays, and
a single IIFE `<script>`. No framework, no bundler, no modules. There are exactly two script tags:
`native.js` (the bundled bridge) and the inline game.

Key seams inside that IIFE:

- **Game loop** — `frame(ts)` runs *always* (menus, store, paused); `update(dt)` **early-returns**
  when `!G.running || G.paused || G.over`. Anything that must keep ticking outside gameplay
  (notification expiry, effect badges) belongs in `frame()`, not `update()`. This distinction has
  already caused one bug (notifications piling up in the store).
- **State** — one mutable `G` object holds everything. `step()` advances the grid; `eatFood()` is
  shared by grid pickups and the magnet fly-in.
- **Grid** — `GRID = 22`, square board for both axes. Cell size is derived in `resize()` from the
  smaller viewport dimension; the board is width-bound on phones. Making the board non-square means
  splitting `GRID` into cols/rows across ~15 call sites.
- **Persistence** — the `store` helper wraps `localStorage` with a `snake_` prefix and JSON
  encoding. New persisted keys must also be added to the reset list in the `setReset` handler.

### Monetization seams

`playAd()` and `IAP.purchase()` are the only integration points between game logic and money.

- **Web** → built-in demo flows (simulated ad overlay, demo purchase sheet). Always works offline.
- **Native + configured** → real AdMob / RevenueCat via `window.SnakeNative`.

`src/native.js` decides which: `STORE_READY = /^goog_/.test(revenueCatApiKey)` — a `test_` key is
deliberately *not* enough, so builds without production keys fall back to the demo flow instead of
silently doing nothing. `TEST_ADS` auto-detects Google's test ad ids and flips
`initializeForTesting`. All real ids live in `src/native.js` CONFIG, except the AdMob **App ID**
which must also be in `android/app/src/main/AndroidManifest.xml` and match the same publisher.

Interstitials are capped (every 3rd replay, min 90s apart, never for ad-free users, never on web) —
Google policy requires natural break points only.

### Localization

`STRINGS.en` / `STRINGS.ru` + `t(key)` + `applyLang(lang)`. Language auto-detects from
`navigator.language`, persists, and is toggleable in Settings.

Adding user-visible text requires **both**: a key in `STRINGS` (both locales) *and* wiring in
`applyLang()`, which sets static overlay elements by id/selector. Dynamically rendered text
(`updateHUD`, `renderShop`, `renderStats`, `gameOver`) must call `t()` itself — `applyLang()` re-runs
those renderers at the end.

### Service worker

`web/sw.js` caches all assets. **Bump `CACHE = 'snake-vN'` on every web change**, otherwise users
keep the stale build. New files must be added to its `ASSETS` list.

## Testing

There is no test framework. Logic is verified with an ad-hoc Node harness:

1. Extract the **last** `<script>` block from `web/index.html`.
2. Inject an export hook before the IIFE closes:
   `.replace('})();', 'globalThis.__api={G,startGame,step,update,...};\n})();')`
3. Stub the browser in Node — `document` (with `getElementById` returning a permissive Proxy),
   `window`, `navigator`, `localStorage`, `performance.now()` backed by a controllable `clock`,
   and no-op `requestAnimationFrame`/`setInterval`.
4. Drive `__api` directly and assert on `G`.

Advance the fake `clock` manually to test anything time-based (magnet flight, combos, ad capping,
notification expiry). `node --check` on the extracted script catches syntax errors quickly.

Visual checks use headless Chrome screenshots against the local server. **Gotcha:** headless Chrome
clamps `innerWidth` to ~500px, so a smaller `--window-size` *crops* a 500px-wide render rather than
reflowing it — narrow-screen "overflow" seen this way is usually an artifact, not a bug. CSS
animations also may not finish before capture; inject `*{animation:none!important}` for clean shots.

## Deployment

Push to `master` → Vercel auto-deploys (**Root Directory = `web`**, no build command) →
https://snake-game-tau-orcin.vercel.app/

## Project status and plans

`ROADMAP.md` holds the live status snapshot and remaining steps (it is kept current — read it
first). `NATIVE_SETUP.md` covers keys/build/store forms, `PUBLISHING.md` covers web hosting.

## Constraints worth knowing

- **Never trigger the app's own ads** in a build with real ad unit ids — AdMob bans accounts for
  self-clicks. Switch to Google's test ids when verifying ad flows.
- iOS Safari does not support `beforeinstallprompt`; install there is a manual "Add to Home Screen"
  instructions overlay, gated on iOS detection.
- Use `100dvh`, not `100vh`, for full-height layout — iOS Safari's `100vh` ignores browser chrome
  and hides the HUD/toolbar behind it. Respect `env(safe-area-inset-*)` (`viewport-fit=cover` is set).
- Real purchases additionally require a Google Play Console account, products, and a RevenueCat Play
  Store service-account JSON — they cannot work from code alone.
