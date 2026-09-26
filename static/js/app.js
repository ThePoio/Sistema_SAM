const state = { user: null };
const $ = (selector) => document.querySelector(selector);

function showMessage(selector, message, isError = true) {
  const element = $(selector);
  element.textContent = message;
  element.style.color = isError ? 'var(--orange)' : 'var(--green)';
}

function headers() {
  return { 'Content-Type': 'application/json', 'X-Role': state.user.role, 'X-User-Id': state.user.username };
}

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'No se pudo completar la operacion');
  return data;
}

function formatDate(value) { return new Date(value).toLocaleDateString('es-ES', { day:'2-digit', month:'short', year:'numeric' }); }
function cardTemplate(item, editable = false) {
  const form = editable ? `<form class="evidence-form" data-id="${item.id}"><label>Avance (%)<input name="progress" type="number" min="0" max="100" value="${item.progress}" required></label><label>Evidencia entregada<textarea name="evidence" required minlength="5">${item.evidence || ''}</textarea></label><button class="button primary mini-button" type="submit">Guardar avance <span>↗</span></button><button class="button ghost mini-button analyze-button" type="button" data-id="${item.id}">Analizar evidencia con IA</button><div class="analysis" data-analysis="${item.id}"></div></form>` : `<p class="meta">Evidencia: ${item.evidence || 'Sin evidencia registrada'}</p>`;
  return `<article class="evaluation-card"><h3>${item.title}</h3><p class="meta">${item.area} · Responsable: ${item.assigned_to} · Limite: ${formatDate(item.due_date)}</p><div class="progress-track"><div class="progress-bar" style="width:${item.progress}%"></div></div><div class="progress-label"><span>${item.status}</span><span>${item.progress}%</span></div>${form}</article>`;
}

async function loadEvaluations() {
  const list = await api('/api/evaluations');
  const target = state.user.role === 'admin' ? '#admin-list' : '#encargado-list';
  $(target).innerHTML = list.length ? list.map((item) => cardTemplate(item, state.user.role === 'encargado')).join('') : '<p class="meta">Aun no hay evaluaciones para mostrar.</p>';
  if (state.user.role === 'encargado') bindEvidenceActions();
}

function userTemplate(user) {
  return `<article class="user-row"><div><strong>${user.username}</strong><p class="meta">${user.display_name}</p></div><p class="meta">${user.email}</p><span class="role-tag">${user.role}</span><p class="meta">ID: ${user.id.slice(-8)}</p><div class="user-row-actions"><button class="button ghost edit-user" type="button" data-user='${JSON.stringify(user)}'>Editar</button><button class="button ghost danger delete-user" type="button" data-id="${user.id}" data-name="${user.username}">Eliminar</button></div></article>`;
}

async function loadUsers() {
  const users = await api('/api/users');
  $('#user-list').innerHTML = users.length ? users.map(userTemplate).join('') : '<p class="meta">No hay usuarios registrados.</p>';
  bindUserActions();
}

function resetUserForm() {
  $('#user-form').reset();
  $('#user-form [name="id"]').value = '';
  $('#user-form [name="username"]').disabled = false;
  $('#user-form [name="password"]').required = true;
  $('#user-form [name="password"]').placeholder = 'Obligatoria al crear';
  $('#user-submit-label').textContent = 'Crear usuario';
  $('#cancel-user-edit').classList.add('hidden');
}

function bindUserActions() {
  document.querySelectorAll('.edit-user').forEach((button) => button.addEventListener('click', () => {
    const user = JSON.parse(button.dataset.user);
    const form = $('#user-form');
    Object.entries(user).forEach(([key, value]) => { if (form.elements[key]) form.elements[key].value = value; });
    form.elements.id.value = user.id;
    form.elements.username.disabled = true;
    form.elements.password.value = '';
    form.elements.password.required = false;
    form.elements.password.placeholder = 'Dejar vacia para conservar';
    $('#user-submit-label').textContent = 'Guardar cambios';
    $('#cancel-user-edit').classList.remove('hidden');
    form.scrollIntoView({ behavior:'smooth', block:'center' });
  }));
  document.querySelectorAll('.delete-user').forEach((button) => button.addEventListener('click', async () => {
    if (!window.confirm(`¿Eliminar al usuario ${button.dataset.name}?`)) return;
    try { await api(`/api/users/${button.dataset.id}`, { method:'DELETE' }); showMessage('#user-message', 'Usuario eliminado correctamente.', false); await loadUsers(); } catch (error) { showMessage('#user-message', error.message); }
  }));
}

function bindEvidenceActions() {
  document.querySelectorAll('.evidence-form').forEach((form) => form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(form));
    try { await api(`/api/evaluations/${form.dataset.id}/progress`, { method:'PUT', body:JSON.stringify({ progress:Number(payload.progress), evidence:payload.evidence }) }); showMessage('#dashboard-message', 'Avance guardado correctamente.', false); await loadEvaluations(); } catch (error) { showMessage('#dashboard-message', error.message); }
  }));
  document.querySelectorAll('.analyze-button').forEach((button) => button.addEventListener('click', async () => {
    const output = document.querySelector(`[data-analysis="${button.dataset.id}"]`);
    button.disabled = true; output.textContent = 'Procesando evidencia durante unos segundos...';
    try { const result = await api(`/api/evaluations/${button.dataset.id}/analyze`, { method:'POST' }); output.textContent = `${result.summary} Puntaje: ${result.score}/100`; } catch (error) { output.textContent = error.message; } finally { button.disabled = false; }
  }));
}

$('#login-form').addEventListener('submit', async (event) => {
  event.preventDefault(); showMessage('#login-message', 'Verificando acceso...', false);
  const payload = Object.fromEntries(new FormData(event.target));
  try { const result = await fetch('/api/auth/login', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) }); const data = await result.json(); if (!result.ok) throw new Error(data.detail); state.user = data.user; $('#login-view').classList.add('hidden'); $('#dashboard-view').classList.remove('hidden'); $('#admin-view').classList.toggle('hidden', state.user.role !== 'admin'); $('#user-management').classList.toggle('hidden', state.user.role !== 'admin'); $('#encargado-view').classList.toggle('hidden', state.user.role !== 'encargado'); $('#dashboard-title').textContent = state.user.role === 'admin' ? 'Control de evaluaciones' : 'Mi agenda de evidencias'; $('#session-user').textContent = `${state.user.display_name} · ${state.user.email}`; await loadEvaluations(); if (state.user.role === 'admin') await loadUsers(); } catch (error) { showMessage('#login-message', error.message); }
});

$('#evaluation-form').addEventListener('submit', async (event) => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.target)); try { await api('/api/evaluations', { method:'POST', body:JSON.stringify({ ...values, due_date:new Date(values.due_date).toISOString() }) }); event.target.reset(); showMessage('#dashboard-message', 'Evaluacion creada correctamente.', false); await loadEvaluations(); } catch (error) { showMessage('#dashboard-message', error.message); } });
$('#user-form').addEventListener('submit', async (event) => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.target)); const id = values.id; const payload = { username:values.username, email:values.email, display_name:values.display_name, role:values.role, ...(values.password ? { password:values.password } : {}) }; try { await api(id ? `/api/users/${id}` : '/api/users', { method:id ? 'PUT' : 'POST', body:JSON.stringify(id ? Object.fromEntries(Object.entries(payload).filter(([key]) => key !== 'username')) : payload) }); showMessage('#user-message', id ? 'Usuario actualizado correctamente.' : 'Usuario creado correctamente.', false); resetUserForm(); await loadUsers(); } catch (error) { showMessage('#user-message', error.message); } });
$('#refresh-admin').addEventListener('click', loadEvaluations); $('#refresh-encargado').addEventListener('click', loadEvaluations);
$('#refresh-users').addEventListener('click', loadUsers); $('#cancel-user-edit').addEventListener('click', resetUserForm);
$('#logout-button').addEventListener('click', () => { state.user = null; $('#dashboard-view').classList.add('hidden'); $('#login-view').classList.remove('hidden'); $('#login-form').reset(); resetUserForm(); });
