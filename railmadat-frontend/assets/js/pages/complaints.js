/* complaints.js — Complaints list page logic */
(async function() {
    if (!AUTH.requireAuth()) return;
    buildSidebarNav(AUTH.getRole());

    const tbody = document.getElementById('complaints-tbody');
    tbody.innerHTML = '<tr><td colspan="7" class="muted">Loading complaints...</td></tr>';

    try {
        // Fetch complaints from backend API
        const complaints = await apiRequest('/complaints');
        if (!complaints || !Array.isArray(complaints)) throw new Error('No data');

        if (complaints.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="muted">No complaints found.</td></tr>';
            return;
        }

        tbody.innerHTML = complaints.map(c =>
            `<tr>
                <td><strong>${c.complaint_id}</strong></td>
                <td>${formatDate(c.created_at)}</td>
                <td>${c.section_id}</td>
                <td>${c.asset_id}</td>
                <td>${statusBadge(c.status)}</td>
                <td>${priorityBadge(c.priority || 'Medium')}</td>
                <td><a href="complaint-details.html?id=${c.complaint_id}">View</a></td>
            </tr>`
        ).join('');
    } catch (err) {
        console.warn('API not available, showing demo data:', err.message);
        // Fallback to demo data
        const demoComplaints = [
            { id: 'CMP-001', date: '25 Aug 2026', section: 'S-02', asset: 'SIG-S02-01', status: 'In Progress', priority: 'Critical' },
            { id: 'CMP-002', date: '24 Aug 2026', section: 'S-01', asset: 'TRK-S01-01', status: 'Under Review', priority: 'High' },
            { id: 'CMP-003', date: '23 Aug 2026', section: 'S-03', asset: 'ELE-S03-01', status: 'Reported', priority: 'Medium' },
        ];
        tbody.innerHTML = demoComplaints.map(c =>
            `<tr>
                <td><strong>${c.id}</strong></td>
                <td>${c.date}</td>
                <td>${c.section}</td>
                <td>${c.asset}</td>
                <td>${statusBadge(c.status)}</td>
                <td>${priorityBadge(c.priority)}</td>
                <td><a href="complaint-details.html?id=${c.id}">View</a></td>
            </tr>`
        ).join('');
    }

    function formatDate(isoString) {
        if (!isoString) return '-';
        const d = new Date(isoString);
        return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    }

    function buildSidebarNav(role) {
        const navs = {
            reporting_officer: [{href:'dashboard.html',label:'Dashboard',icon:'\u25A6'},{href:'new-complaint.html',label:'Report Fault',icon:'\u271A'},{href:'complaints.html',label:'My Reports',icon:'\u25A4'},{href:'notifications.html',label:'Notifications',icon:'\uD83D\uDD14'},{href:'profile.html',label:'Profile',icon:'\u25CF'}],
            maintenance_staff: [{href:'dashboard.html',label:'Dashboard',icon:'\u25A6'},{href:'assigned-tasks.html',label:'Tasks',icon:'\u2713'},{href:'notifications.html',label:'Notifications',icon:'\uD83D\uDD14'},{href:'profile.html',label:'Profile',icon:'\u25CF'}],
            manager: [{href:'dashboard.html',label:'Dashboard',icon:'\u25A6'},{href:'complaints.html',label:'Complaints',icon:'\u26A0'},{href:'assigned-tasks.html',label:'Tasks',icon:'\u2713'},{href:'bundle-approvals.html',label:'Bundles',icon:'\u25B7'},{href:'pending-approvals.html',label:'Approvals',icon:'\u25A4'},{href:'inspections.html',label:'Inspections',icon:'\u23F3'},{href:'notifications.html',label:'Notifications',icon:'\uD83D\uDD14'},{href:'profile.html',label:'Profile',icon:'\u25CF'}],
            administrator: [{href:'dashboard.html',label:'Dashboard',icon:'\u25A6'},{href:'team-management.html',label:'Users',icon:'\u25A4'},{href:'notifications.html',label:'Notifications',icon:'\uD83D\uDD14'},{href:'profile.html',label:'Profile',icon:'\u25CF'}],
        };
        const nav = document.getElementById('sidebar-nav');
        (navs[role] || []).forEach(i => {
            const a = document.createElement('a'); a.href = i.href;
            a.className = 'nav-item' + (location.pathname.endsWith(i.href) ? ' active' : '');
            a.innerHTML = `<span class="icon">${i.icon}</span>${i.label}`;
            nav.appendChild(a);
        });
    }
})();
