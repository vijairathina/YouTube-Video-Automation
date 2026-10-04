/**
 * YT Manager - REST API Client
 */

const API = {
    async get(endpoint, params = {}) {
        const url = new URL(endpoint, window.location.origin);
        Object.keys(params).forEach(k => {
            if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
                url.searchParams.append(k, params[k]);
            }
        });
        const res = await fetch(url.toString(), { headers: { 'Accept': 'application/json' } });
        return res.json();
    },

    async post(endpoint, data = {}) {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },

    getHealth: () => API.get('/api/health'),
    getStats: () => API.get('/api/dashboard/stats'),
    getUploads: (params) => API.get('/api/uploads', params),
    getPendingFiles: () => API.get('/api/files/pending'),
    getSettings: () => API.get('/api/uploader/settings'),
    saveSettings: (data) => API.post('/api/uploader/settings', data),
    triggerRetry: () => API.post('/api/uploader/retry'),
    backupDb: () => API.post('/api/database/backup')
};
