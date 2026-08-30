/* =========================================================
   dashboard.js — RailMadat Dashboard

   Role-based dashboard rendering.
   Roles: reporting_officer, maintenance_staff, manager, administrator
   ========================================================= */

(function() {
    if (!AUTH.requireAuth()) return;

    const role = AUTH.getRole();
    const name = AUTH.getUserName() || 'Officer';

    document.getElementById('welcome-name').textContent = name;
    document.getElementById('welcome-role').textContent = roleLabel(role) + (AUTH.getEmail() ? ' \u00B7 ' + AUTH.getEmail() : '');

    // Build sidebar nav based on role
    buildSidebarNav(role);

    // Render role-specific dashboard
    renderDashboard(role);
})();

function buildSidebarNav(role) {
    const navs = {
        reporting_officer: [
            { href: 'dashboard.html', label: 'Dashboard', icon: '\u25A6' },
            { href: 'new-complaint.html', label: 'Report Fault', icon: '\u271A' },
            { href: 'complaints.html', label: 'My Reports', icon: '\u25A4' },
            { href: 'notifications.html', label: 'Notifications', icon: '\uD83D\uDD14' },
            { href: 'profile.html', label: 'Profile', icon: '\u25CF' },
        ],
        maintenance_staff: [
            { href: 'dashboard.html', label: 'Dashboard', icon: '\u25A6' },
            { href: 'assigned-tasks.html', label: 'Assigned Tasks', icon: '\u2713' },
            { href: 'work-completion.html', label: 'Work Completion', icon: '\u2709' },
            { href: 'notifications.html', label: 'Notifications', icon: '\uD83D\uDD14' },
            { href: 'profile.html', label: 'Profile', icon: '\u25CF' },
        ],
        manager: [
            { href: 'dashboard.html', label: 'Dashboard', icon: '\u25A6' },
            { href: 'complaints.html', label: 'Complaints', icon: '\u26A0' },
            { href: 'assigned-tasks.html', label: 'Tasks', icon: '\u2713' },
            { href: 'bundle-approvals.html', label: 'Bundle Approvals', icon: '\u25B7' },
            { href: 'pending-approvals.html', label: 'Approval Queue', icon: '\u25A4' },
            { href: 'maintenance-schedule.html', label: 'Schedule', icon: '\u25C8' },
            { href: 'team-management.html', label: 'Teams', icon: '\u25C9' },
            { href: 'inspections.html', label: 'Inspections', icon: '\u23F3' },
            { href: 'notifications.html', label: 'Notifications', icon: '\uD83D\uDD14' },
            { href: 'profile.html', label: 'Profile', icon: '\u25CF' },
        ],
        administrator: [
            { href: 'dashboard.html', label: 'Dashboard', icon: '\u25A6' },
            { href: 'team-management.html', label: 'User Management', icon: '\u25A4' },
            { href: 'maintenance-schedule.html', label: 'Assets', icon: '\u25C8' },
            { href: 'settings.html', label: 'System Health', icon: '\u25C9' },
            { href: 'notifications.html', label: 'Notifications', icon: '\uD83D\uDD14' },
            { href: 'profile.html', label: 'Profile', icon: '\u25CF' },
        ],
    };

    const items = navs[role] || navs.reporting_officer;
    const nav = document.getElementById('sidebar-nav');
    items.forEach(item => {
        const a = document.createElement('a');
        a.href = item.href;
        a.className = 'nav-item' + (window.location.pathname.endsWith(item.href) ? ' active' : '');
        a.innerHTML = `<span class="icon">${item.icon}</span>${item.label}`;
        nav.appendChild(a);
    });
}

async function renderDashboard(role) {
    const container = document.getElementById('dashboard-content');
    container.innerHTML = '<p class="muted">Loading dashboard data...</p>';

    try {
        // Fetch stats from backend API
        const stats = await apiRequest('/dashboard/stats');
        if (!stats) throw new Error('No data received');

        // Build role-specific cards from API data
        let cards = [];

        switch (role) {
            case 'reporting_officer':
                cards = [
                    { label: 'My Complaints', value: stats.my_complaints || 0 },
                    { label: 'Open Reports', value: stats.open_complaints || 0 },
                    { label: 'In Progress', value: stats.in_progress || 0 },
                    { label: 'Completed', value: stats.completed || 0 },
                ];
                break;
            case 'maintenance_staff':
                cards = [
                    { label: 'My Tasks', value: stats.my_tasks || 0 },
                    { label: 'Critical Tasks', value: stats.critical_tasks || 0 },
                    { label: 'In Progress', value: stats.in_progress || 0 },
                    { label: 'Total Tasks', value: stats.total_tasks || 0 },
                ];
                break;
            case 'manager':
            case 'Maintenance Manager':
                cards = [
                    { label: 'Critical Tasks', value: stats.critical_tasks || 0 },
                    { label: 'Pending Approvals', value: stats.pending_approvals || 0 },
                    { label: 'Overdue Tasks', value: stats.overdue_tasks || 0 },
                    { label: 'Total Complaints', value: stats.total_complaints || 0 },
                ];
                break;
            case 'administrator':
            case 'Administrator':
                cards = [
                    { label: 'Total Complaints', value: stats.total_complaints || 0 },
                    { label: 'Total Tasks', value: stats.total_tasks || 0 },
                    { label: 'Critical Tasks', value: stats.critical_tasks || 0 },
                    { label: 'Failed Audits', value: stats.pending_audits || 0 },
                ];
                break;
            default:
                cards = [
                    { label: 'Total Complaints', value: stats.total_complaints || 0 },
                    { label: 'Open Reports', value: stats.open_complaints || 0 },
                    { label: 'In Progress', value: stats.in_progress || 0 },
                    { label: 'Completed', value: stats.completed || 0 },
                ];
        }

        let html = '<div class="cards-grid">';
        cards.forEach(c => {
            html += `<div class="card"><span class="card-label">${c.label}</span><span class="card-value">${c.value}</span></div>`;
        });
        html += '</div>';

        html += `<div class="panel"><p class="muted">Dashboard data loaded from backend API.</p></div>`;
        container.innerHTML = html;

    } catch (err) {
        console.warn('API not available, showing demo data:', err.message);
        // Fallback to demo data if backend is not running
        const dashboards = {
            reporting_officer: {
                cards: [
                    { label: 'Open Reports', value: 3 },
                    { label: 'Under Review', value: 2 },
                    { label: 'In Progress', value: 1 },
                    { label: 'Resolved', value: 5 },
                ],
                message: 'Demo mode — Connect backend API for live data.'
            },
            maintenance_staff: {
                cards: [
                    { label: 'Assigned Tasks', value: 4 },
                    { label: 'Critical Tasks', value: 1 },
                    { label: 'Work in Progress', value: 2 },
                    { label: 'Interrupted', value: 0 },
                ],
                message: 'Demo mode — Connect backend API for live data.'
            },
            manager: {
                cards: [
                    { label: 'Critical Tasks', value: 2 },
                    { label: 'Overdue Tasks', value: 1 },
                    { label: 'Pending Verification', value: 3 },
                    { label: 'Blocks Awaiting Approval', value: 2 },
                ],
                message: 'Demo mode — Connect backend API for live data.'
            },
            administrator: {
                cards: [
                    { label: 'Active Users', value: 12 },
                    { label: 'Total Complaints', value: 25 },
                    { label: 'Total Tasks', value: 18 },
                    { label: 'Failed Logins', value: 0 },
                ],
                message: 'Demo mode — Connect backend API for live data.'
            },
        };

        const data = dashboards[role] || dashboards.reporting_officer;
        let html = '<div class="cards-grid">';
        data.cards.forEach(c => {
            html += `<div class="card"><span class="card-label">${c.label}</span><span class="card-value">${c.value}</span></div>`;
        });
        html += '</div>';
        html += `<div class="panel"><p class="muted">${data.message}</p></div>`;
        container.innerHTML = html;
    }
}
