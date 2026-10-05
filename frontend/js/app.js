/**
 * YT Manager - Interactive Glass Controller
 */

let state = {
    uploads: [],
    pendingFiles: [],
    currentPage: 1,
    limit: 25,
    search: '',
    statusFilter: ''
};

document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
    setupEventListeners();
    setupHashNavigation();
    setInterval(pollStatus, 5000); // 5-second live status polling
});

async function initApp() {
    await checkHealth();
    await loadStats();
    await loadUploads();
    await loadPendingFiles();
    await loadSettings();
}

async function checkHealth() {
    try {
        const h = await API.getHealth();
        
        // Desktop Badge
        const badge = document.getElementById('healthBadge');
        if (badge) {
            badge.innerText = `● ${h.service} (${h.youtube_auth})`;
            badge.className = h.status === 'Online' ? 'glass-badge badge-emerald' : 'glass-badge badge-coral';
        }

        // Mobile Top Header Badge
        const mobileBadge = document.getElementById('mobileHealthBadge');
        if (mobileBadge) {
            mobileBadge.innerText = h.status === 'Online' ? '● Online' : '● Offline';
            mobileBadge.className = h.status === 'Online' ? 'glass-badge badge-emerald' : 'glass-badge badge-coral';
        }
    } catch (e) {
        console.warn('Health check error:', e);
    }
}

async function loadStats() {
    try {
        const s = await API.getStats();
        const totalEl = document.getElementById('statTotalUploads');
        const successEl = document.getElementById('statSuccess');
        const failedEl = document.getElementById('statFailed');
        const workerStatus = document.getElementById('statWorkerStatus');
        const folderDisplay = document.getElementById('activeFolderDisplay');

        if (totalEl) totalEl.innerText = s.total_uploads ?? 0;
        if (successEl) successEl.innerText = s.success_count ?? 0;
        if (failedEl) failedEl.innerText = s.failed_count ?? 0;
        if (workerStatus) workerStatus.innerText = s.worker_status || 'Idle';
        if (folderDisplay) folderDisplay.innerText = s.current_folder || '.';
    } catch (e) {
        console.warn('Error loading stats:', e);
    }
}

async function pollStatus() {
    try {
        const s = await API.getStats();
        const statusEl = document.getElementById('statWorkerStatus');
        if (statusEl) statusEl.innerText = s.worker_status || 'Idle';
    } catch (e) {}
}

async function loadUploads() {
    const tableBody = document.getElementById('uploadsTableBody');
    if (!tableBody) return;

    try {
        const res = await API.getUploads({
            page: state.currentPage,
            limit: state.limit,
            status: state.statusFilter,
            search: state.search
        });

        state.uploads = res.items || [];
        renderUploadsTable(state.uploads);
        renderPagination(res.total, res.page, res.limit);
    } catch (e) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--accent-coral); padding: 1.5rem;">Failed to load upload history.</td></tr>';
    }
}

function renderUploadsTable(items) {
    const tableBody = document.getElementById('uploadsTableBody');
    if (!tableBody) return;

    if (!items.length) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">No upload history found.</td></tr>';
        return;
    }

    tableBody.innerHTML = items.map(u => {
        const statusClass = u.status === 'Success' ? 'status-success' : 'status-failed';
        const ytLink = u.video_id && u.video_id !== 'N/A' 
            ? `<a href="https://youtu.be/${u.video_id}" target="_blank" style="color: var(--accent-amber); text-decoration: none;"><i class="fab fa-youtube"></i> ${u.video_id}</a>`
            : '<span style="color: var(--text-muted);">N/A</span>';

        return `
            <tr>
                <td style="color: var(--text-secondary); font-family: monospace; font-size: 0.8rem; white-space: nowrap;">${u.uploaded_at || 'Just now'}</td>
                <td style="font-weight: 600; color: var(--text-primary); word-break: break-all;">${u.filename}</td>
                <td style="white-space: nowrap;">${ytLink}</td>
                <td><span class="status-pill ${statusClass}">${u.status}</span></td>
                <td style="color: var(--text-muted); font-size: 0.8rem; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${u.error_details || 'Uploaded successfully'}">
                    ${u.error_details || 'Uploaded successfully'}
                </td>
            </tr>
        `;
    }).join('');
}

function renderPagination(total, page, limit) {
    const container = document.getElementById('paginationControls');
    if (!container) return;
    const totalPages = Math.ceil(total / limit) || 1;
    container.innerHTML = `
        <span style="font-size: 0.85rem; color: var(--text-secondary);">Showing Page ${page} of ${totalPages} (${total} total)</span>
        <div style="display: flex; gap: 0.5rem;">
            <button class="glass-btn" ${page <= 1 ? 'disabled style="opacity:0.4; cursor:not-allowed;"' : ''} onclick="changePage(${page - 1})">Previous</button>
            <button class="glass-btn" ${page >= totalPages ? 'disabled style="opacity:0.4; cursor:not-allowed;"' : ''} onclick="changePage(${page + 1})">Next</button>
        </div>
    `;
}

function changePage(p) {
    state.currentPage = p;
    loadUploads();
}

async function loadPendingFiles() {
    try {
        const res = await API.getPendingFiles();
        state.pendingFiles = res.files || [];
        const countBadge = document.getElementById('pendingFilesCount');
        if (countBadge) countBadge.innerText = `${state.pendingFiles.length} detected`;
    } catch (e) {
        console.warn('Error loading pending files:', e);
    }
}

async function loadSettings() {
    try {
        const res = await API.getSettings();
        if (res.success && res.config) {
            const c = res.config;
            document.getElementById('settingFolder').value = c.folder_path || '';
            document.getElementById('settingIsSmb').checked = c.is_smb;
            document.getElementById('settingSmbShare').value = c.smb_share || '';
            document.getElementById('settingSmbUser').value = c.smb_username || '';
            document.getElementById('settingInterval').value = c.upload_interval_mins || 45;
            document.getElementById('settingRetry').value = c.retry_interval_hours || 24;
            document.getElementById('settingEnabled').checked = c.upload_enabled;
            toggleSmbFields();
        }
    } catch (e) {
        console.warn('Error loading settings:', e);
    }
}

function toggleSmbFields() {
    const isSmb = document.getElementById('settingIsSmb').checked;
    const box = document.getElementById('smbFieldsBox');
    if (box) box.style.display = isSmb ? 'grid' : 'none';
}

function switchView(viewName) {
    // Update active state in mobile bottom navigation
    document.querySelectorAll('.mobile-nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll(`.mobile-nav-item[href="#${viewName}"]`).forEach(el => el.classList.add('active'));

    // Update active state in desktop sidebar navigation
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    document.querySelectorAll(`.nav-link[href="#${viewName}"]`).forEach(el => el.classList.add('active'));

    // Smooth scroll to view section
    const targetId = viewName === 'dashboard' ? 'dashboardSection' : 'historySection';
    const targetEl = document.getElementById(targetId);
    if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function setupHashNavigation() {
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.replace('#', '') || 'dashboard';
        if (hash === 'settings') {
            openModal('settingsModal');
        } else if (hash === 'dashboard' || hash === 'history') {
            switchView(hash);
        }
    });

    if (window.location.hash) {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'settings') openModal('settingsModal');
        else if (hash === 'dashboard' || hash === 'history') switchView(hash);
    }
}

async function refreshAllData() {
    await checkHealth();
    await loadStats();
    await loadPendingFiles();
    await loadUploads();
}

function setupEventListeners() {
    let timeout;
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                state.search = e.target.value.trim();
                state.currentPage = 1;
                loadUploads();
            }, 300);
        });
    }

    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', (e) => {
            state.statusFilter = e.target.value;
            state.currentPage = 1;
            loadUploads();
        });
    }

    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                folder_path: document.getElementById('settingFolder').value,
                is_smb: document.getElementById('settingIsSmb').checked,
                smb_share: document.getElementById('settingSmbShare').value,
                smb_username: document.getElementById('settingSmbUser').value,
                smb_password: document.getElementById('settingSmbPass').value,
                upload_interval_mins: parseInt(document.getElementById('settingInterval').value),
                retry_interval_hours: parseInt(document.getElementById('settingRetry').value),
                upload_enabled: document.getElementById('settingEnabled').checked
            };
            await API.saveSettings(data);
            alert('Settings saved successfully!');
            closeModal('settingsModal');
            await loadStats();
            await loadPendingFiles();
        });
    }

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal('settingsModal');
        }
    });
}

async function triggerRetry() {
    await API.triggerRetry();
    alert('Immediate upload scan & retry pushed!');
    await loadStats();
    await loadPendingFiles();
    await loadUploads();
}

async function triggerBackup() {
    const res = await API.backupDb();
    if (res.success) {
        alert('Database snapshot created successfully at:\n' + res.backup_file);
    } else {
        alert('Backup error: ' + res.error);
    }
}

function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('active');
}

function handleOverlayClick(event, id) {
    if (event.target && event.target.id === id) {
        closeModal(id);
    }
}
