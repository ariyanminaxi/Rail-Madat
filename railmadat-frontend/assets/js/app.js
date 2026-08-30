/* =========================================================
   app.js — RailMadat Shared Layout Engine
   
   Generates sidebar, topbar, theme toggle, IST clock,
   and role-based navigation for ALL authenticated pages.
   Include this script on every page after auth.js and api.js.
   ========================================================= */

(function() {
    'use strict';

    // ---- Role-based navigation maps ----
    var NAV_MAP = {
        'Administrator': [
            { href: 'dashboard.html', icon: '◪', label: 'Dashboard' },
            { href: 'complaints.html', icon: '📋', label: 'All Complaints' },
            { href: 'pending-approvals.html', icon: '✓', label: 'Pending Approvals' },
            { href: 'bundle-approvals.html', icon: '▷', label: 'Bundle Approvals' },
            { href: 'maintenance-schedule.html', icon: '📅', label: 'Maintenance Schedule' },
            { href: 'team-management.html', icon: '👥', label: 'Team Management' },
            { href: 'inspections.html', icon: '🔍', label: 'Inspector Dashboard' },
            { href: 'notifications.html', icon: '🔔', label: 'Notifications' },
            { href: 'settings.html', icon: '⚙', label: 'System Settings' },
        ],
        'Maintenance_Manager': [
            { href: 'dashboard.html', icon: '◪', label: 'Dashboard' },
            { href: 'complaints.html', icon: '📋', label: 'All Complaints' },
            { href: 'pending-approvals.html', icon: '✓', label: 'Pending Approvals' },
            { href: 'bundle-approvals.html', icon: '▷', label: 'Bundle Approvals' },
            { href: 'maintenance-schedule.html', icon: '📅', label: 'Maintenance Schedule' },
            { href: 'team-management.html', icon: '👥', label: 'Team Management' },
            { href: 'notifications.html', icon: '🔔', label: 'Notifications' },
            { href: 'settings.html', icon: '⚙', label: 'Settings' },
        ],
        'Maintenance_Staff': [
            { href: 'dashboard.html', icon: '◪', label: 'Dashboard' },
            { href: 'assigned-tasks.html', icon: '✓', label: 'Assigned Tasks' },
            { href: 'work-completion.html', icon: '📝', label: 'Work Completion' },
            { href: 'notifications.html', icon: '🔔', label: 'Notifications' },
            { href: 'settings.html', icon: '⚙', label: 'Settings' },
        ],
        'Inspector': [
            { href: 'dashboard.html', icon: '◪', label: 'Dashboard' },
            { href: 'inspections.html', icon: '🔍', label: 'Pending Inspections' },
            { href: 'notifications.html', icon: '🔔', label: 'Notifications' },
            { href: 'settings.html', icon: '⚙', label: 'Settings' },
        ],
        'Reporter': [
            { href: 'dashboard.html', icon: '◪', label: 'Dashboard' },
            { href: 'complaints.html', icon: '📋', label: 'My Complaints' },
            { href: 'new-complaint.html', icon: '✚', label: 'Report Fault' },
            { href: 'notifications.html', icon: '🔔', label: 'Notifications' },
            { href: 'settings.html', icon: '⚙', label: 'Settings' },
        ],
    };

    // ---- Theme Manager ----
    var ThemeManager = {
        getTheme: function() {
            return localStorage.getItem('railmadat-theme') || 'dark';
        },
        setTheme: function(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('railmadat-theme', theme);
            var btn = document.querySelector('.theme-toggle');
            if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
        },
        toggle: function() {
            this.setTheme(this.getTheme() === 'dark' ? 'light' : 'dark');
        },
        init: function() {
            this.setTheme(this.getTheme());
        }
    };

    // ---- IST Clock ----
    function updateClock() {
        var el = document.getElementById('ist-clock');
        if (!el) return;
        var now = new Date();
        var ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
        var h = ist.getHours(), m = ist.getMinutes(), s = ist.getSeconds();
        el.textContent = String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0') + ' IST';
    }

    // ---- Build Sidebar ----
    function buildSidebar() {
        var container = document.getElementById('sidebar-container');
        if (!container) return;

        var role = AUTH.getRole();
        var userName = AUTH.getUserName() || 'User';
        var navItems = NAV_MAP[role] || NAV_MAP['Administrator'];
        var currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';

        var html = '<aside class="sidebar" id="sidebar">';
        html += '<div class="brand"><div class="brand-icon">R</div>';
        html += '<div><h1>RailMadad</h1><span>Maintenance Coordination</span></div></div>';
        html += '<nav class="navigation" aria-label="Primary navigation">';

        navItems.forEach(function(item) {
            var isActive = item.href === currentPage;
            html += '<a href="' + item.href + '" class="nav-item' + (isActive ? ' active' : '') + '">';
            html += '<span class="icon">' + item.icon + '</span>' + item.label + '</a>';
        });

        html += '</nav>';
        html += '<div class="sidebar-footer">';
        html += '<div class="safety-badge"><span class="dot"></span> Decision Support Mode</div>';
        html += '<p>AI recommendations require human approval.</p>';
        html += '</div></aside>';

        container.innerHTML = html;
    }

    // ---- Build Topbar ----
    function buildTopbar() {
        var container = document.getElementById('topbar-container');
        if (!container) return;

        var role = AUTH.getRole();
        var userName = AUTH.getUserName() || 'User';
        var roleLabel = role ? role.replace(/_/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); }) : '';
        var initials = (userName || 'U').charAt(0).toUpperCase();
        var currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
        var pageTitle = currentPage.replace('.html', '').replace(/-/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); });

        var html = '<header class="topbar">';
        html += '<div class="topbar-left">';
        html += '<button type="button" class="sidebar-toggle" id="sidebar-toggle" aria-label="Toggle menu">☰</button>';
        html += '<div>';
        html += '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="dashboard.html">Home</a> / <span class="current">' + pageTitle + '</span></nav>';
        html += '<h2>' + pageTitle + '</h2>';
        html += '</div></div>';

        html += '<div class="topbar-actions">';
        html += '<span class="ist-clock" id="ist-clock"></span>';
        html += '<a href="notifications.html" class="notification-button" aria-label="Notifications">🔔<span class="notification-count" id="notif-count" style="display:none">0</span></a>';
        html += '<button type="button" class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">☀️</button>';
        html += '<div style="position:relative">';
        html += '<button type="button" class="user-profile" id="user-menu-btn">';
        html += '<div class="avatar">' + initials + '</div>';
        html += '<div><strong>' + userName + '</strong><span>' + roleLabel + '</span></div>';
        html += '</button>';
        html += '<div class="profile-dropdown" id="profile-dropdown">';
        html += '<div class="profile-dropdown-header"><strong>' + userName + '</strong><span>' + roleLabel + '</span></div>';
        html += '<a href="settings.html">View Profile</a>';
        html += '<button type="button" class="sign-out-button" onclick="AUTH.logout()">Sign Out</button>';
        html += '</div></div>';

        html += '</div></header>';

        container.innerHTML = html;

        // Wire up topbar events
        var toggleBtn = document.getElementById('sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() {
                document.getElementById('sidebar').classList.toggle('open');
            });
        }

        var themeBtn = document.getElementById('theme-toggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', function() { ThemeManager.toggle(); });
        }

        var menuBtn = document.getElementById('user-menu-btn');
        if (menuBtn) {
            menuBtn.addEventListener('click', function() {
                document.getElementById('profile-dropdown').classList.toggle('open');
            });
        }

        document.addEventListener('click', function(e) {
            if (!e.target.closest('.user-profile') && !e.target.closest('.profile-dropdown')) {
                var dd = document.getElementById('profile-dropdown');
                if (dd) dd.classList.remove('open');
            }
        });
    }

    // ---- Init ----
    document.addEventListener('DOMContentLoaded', function() {
        ThemeManager.init();
        buildSidebar();
        buildTopbar();
        updateClock();
        setInterval(updateClock, 1000);
    });

    // Expose for other scripts
    window.RailMadat = { ThemeManager: ThemeManager };
})();
