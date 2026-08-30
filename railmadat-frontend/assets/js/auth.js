/* =========================================================
   auth.js — RailMadat Authentication

   Login via Supabase, token storage, role-based access.
   ========================================================= */

const AUTH = {
    getToken() { return localStorage.getItem('railmadat-token'); },
    getRole() { return localStorage.getItem('railmadat-role'); },
    getUserName() { return localStorage.getItem('railmadat-name'); },
    getEmail() { return localStorage.getItem('railmadat-email'); },
    isAuthenticated() { return !!this.getToken(); },

    setSession(token, role, name, email) {
        localStorage.setItem('railmadat-token', token);
        localStorage.setItem('railmadat-role', role);
        localStorage.setItem('railmadat-name', name || '');
        localStorage.setItem('railmadat-email', email || '');
    },

    clearSession() {
        localStorage.removeItem('railmadat-token');
        localStorage.removeItem('railmadat-role');
        localStorage.removeItem('railmadat-name');
        localStorage.removeItem('railmadat-email');
    },

    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    },

    requireRole(...roles) {
        if (!this.isAuthenticated()) {
            window.location.href = '/login.html';
            return false;
        }
        if (!roles.includes(this.getRole())) {
            window.location.href = '/dashboard.html';
            return false;
        }
        return true;
    },

    logout() {
        this.clearSession();
        window.location.href = '/login.html';
    }
};
