/* =========================================================
   utils.js — RailMadat Utility Functions

   Date formatting (IST), validators, DOM helpers.
   ========================================================= */

/* ---- IST Date Formatting ---- */

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function formatIST(value) {
    if (!value) return 'Not available yet.';
    const date = value instanceof Date ? value : new Date(value);
    if (isNaN(date.getTime())) return 'Not available yet.';
    const ist = new Date(date.getTime() + (5.5 * 60 - date.getTimezoneOffset()) * 60000);
    return `${String(ist.getDate()).padStart(2,'0')} ${MONTHS[ist.getMonth()]} ${ist.getFullYear()}, ${String(ist.getHours()).padStart(2,'0')}:${String(ist.getMinutes()).padStart(2,'0')} IST`;
}

function formatISTClock(date) {
    date = date || new Date();
    const ist = new Date(date.getTime() + (5.5 * 60 - date.getTimezoneOffset()) * 60000);
    return `${String(ist.getHours()).padStart(2,'0')}:${String(ist.getMinutes()).padStart(2,'0')}:${String(ist.getSeconds()).padStart(2,'0')} IST`;
}

function toTitleCase(s) {
    if (!s) return '';
    return s.split(/[_\s]+/).filter(Boolean).map(w => w[0].toUpperCase() + w.slice(1)).join(' ');
}

function initials(name) {
    if (!name) return '?';
    return name.split(' ').filter(Boolean).map(p => p[0]).join('').substring(0, 2).toUpperCase();
}

function truncate(text, max) {
    max = max || 80;
    if (!text || text.length <= max) return text || '';
    return text.slice(0, max - 1) + '\u2026';
}

/* ---- DOM Helpers ---- */

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function el(tag, attrs, ...children) {
    const e = document.createElement(tag);
    if (attrs) Object.entries(attrs).forEach(([k, v]) => {
        if (k === 'className') e.className = v;
        else if (k === 'onclick') e.onclick = v;
        else if (k.startsWith('on')) e.addEventListener(k.slice(2).toLowerCase(), v);
        else e.setAttribute(k, v);
    });
    children.forEach(c => {
        if (typeof c === 'string') e.appendChild(document.createTextNode(c));
        else if (c) e.appendChild(c);
    });
    return e;
}

/* ---- Badge Helpers ---- */

const STATUS_META = {
    'Complaint Filed': { icon: '\u2709', tone: 'grey' },
    'Under Review': { icon: '\u23F3', tone: 'blue' },
    'Classified': { icon: '\u2611', tone: 'blue' },
    'Waiting for Block': { icon: '\u23F3', tone: 'blue' },
    'Scheduled': { icon: '\u{1F4C5}', tone: 'blue' },
    'In Progress': { icon: '\u2699', tone: 'orange' },
    'Completed': { icon: '\u2713', tone: 'green' },
    'Interrupted': { icon: '\u26A0', tone: 'red' },
    'Awaiting Materials': { icon: '\u23F3', tone: 'orange' },
    'Deferred': { icon: '\u23F8', tone: 'grey' },
    'Cancelled': { icon: '\u2715', tone: 'grey' },
    'Emergency': { icon: '\u26A0', tone: 'emergency' },
};

function statusBadge(status) {
    const m = STATUS_META[status] || { icon: '\u25CF', tone: 'grey' };
    return `<span class="badge badge-${m.tone}">${m.icon} ${status || 'Unknown'}</span>`;
}

const PRIORITY_META = {
    Low: { icon: '\u25CB', tone: 'grey' },
    Medium: { icon: '\u25D1', tone: 'blue' },
    High: { icon: '\u25CF', tone: 'orange' },
    Critical: { icon: '\u2757', tone: 'red' },
    Emergency: { icon: '\u26A0', tone: 'emergency' },
};

function priorityBadge(p) {
    const m = PRIORITY_META[p] || { icon: '\u25CF', tone: 'grey' };
    return `<span class="badge badge-${m.tone}">${m.icon} ${p || 'Unknown'}</span>`;
}
