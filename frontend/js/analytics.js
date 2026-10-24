/* Disabled until a measurement ID and explicit visitor consent are supplied. */
(() => {
    'use strict';
    const ANALYTICS_ID = 'G-XXXXXXXXXX';
    let loaded = false;

    function loadAnalytics() {
        if (loaded || ANALYTICS_ID === 'G-XXXXXXXXXX' || !/^G-[A-Z0-9]+$/.test(ANALYTICS_ID)) return;
        if (window.plexudoAnalyticsConsent !== true) return;
        if (navigator.globalPrivacyControl === true || navigator.doNotTrack === '1') return;
        loaded = true;
        window.dataLayer = window.dataLayer || [];
        window.gtag = function () { window.dataLayer.push(arguments); };
        window.gtag('js', new Date());
        window.gtag('config', ANALYTICS_ID);
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(ANALYTICS_ID)}`;
        document.head.appendChild(script);
    }

    window.addEventListener('plexudo:analytics-consent', loadAnalytics);
    loadAnalytics();
})();
