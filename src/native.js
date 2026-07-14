// Native bridge for the Capacitor (Android/iOS) build.
// Bundled to web/native.js by esbuild (npm run build:native).
// On web (non-native) every method is a no-op / returns false, so the game's
// built-in demo purchase & ad flows keep working unchanged.
//
// ============================================================================
//  BEFORE RELEASE, fill CONFIG below with your real keys/ids (see NATIVE_SETUP.md)
// ============================================================================
import { Capacitor } from '@capacitor/core';
import { AdMob } from '@capacitor-community/admob';
import { Purchases, LOG_LEVEL } from '@revenuecat/purchases-capacitor';
import { SplashScreen } from '@capacitor/splash-screen';
import { App } from '@capacitor/app';

const CONFIG = {
  packageId: 'com.snakepremium.game',
  // RevenueCat public SDK key (Android starts with "goog_", iOS with "appl_")
  revenueCatApiKey: 'goog_REPLACE_WITH_YOUR_KEY',
  // AdMob rewarded ad unit id (create in AdMob console). Test id used as placeholder.
  rewardedAdUnitId: 'ca-app-pub-3940256099942544/5224354917',   // <-- Google TEST id
  interstitialAdUnitId: 'ca-app-pub-3940256099942544/1033173712', // <-- Google TEST id
  // Map the game's internal product ids -> the product ids you create in the store.
  PRODUCTS: {
    premium:     'premium',
    noads:       'noads',
    coins1000:   'coins_1000',
    coins6000:   'coins_6000',
    skin_aurora: 'skin_aurora',
  },
};

const isNative = Capacitor.isNativePlatform();
// Until you paste real keys, the build runs FREE & fully playable:
// Google TEST ads are shown, and purchases fall back to the in-app demo flow.
const STORE_READY = CONFIG.revenueCatApiKey.indexOf('REPLACE') === -1;
const TEST_ADS = /3940256099942544/.test(CONFIG.rewardedAdUnitId); // Google's test ad ids

const Native = {
  isNative,
  storeReady: STORE_READY,
  config: CONFIG,

  async init() {
    if (!isNative) return;
    try { await SplashScreen.hide(); } catch (e) {}
    // ---- Ads + consent (GDPR/UMP) ----
    try {
      await AdMob.initialize({ initializeForTesting: TEST_ADS });
      const consent = await AdMob.requestConsentInfo();
      if (consent && consent.isConsentFormAvailable && consent.status === 'REQUIRED') {
        await AdMob.showConsentForm();
      }
    } catch (e) { console.warn('[native] AdMob init failed', e); }
    // ---- In-app purchases (RevenueCat) — only when a real key is set ----
    if (STORE_READY) {
      try {
        await Purchases.setLogLevel({ level: LOG_LEVEL.ERROR });
        await Purchases.configure({ apiKey: CONFIG.revenueCatApiKey });
      } catch (e) { console.warn('[native] Purchases init failed', e); }
    }
  },

  // Show a rewarded ad. Resolves true only if the user earned the reward.
  async showRewarded() {
    if (!isNative) return false;
    try {
      await AdMob.prepareRewardVideoAd({ adId: CONFIG.rewardedAdUnitId });
      const reward = await AdMob.showRewardVideoAd();
      return !!reward;
    } catch (e) { console.warn('[native] rewarded ad failed', e); return false; }
  },

  // Optional: interstitial between games (call with frequency capping in the game).
  async showInterstitial() {
    if (!isNative) return;
    try {
      await AdMob.prepareInterstitial({ adId: CONFIG.interstitialAdUnitId });
      await AdMob.showInterstitial();
    } catch (e) { console.warn('[native] interstitial failed', e); }
  },

  // Purchase by the game's internal product id. Returns {ok:boolean, reason?}.
  async purchase(internalId) {
    if (!isNative) return { ok: false, reason: 'web' };
    if (!STORE_READY) return { ok: false, reason: 'not-configured' }; // free build -> game uses demo sheet
    const storeId = CONFIG.PRODUCTS[internalId] || internalId;
    try {
      const { products } = await Purchases.getProducts({ productIdentifiers: [storeId] });
      if (!products || !products.length) return { ok: false, reason: 'not-found' };
      await Purchases.purchaseStoreProduct({ product: products[0] });
      return { ok: true };
    } catch (e) {
      const cancelled = e && (e.code === '1' || e.userCancelled || /cancel/i.test(e.message || ''));
      return { ok: false, reason: cancelled ? 'cancelled' : 'error' };
    }
  },

  // Restore non-consumable purchases (required by stores). Returns owned product ids.
  async restore() {
    if (!isNative) return [];
    try {
      const info = await Purchases.restorePurchases();
      const ci = info && info.customerInfo ? info.customerInfo : info;
      const active = (ci && ci.allPurchasedProductIdentifiers) || [];
      // Map store ids back to internal ids
      const inv = Object.fromEntries(Object.entries(CONFIG.PRODUCTS).map(([k, v]) => [v, k]));
      return active.map(id => inv[id] || id);
    } catch (e) { console.warn('[native] restore failed', e); return []; }
  },

  // Ask the platform to open the in-app review / store listing.
  async rate() {
    if (!isNative) { window.open('https://play.google.com/store/apps/details?id=' + CONFIG.packageId, '_blank'); return; }
    try { window.open('market://details?id=' + CONFIG.packageId, '_system'); } catch (e) {}
  },

  async hideSplash() { try { await SplashScreen.hide(); } catch (e) {} },
};

if (isNative) {
  Native.init();
  // Back button: let the game handle menus; exit only from the main menu.
  try {
    App.addListener('backButton', () => {
      if (typeof window.snakeBackButton === 'function') window.snakeBackButton();
      else App.exitApp();
    });
  } catch (e) {}
}

window.SnakeNative = Native;
