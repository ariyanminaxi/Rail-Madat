/* =========================================================
   theme.js — RailMadat Dark/Light Theme Toggle

   Persists preference in localStorage.
   ========================================================= */

const ThemeManager = {
    init() {
        const saved = localStorage.getItem('railmadat-theme') || 'light';
        this.setTheme(saved);
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('railmadat-theme', theme);
        this.updateIcon(theme);
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        this.setTheme(current === 'dark' ? 'light' : 'dark');
    },

    updateIcon(theme) {
        const btn = document.querySelector('.theme-toggle');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
            btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
        }
    }
};

document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
