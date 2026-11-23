/**
 * LIV-SENSI AI – SHELL NAVIGATION & MOBILE PWA CONTROLLER
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Sidebar Collapse / Expand Toggle & Mobile Drawer
  const sidebar = document.querySelector('.hv-sidebar');
  const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
  const backdrop = document.querySelector('.sidebar-backdrop');

  if (sidebar && btnToggleSidebar) {
    // If mobile or tablet, remove collapsed state completely
    if (window.innerWidth <= 1024) {
      sidebar.classList.remove('collapsed');
    } else {
      // Restore saved state for desktop
      const isCollapsed = localStorage.getItem('hv_sidebar_collapsed') === 'true';
      if (isCollapsed) sidebar.classList.add('collapsed');
    }

    btnToggleSidebar.addEventListener('click', () => {
      if (window.innerWidth <= 1024) {
        // Mobile / Tablet Drawer Toggle
        sidebar.classList.toggle('open');
        if (backdrop) backdrop.classList.toggle('active');
      } else {
        // Desktop Collapse
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('hv_sidebar_collapsed', sidebar.classList.contains('collapsed'));
      }
    });
  }

  // Close mobile drawer when backdrop, close button, or any sidebar item is tapped
  if (backdrop && sidebar) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.remove('active');
    });
  }

  document.querySelectorAll('.btn-close-sidebar-mobile').forEach(btn => {
    btn.addEventListener('click', () => {
      if (sidebar) sidebar.classList.remove('open');
      if (backdrop) backdrop.classList.remove('active');
    });
  });

  document.querySelectorAll('.hv-sidebar-item').forEach(item => {
    item.addEventListener('click', () => {
      if (window.innerWidth <= 1024 && sidebar) {
        sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('active');
      }
    });
  });

  // 2. Mobile Menu Toggle (Landing page if present)
  const btnMobileMenu = document.getElementById('btn-mobile-menu');
  const mobileDrawer = document.getElementById('mobile-drawer');
  const mobileDrawerClose = document.getElementById('btn-close-mobile');

  if (btnMobileMenu && mobileDrawer) {
    btnMobileMenu.addEventListener('click', () => {
      mobileDrawer.classList.remove('hidden');
    });
  }

  if (mobileDrawerClose && mobileDrawer) {
    mobileDrawerClose.addEventListener('click', () => {
      mobileDrawer.classList.add('hidden');
    });
  }

  // 3. Highlight Active Navigation Item & Mobile Bottom Tabs
  const currentPath = window.location.pathname.toLowerCase();
  const navLinks = document.querySelectorAll('.hv-sidebar-item, .hv-nav-link, .mobile-nav-tab');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    const cleanHref = href.replace('../', '').toLowerCase();
    if (
      (cleanHref === 'index.html' && (currentPath === '/' || currentPath.endsWith('/index.html') || currentPath.endsWith('/ui-preview/'))) ||
      (cleanHref !== 'index.html' && currentPath.includes(cleanHref))
    ) {
      link.classList.add('active');
    }
  });

  // 4. Modal Triggers
  document.querySelectorAll('[data-modal-target]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = trigger.getAttribute('data-modal-target');
      const modal = document.getElementById(targetId);
      if (modal) modal.classList.remove('hidden');
    });
  });

  document.querySelectorAll('.btn-close-modal, .modal-overlay').forEach(closer => {
    closer.addEventListener('click', (e) => {
      if (e.target === closer || closer.classList.contains('btn-close-modal')) {
        const modal = closer.closest('.modal-overlay');
        if (modal) modal.classList.add('hidden');
      }
    });
  });

  // 5. PWA Service Worker Registration
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(err => {
      console.log('PWA ServiceWorker notice:', err);
    });
  }

  // 6. PWA Install Prompt Listener
  let deferredPrompt;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const installBtn = document.getElementById('btn-pwa-install');
    if (installBtn) {
      installBtn.style.display = 'inline-flex';
      installBtn.addEventListener('click', () => {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('User installed Liv-Sensi PWA');
          }
          deferredPrompt = null;
        });
      });
    }
  });
});
