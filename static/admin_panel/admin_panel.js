(() => {
    const state = {
        resource: null,
        page: 1,
        pageSize: 20,
        search: '',
        ordering: '',
        filters: [],
        count: 0,
        next: null,
        previous: null,
        cache: {},
        selectedId: null,
    };

    const resources = [
        { id: 'users', label: 'Пользователи', endpoint: '/api/users/' },
        { id: 'specialties', label: 'Специальности', endpoint: '/api/specialties/' },
        { id: 'competencies', label: 'Компетенции', endpoint: '/api/competencies/' },
        { id: 'user-competencies', label: 'Компетенции пользователей', endpoint: '/api/user-competencies/' },
        { id: 'competency-assessments', label: 'Оценки компетенций', endpoint: '/api/competency-assessments/' },
        { id: 'courses', label: 'Курсы', endpoint: '/api/courses/' },
        { id: 'course-materials', label: 'Материалы курсов', endpoint: '/api/course-materials/' },
        { id: 'enrollments', label: 'Зачисления', endpoint: '/api/enrollments/' },
        { id: 'tasks', label: 'Задания', endpoint: '/api/tasks/' },
        { id: 'task-assignments', label: 'Назначения заданий', endpoint: '/api/task-assignments/' },
        { id: 'task-submissions', label: 'Ответы на задания', endpoint: '/api/task-submissions/' },
        { id: 'tests', label: 'Тесты', endpoint: '/api/tests/' },
        { id: 'questions', label: 'Вопросы', endpoint: '/api/questions/' },
        { id: 'answers', label: 'Ответы', endpoint: '/api/answers/' },
        { id: 'results', label: 'Результаты', endpoint: '/api/results/' },
        { id: 'feedback', label: 'Отзывы', endpoint: '/api/feedback/' },
        { id: 'task-reviews', label: 'Проверки заданий', endpoint: '/api/task-reviews/' },
        { id: 'audit-logs', label: 'Журнал аудита', endpoint: '/api/audit-logs/' },
        { id: 'training-events', label: 'События обучения', endpoint: '/api/training-events/' },
        { id: 'dashboards', label: 'Дашборды', endpoint: '/api/dashboards/' },
        { id: 'reports', label: 'Отчёты', endpoint: '/api/reports/' },
        { id: 'report-exports', label: 'Экспорт отчётов', endpoint: '/api/report-exports/' },
        { id: 'backups', label: 'Резервные копии', endpoint: '/api/backups/' },
    ];

    const elements = {
        resourceList: document.getElementById('resourceList'),
        resourceTitle: document.getElementById('resourceTitle'),
        resourceMeta: document.getElementById('resourceMeta'),
        searchInput: document.getElementById('searchInput'),
        orderingInput: document.getElementById('orderingInput'),
        pageSizeInput: document.getElementById('pageSizeInput'),
        applyFilters: document.getElementById('applyFilters'),
        resetFilters: document.getElementById('resetFilters'),
        addFilterRow: document.getElementById('addFilterRow'),
        filterRows: document.getElementById('filterRows'),
        dataTable: document.getElementById('dataTable'),
        paginationText: document.getElementById('paginationText'),
        prevPage: document.getElementById('prevPage'),
        nextPage: document.getElementById('nextPage'),
        createBtn: document.getElementById('createBtn'),
        refreshBtn: document.getElementById('refreshBtn'),
        backupBtn: document.getElementById('backupBtn'),
        restoreBtn: document.getElementById('restoreBtn'),
        restoreFile: document.getElementById('restoreFile'),
        restoreKeyInput: document.getElementById('restoreKeyInput'),
        modal: document.getElementById('formModal'),
        modalTitle: document.getElementById('modalTitle'),
        modalBody: document.getElementById('modalBody'),
        modalSave: document.getElementById('modalSave'),
        modalCancel: document.getElementById('modalCancel'),
        notice: document.getElementById('notice'),
    };

    const tokens = window.__TOKENS__ || {};
    const tokenStore = {
        access: tokens.access || localStorage.getItem('admin_access') || '',
        refresh: tokens.refresh || localStorage.getItem('admin_refresh') || '',
        set(access, refresh) {
            if (access) {
                this.access = access;
                localStorage.setItem('admin_access', access);
            }
            if (refresh) {
                this.refresh = refresh;
                localStorage.setItem('admin_refresh', refresh);
            }
        },
        clear() {
            this.access = '';
            this.refresh = '';
            localStorage.removeItem('admin_access');
            localStorage.removeItem('admin_refresh');
        },
    };

    if (tokens.access || tokens.refresh) {
        tokenStore.set(tokens.access, tokens.refresh);
    }

    const restoreKeyStore = {
        key: localStorage.getItem('restore_key') || '',
        set(value) {
            this.key = value || '';
            if (this.key) {
                localStorage.setItem('restore_key', this.key);
            } else {
                localStorage.removeItem('restore_key');
            }
        },
    };

    if (elements.restoreKeyInput) {
        elements.restoreKeyInput.value = restoreKeyStore.key;
        elements.restoreKeyInput.addEventListener('input', (event) => {
            restoreKeyStore.set(event.target.value.trim());
        });
    }

    function showNotice(message, isError = false) {
        if (!elements.notice) return;
        elements.notice.textContent = message;
        elements.notice.classList.toggle('error', isError);
        elements.notice.style.display = message ? 'block' : 'none';
    }

    async function refreshToken() {
        if (!tokenStore.refresh) return false;
        const response = await fetch('/api/auth/token/refresh/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: tokenStore.refresh }),
        });
        if (!response.ok) {
            tokenStore.clear();
            return false;
        }
        const data = await response.json();
        tokenStore.set(data.access, data.refresh || tokenStore.refresh);
        return true;
    }

    async function apiFetch(url, options = {}, retry = true) {
        const headers = options.headers || {};
        if (tokenStore.access) {
            headers.Authorization = `Bearer ${tokenStore.access}`;
        }
        if (restoreKeyStore.key && url.startsWith('/api/backups')) {
            headers['X-Restore-Key'] = restoreKeyStore.key;
        }
        options.headers = headers;

        const response = await fetch(url, options);
        if (response.status === 401 && retry) {
            const refreshed = await refreshToken();
            if (refreshed) {
                return apiFetch(url, options, false);
            }
        }
        return response;
    }

    function buildQuery() {
        const params = new URLSearchParams();
        if (state.search) params.set('search', state.search);
        if (state.ordering) params.set('ordering', state.ordering);
        if (state.page) params.set('page', state.page);
        if (state.pageSize) params.set('page_size', state.pageSize);
        state.filters.forEach((filter) => {
            if (filter.field && filter.value !== '') {
                params.set(filter.field, filter.value);
            }
        });
        return params.toString();
    }

    function updateMeta() {
        const totalPages = state.pageSize ? Math.ceil(state.count / state.pageSize) : 1;
        elements.paginationText.textContent = `Страница ${state.page} из ${totalPages || 1} — записей: ${state.count}`;
        elements.prevPage.disabled = !state.previous;
        elements.nextPage.disabled = !state.next;
    }

    function renderTable(items) {
        elements.dataTable.innerHTML = '';
        if (!items || items.length === 0) {
            const empty = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 99;
            cell.textContent = 'Нет данных для этого ресурса.';
            empty.appendChild(cell);
            elements.dataTable.appendChild(empty);
            return;
        }

        const hiddenColumns = new Set(['score_color']);
        const columns = Object.keys(items[0]).filter((col) => !hiddenColumns.has(col));
        const thead = document.createElement('thead');
        const headRow = document.createElement('tr');
        columns.forEach((col) => {
            const th = document.createElement('th');
            th.textContent = col;
            headRow.appendChild(th);
        });
        const actionTh = document.createElement('th');
        actionTh.textContent = 'Действия';
        headRow.appendChild(actionTh);
        thead.appendChild(headRow);
        elements.dataTable.appendChild(thead);

        const tbody = document.createElement('tbody');
        items.forEach((item) => {
            const row = document.createElement('tr');
            columns.forEach((col) => {
                const td = document.createElement('td');
                const value = item[col];
                if (state.resource && state.resource.id === 'results' && col === 'score' && value !== null && value !== undefined) {
                    td.textContent = `${value}%`;
                    const color = item.score_color;
                    if (color) td.classList.add(`score-${color}`);
                } else if (Array.isArray(value)) {
                    td.textContent = `${value.length} элементов`;
                } else if (value && typeof value === 'object') {
                    const text = JSON.stringify(value);
                    td.textContent = text.length > 120 ? `${text.slice(0, 120)}...` : text;
                } else {
                    td.textContent = value === null ? '' : value;
                }
                row.appendChild(td);
            });

            const actionsTd = document.createElement('td');
            const actions = document.createElement('div');
            actions.className = 'row-actions';
            if (state.resource && state.resource.id === 'backups') {
                const downloadBtn = document.createElement('button');
                downloadBtn.className = 'secondary';
                downloadBtn.textContent = 'Скачать';
                downloadBtn.addEventListener('click', () => downloadBackup(item));
                const restoreBtn = document.createElement('button');
                restoreBtn.className = 'secondary';
                restoreBtn.textContent = 'Восстановить';
                restoreBtn.addEventListener('click', () => restoreBackup(item));
                actions.appendChild(downloadBtn);
                actions.appendChild(restoreBtn);
            } else {
                const editBtn = document.createElement('button');
                editBtn.className = 'secondary';
                editBtn.textContent = 'Редактировать';
                editBtn.addEventListener('click', () => openForm('edit', item));
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'secondary';
                deleteBtn.textContent = 'Удалить';
                deleteBtn.addEventListener('click', () => removeItem(item));
                actions.appendChild(editBtn);
                actions.appendChild(deleteBtn);
            }
            actionsTd.appendChild(actions);
            row.appendChild(actionsTd);
            tbody.appendChild(row);
        });
        elements.dataTable.appendChild(tbody);
    }

    function renderFilters() {
        elements.filterRows.innerHTML = '';
        state.filters.forEach((filter, idx) => {
            const row = document.createElement('div');
            row.className = 'filter-row';
            const fieldInput = document.createElement('input');
            fieldInput.placeholder = 'Поле (например, status, role)';
            fieldInput.value = filter.field;
            const valueInput = document.createElement('input');
            valueInput.placeholder = 'Значение';
            valueInput.value = filter.value;
            const removeBtn = document.createElement('button');
            removeBtn.className = 'secondary';
            removeBtn.textContent = 'Удалить';
            removeBtn.addEventListener('click', () => {
                state.filters.splice(idx, 1);
                renderFilters();
            });
            fieldInput.addEventListener('input', (e) => {
                filter.field = e.target.value.trim();
            });
            valueInput.addEventListener('input', (e) => {
                filter.value = e.target.value.trim();
            });
            row.appendChild(fieldInput);
            row.appendChild(valueInput);
            row.appendChild(removeBtn);
            elements.filterRows.appendChild(row);
        });
    }

    async function fetchList() {
        if (!state.resource) return;
        showNotice('');
        const query = buildQuery();
        const url = query ? `${state.resource.endpoint}?${query}` : state.resource.endpoint;
        const response = await apiFetch(url);
        const data = await response.json();
        if (!response.ok) {
            const message = data?.error?.message || 'Не удалось загрузить данные.';
            showNotice(message, true);
            return;
        }
        const items = data.results || data;
        state.count = data.count ?? items.length;
        state.next = data.next || null;
        state.previous = data.previous || null;
        renderTable(items);
        updateMeta();
    }

    async function getMetadata(detail = false) {
        if (!state.resource) return {};
        const cacheKey = `${state.resource.id}-${detail ? 'detail' : 'list'}`;
        if (state.cache[cacheKey]) return state.cache[cacheKey];
        const url = detail && state.selectedId ? `${state.resource.endpoint}${state.selectedId}/` : state.resource.endpoint;
        const response = await apiFetch(url, { method: 'OPTIONS' });
        if (!response.ok) return {};
        const data = await response.json();
        state.cache[cacheKey] = data;
        return data;
    }

    function buildForm(fields, data = {}) {
        const form = document.createElement('form');
        form.id = 'resourceForm';
        const grid = document.createElement('div');
        grid.className = 'form-grid';
        Object.entries(fields).forEach(([name, config]) => {
            if (config.read_only) return;
            const field = document.createElement('div');
            field.className = 'form-field';
            const label = document.createElement('label');
            label.textContent = config.label || name;
            field.appendChild(label);

            let input;
            const type = config.type || 'string';
            if (config.choices) {
                input = document.createElement('select');
                const blank = document.createElement('option');
                blank.value = '';
                blank.textContent = '---';
                input.appendChild(blank);
                config.choices.forEach((choice) => {
                    const option = document.createElement('option');
                    option.value = choice.value;
                    option.textContent = choice.display_name;
                    input.appendChild(option);
                });
            } else if (type === 'boolean') {
                input = document.createElement('input');
                input.type = 'checkbox';
            } else if (type === 'integer' || type === 'number' || type === 'decimal') {
                input = document.createElement('input');
                input.type = 'number';
            } else if (config.format === 'date') {
                input = document.createElement('input');
                input.type = 'date';
            } else if (config.format === 'date-time') {
                input = document.createElement('input');
                input.type = 'datetime-local';
            } else if (type === 'file' || config.format === 'binary') {
                input = document.createElement('input');
                input.type = 'file';
            } else if (config.max_length && config.max_length > 255) {
                input = document.createElement('textarea');
            } else {
                input = document.createElement('input');
                input.type = 'text';
            }

            input.name = name;
            if (config.required) {
                input.required = true;
            }

            if (type === 'boolean') {
                input.checked = Boolean(data[name]);
            } else if (data[name] !== undefined && data[name] !== null && input.type !== 'file') {
                input.value = data[name];
            }

            field.appendChild(input);
            grid.appendChild(field);
        });
        form.appendChild(grid);
        return form;
    }

    async function openForm(mode, item = {}) {
        state.selectedId = item.id || null;
        const metadata = await getMetadata(Boolean(state.selectedId));
        const actions = metadata.actions || {};
        const fields = mode === 'edit' ? actions.PUT || actions.PATCH || actions.POST || {} : actions.POST || {};
        elements.modalTitle.textContent = mode === 'edit' ? 'Редактирование записи' : 'Создание записи';
        elements.modalBody.innerHTML = '';
        const form = buildForm(fields, item);
        elements.modalBody.appendChild(form);
        elements.modal.dataset.mode = mode;
        elements.modal.classList.add('active');
    }

    async function submitForm() {
        const form = document.getElementById('resourceForm');
        if (!form) return;
        const mode = elements.modal.dataset.mode;
        const isEdit = mode === 'edit';
        const url = isEdit ? `${state.resource.endpoint}${state.selectedId}/` : state.resource.endpoint;
        const method = isEdit ? 'PUT' : 'POST';

        const inputs = Array.from(form.elements).filter((el) => el.name);
        const hasFile = inputs.some((el) => el.type === 'file' && el.files.length);

        let body;
        let headers = {};
        if (hasFile) {
            body = new FormData();
            inputs.forEach((el) => {
                if (el.type === 'checkbox') {
                    body.append(el.name, el.checked);
                } else if (el.type === 'file') {
                    if (el.files.length) body.append(el.name, el.files[0]);
                } else if (el.value !== '') {
                    body.append(el.name, el.value);
                }
            });
        } else {
            const payload = {};
            inputs.forEach((el) => {
                if (el.type === 'checkbox') {
                    payload[el.name] = el.checked;
                } else if (el.value !== '') {
                    payload[el.name] = el.value;
                }
            });
            body = JSON.stringify(payload);
            headers['Content-Type'] = 'application/json';
        }

        const response = await apiFetch(url, { method, headers, body });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const message = data?.error?.message || 'Не удалось сохранить.';
            showNotice(message, true);
            return;
        }
        elements.modal.classList.remove('active');
        await fetchList();
        showNotice('Сохранено.');
    }

    async function removeItem(item) {
        if (!confirm('Удалить эту запись?')) return;
        const url = `${state.resource.endpoint}${item.id}/`;
        const response = await apiFetch(url, { method: 'DELETE' });
        if (response.status === 204) {
            showNotice('Удалено.');
            fetchList();
            return;
        }
        const data = await response.json().catch(() => ({}));
        const message = data?.error?.message || 'Не удалось удалить.';
        showNotice(message, true);
    }

    function setResource(resource) {
        state.resource = resource;
        state.page = 1;
        state.filters = [];
        elements.resourceTitle.textContent = resource.label;
        elements.resourceMeta.textContent = resource.endpoint;
        toggleBackupControls();
        renderFilters();
        fetchList();
        document.querySelectorAll('.nav button').forEach((btn) => {
            btn.classList.toggle('active', btn.dataset.id === resource.id);
        });
    }

    function toggleBackupControls() {
        const isBackups = state.resource && state.resource.id === 'backups';
        if (elements.backupBtn) {
            elements.backupBtn.style.display = isBackups ? 'inline-flex' : 'none';
        }
        if (elements.restoreBtn) {
            elements.restoreBtn.style.display = isBackups ? 'inline-flex' : 'none';
        }
        if (elements.restoreKeyInput) {
            elements.restoreKeyInput.style.display = isBackups ? 'inline-flex' : 'none';
        }
        if (elements.createBtn) {
            elements.createBtn.style.display = isBackups ? 'none' : 'inline-flex';
        }
    }

    async function createBackup() {
        showNotice('');
        const response = await apiFetch('/api/backups/', { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const message = data?.error?.message || 'Не удалось создать резервную копию.';
            showNotice(message, true);
            return;
        }
        await fetchList();
        showNotice('Резервная копия создана.');
    }

    async function restoreFromFile(file) {
        if (!file) return;
        if (!confirm('Восстановить базу из этого бэкапа? Текущие данные будут заменены.')) return;
        showNotice('');
        const body = new FormData();
        body.append('backup_file', file);
        const response = await apiFetch('/api/backups/restore_upload/', { method: 'POST', body });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const message = data?.error?.message || 'Не удалось восстановить.';
            showNotice(message, true);
            return;
        }
        if (data.access || data.refresh) {
            tokenStore.set(data.access, data.refresh);
        }
        await fetchList();
        showNotice('Восстановление выполнено. При необходимости обновите страницу.');
    }

    async function downloadBackup(item) {
        if (!item || !item.id) return;
        showNotice('');
        const response = await apiFetch(`/api/backups/${item.id}/download/`);
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            const message = data?.error?.message || 'Не удалось скачать.';
            showNotice(message, true);
            return;
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = item.file_path ? item.file_path.split('/').pop() : `backup-${item.id}.json`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    async function restoreBackup(item) {
        if (!item || !item.id) return;
        if (!confirm('Восстановить базу из этого бэкапа? Текущие данные будут заменены.')) return;
        showNotice('');
        const response = await apiFetch(`/api/backups/${item.id}/restore/`, { method: 'POST' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const message = data?.error?.message || 'Не удалось восстановить.';
            showNotice(message, true);
            return;
        }
        if (data.access || data.refresh) {
            tokenStore.set(data.access, data.refresh);
        }
        showNotice('Восстановление выполнено. При необходимости обновите страницу.');
    }

    function initNav() {
        resources.forEach((resource) => {
            const btn = document.createElement('button');
            btn.textContent = resource.label;
            btn.dataset.id = resource.id;
            btn.addEventListener('click', () => setResource(resource));
            elements.resourceList.appendChild(btn);
        });
        setResource(resources[0]);
    }

    elements.applyFilters.addEventListener('click', () => {
        state.search = elements.searchInput.value.trim();
        state.ordering = elements.orderingInput.value.trim();
        state.pageSize = Number(elements.pageSizeInput.value) || 20;
        state.page = 1;
        fetchList();
    });

    elements.resetFilters.addEventListener('click', () => {
        elements.searchInput.value = '';
        elements.orderingInput.value = '';
        elements.pageSizeInput.value = 20;
        state.search = '';
        state.ordering = '';
        state.pageSize = 20;
        state.filters = [];
        renderFilters();
        fetchList();
    });

    elements.addFilterRow.addEventListener('click', () => {
        state.filters.push({ field: '', value: '' });
        renderFilters();
    });

    elements.prevPage.addEventListener('click', () => {
        if (!state.previous) return;
        state.page = Math.max(1, state.page - 1);
        fetchList();
    });

    elements.nextPage.addEventListener('click', () => {
        if (!state.next) return;
        state.page += 1;
        fetchList();
    });

    elements.createBtn.addEventListener('click', () => openForm('create'));
    elements.refreshBtn.addEventListener('click', fetchList);
    elements.modalCancel.addEventListener('click', () => elements.modal.classList.remove('active'));
    elements.modalSave.addEventListener('click', submitForm);
    if (elements.backupBtn) {
        elements.backupBtn.addEventListener('click', createBackup);
    }
    if (elements.restoreBtn && elements.restoreFile) {
        elements.restoreBtn.addEventListener('click', () => elements.restoreFile.click());
        elements.restoreFile.addEventListener('change', (event) => {
            const file = event.target.files && event.target.files[0];
            event.target.value = '';
            restoreFromFile(file);
        });
    }

    initNav();
})();
