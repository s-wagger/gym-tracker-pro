/**
 * Gym Tracker Pro - Progressive Web App (PWA) Manager
 * Registers the Service Worker and manages the "Install App" prompt across devices.
 */

let deferredPrompt = null;

// 1. Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then((reg) => {
        console.log('[PWA] Service Worker registered successfully with scope:', reg.scope);
      })
      .catch((err) => {
        console.error('[PWA] Service Worker registration failed:', err);
      });
  });
}

// 2. Install Prompt Interception
window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent Chrome 76+ from automatically showing the prompt
  e.preventDefault();
  // Stash the event so it can be triggered later.
  deferredPrompt = e;

  // Reveal Install buttons if present on the page
  const installButtons = document.querySelectorAll('.btn-pwa-install');
  installButtons.forEach((btn) => {
    btn.classList.remove('hidden');
    btn.addEventListener('click', triggerPwaInstall);
  });

  const installBanner = document.getElementById('pwa-install-banner');
  if (installBanner) {
    installBanner.classList.remove('hidden');
  }
});

function triggerPwaInstall() {
  if (!deferredPrompt) {
    // If on iOS or standalone already
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    if (isIOS) {
      alert("To install Gym Tracker Pro on iOS: Tap the Share button in Safari, then tap 'Add to Home Screen'.");
    } else {
      alert("Gym Tracker Pro is already installed or your browser doesn't support direct installation. Use your browser's menu to 'Add to Home screen'.");
    }
    return;
  }

  // Show the prompt
  deferredPrompt.prompt();

  // Wait for the user to respond to the prompt
  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      console.log('[PWA] User accepted the install prompt');
      const installBanner = document.getElementById('pwa-install-banner');
      if (installBanner) installBanner.classList.add('hidden');
    } else {
      console.log('[PWA] User dismissed the install prompt');
    }
    deferredPrompt = null;
  });
}

window.addEventListener('appinstalled', () => {
  console.log('[PWA] Gym Tracker Pro was installed on the device!');
  const installBanner = document.getElementById('pwa-install-banner');
  if (installBanner) installBanner.classList.add('hidden');
  if (typeof showToast === 'function') {
    showToast('Gym Tracker Pro successfully installed! You can now launch it from your home screen.', 'success', 'PWA Installed');
  }
});
