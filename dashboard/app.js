// Configuración
const API_URL = 'http://localhost:9000';  // Backend FastAPI
let authToken = null;
let currentUser = null;
let selectedIncidenciaId = null;
let selectedRutaId = null;

// ==================== AUTENTICACIÓN ====================

// Login
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    // Limpiar error previo
    const errorDiv = document.getElementById('loginError');
    if (errorDiv) {
        errorDiv.textContent = '';
        errorDiv.classList.remove('active');
    }
    
    try {
        console.log('Intentando login con:', username);
        
        const response = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        console.log('Respuesta del servidor:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Credenciales inválidas');
        }
        
        const data = await response.json();
        console.log('Login exitoso:', data);
        
        authToken = data.access_token;
        currentUser = data;
        
        // Guardar en localStorage
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        // Ocultar modal de login
        closeModal('loginModal');
        
        // Actualizar UI
        document.getElementById('username').textContent = currentUser.username;
        
        // Cargar datos iniciales
        loadIncidencias();
        
    } catch (error) {
        console.error('Error en login:', error);
        showError('loginError', error.message);
    }
});

// Logout
function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    // Mostrar modal de login
    document.getElementById('loginModal').classList.add('active');
}

// Verificar autenticación al cargar
window.addEventListener('DOMContentLoaded', () => {
    authToken = localStorage.getItem('authToken');
    const userStr = localStorage.getItem('currentUser');
    
    if (authToken && userStr) {
        currentUser = JSON.parse(userStr);
        document.getElementById('username').textContent = currentUser.username;
        closeModal('loginModal');
        loadIncidencias();
    }
});

// ==================== NAVEGACIÓN ====================

// Tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Cambiar tab activo
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Cambiar contenido activo
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
        
        // Cargar datos según la tab
        if (tabName === 'incidencias') loadIncidencias();
        else if (tabName === 'rutas') loadRutas();
        else if (tabName === 'conductores') loadConductores();
        else if (tabName === 'horarios') loadHorarios();
        else if (tabName === 'stats') loadStats();
    });
});

// ==================== INCIDENCIAS ====================

async function loadIncidencias() {
    const container = document.getElementById('incidenciasList');
    container.innerHTML = '<div class="loading">Cargando incidencias...</div>';
    
    try {
        const estado = document.getElementById('filterEstado').value;
        const zona = document.getElementById('filterZona').value;
        
        let url = `${API_URL}/api/incidencias/`;
        const params = new URLSearchParams();
        if (estado) params.append('estado', estado);
        if (zona) params.append('zona', zona);
        
        if (params.toString()) url += '?' + params.toString();
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Asegurar que incidencias sea un array
        const incidencias = Array.isArray(data) ? data : [];
        
        if (incidencias.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>📭 No hay incidencias</h3>
                    <p>No se encontraron incidencias con los filtros seleccionados</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = incidencias.map(inc => `
            <div class="card">
                <div class="card-header">
                    <div>
                        <span class="badge badge-${inc.tipo}">${formatTipo(inc.tipo)}</span>
                        <span class="badge badge-${inc.estado}">${formatEstado(inc.estado)}</span>
                    </div>
                    <span class="badge badge-${inc.zona}">${inc.zona}</span>
                </div>
                <div class="card-body">
                    <div class="card-info">
                        <div class="info-row">
                            <span class="info-label">ID:</span>
                            <span class="info-value">#${inc.id}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Gravedad:</span>
                            <span class="info-value">${inc.gravedad}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Descripción:</span>
                            <span class="info-value">${inc.descripcion || 'Sin descripción'}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Reportado:</span>
                            <span class="info-value">${formatDate(inc.reportado_en)}</span>
                        </div>
                        ${inc.lat && inc.lon ? `
                        <div class="info-row">
                            <span class="info-label">Ubicación:</span>
                            <span class="info-value">${inc.lat.toFixed(4)}, ${inc.lon.toFixed(4)}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
                <div class="card-footer">
                    ${inc.estado === 'pendiente' ? `
                        <button onclick="showValidarModal(${inc.id})" class="btn btn-success btn-sm">✅ Validar</button>
                        <button onclick="showRechazarModal(${inc.id})" class="btn btn-danger btn-sm">❌ Rechazar</button>
                    ` : ''}
                    ${inc.foto_url ? `
                        <a href="${inc.foto_url}" target="_blank" class="btn btn-info btn-sm">📷 Ver Foto</a>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        container.innerHTML = `<div class="error-message active">Error al cargar incidencias: ${error.message}</div>`;
    }
}

// Validar incidencia
function showValidarModal(id) {
    selectedIncidenciaId = id;
    document.getElementById('validarInfo').textContent = `¿Está seguro de validar la incidencia #${id}?`;
    document.getElementById('validarModal').classList.add('active');
}

async function confirmarValidacion() {
    const errorDiv = document.getElementById('validarError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('active');
    
    try {
        const response = await fetch(`${API_URL}/api/incidencias/${selectedIncidenciaId}/validate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al validar incidencia');
        }
        
        const result = await response.json();
        
        closeModal('validarModal');
        
        // Mostrar mensaje de éxito
        if (result.ruta_generada_id) {
            // Si se generó ruta, mostrar indicador de carga brevemente para feedback visual
            showLoading();
            setTimeout(() => {
                hideLoading();
                alert(`✅ Incidencia validada exitosamente\n🗺️ ¡Se generó la ruta #${result.ruta_generada_id}!\n\nSe superó el umbral de gravedad.`);
                loadRutas();
            }, 1500);
        } else {
            alert('✅ Incidencia validada exitosamente\n\nAún no se supera el umbral para generar ruta.');
        }
        
        loadIncidencias();
        
    } catch (error) {
        hideLoading();
        showError('validarError', error.message);
    }
}

// Rechazar incidencia
function showRechazarModal(id) {
    selectedIncidenciaId = id;
    document.getElementById('rechazarInfo').textContent = `Rechazar la incidencia #${id}`;
    document.getElementById('rechazarMotivo').value = '';
    document.getElementById('rechazarModal').classList.add('active');
}

async function confirmarRechazo() {
    const errorDiv = document.getElementById('rechazarError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('active');
    
    try {
        const response = await fetch(`${API_URL}/api/incidencias/${selectedIncidenciaId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ estado: 'cancelada' })
        });
        
        if (!response.ok) {
            throw new Error('Error al rechazar incidencia');
        }
        
        closeModal('rechazarModal');
        alert('❌ Incidencia rechazada');
        loadIncidencias();
        
    } catch (error) {
        showError('rechazarError', error.message);
    }
}

// ==================== RUTAS ====================

async function loadRutas() {
    const container = document.getElementById('rutasList');
    container.innerHTML = '<div class="loading">Cargando rutas...</div>';
    
    try {
        const zonaFilter = document.getElementById('filterRutaZona').value;
        const estadoFilter = document.getElementById('filterRutaEstado').value;
        
        let todasRutas = [];
        
        // Si se selecciona una zona específica, solo cargar esa zona
        if (zonaFilter) {
            const response = await fetch(`${API_URL}/api/rutas/zona/${zonaFilter}`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            const data = await response.json();
            todasRutas = data.rutas || [];
        } else {
            // Cargar ambas zonas
            const [orientalRes, occidentalRes] = await Promise.all([
                fetch(`${API_URL}/api/rutas/zona/oriental`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                }),
                fetch(`${API_URL}/api/rutas/zona/occidental`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                })
            ]);
            
            const orientalData = await orientalRes.json();
            const occidentalData = await occidentalRes.json();
            
            todasRutas = [
                ...(orientalData.rutas || []),
                ...(occidentalData.rutas || [])
            ];
        }
        
        // Filtrar por estado si se seleccionó
        let rutas = todasRutas;
        if (estadoFilter) {
            rutas = todasRutas.filter(r => r.estado === estadoFilter);
        }
        
        // Asegurar que rutas sea un array
        rutas = Array.isArray(rutas) ? rutas : [];
        
        if (rutas.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>🗺️ No hay rutas</h3>
                    <p>No se encontraron rutas con los filtros seleccionados</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = rutas.map(ruta => `
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Ruta #${ruta.id}</div>
                    <span class="badge badge-${ruta.zona}">${ruta.zona}</span>
                </div>
                <div class="card-body">
                    <div class="card-info">
                        <div class="info-row">
                            <span class="info-label">Estado:</span>
                            <span class="badge badge-${ruta.estado}">${formatEstado(ruta.estado)}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Gravedad Total:</span>
                            <span class="info-value">${ruta.suma_gravedad}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Camiones:</span>
                            <span class="info-value">${ruta.camiones_usados}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Duración:</span>
                            <span class="info-value">${ruta.duracion_estimada || 'N/A'}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Distancia:</span>
                            <span class="info-value">${(ruta.costo_total_metros / 1000).toFixed(2)} km</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Generada:</span>
                            <span class="info-value">${formatDate(ruta.fecha_generacion)}</span>
                        </div>
                        ${ruta.asignaciones && ruta.asignaciones.length > 0 ? `
                        <div class="info-row">
                            <span class="info-label">👷 Conductor:</span>
                            <span class="info-value">${ruta.asignaciones[0].conductor_nombre}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">🚛 Camión:</span>
                            <span class="info-value">${ruta.asignaciones[0].camion_tipo === 'posterior' ? 'Posterior' : 'Lateral'} - ${ruta.asignaciones[0].camion_id}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
                <div class="card-footer">
                    ${ruta.estado === 'planeada' && (!ruta.asignaciones || ruta.asignaciones.length === 0) ? `
                        <button onclick="showAsignarModal(${ruta.id})" class="btn btn-primary btn-sm">👷 Asignar Conductor</button>
                    ` : ''}
                    ${ruta.asignaciones && ruta.asignaciones.length > 0 ? `
                        <span class="badge badge-success">✅ Conductor Asignado</span>
                    ` : ''}
                    <button onclick="showRutaDetalle(${ruta.id})" class="btn btn-info btn-sm">👁️ Ver Detalles</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        container.innerHTML = `<div class="error-message active">Error al cargar rutas: ${error.message}</div>`;
    }
}

// Mostrar modal de asignación
async function showAsignarModal(rutaId) {
    selectedRutaId = rutaId;
    document.getElementById('asignarInfo').textContent = `Asignar conductor a la Ruta #${rutaId}`;
    document.getElementById('asignarError').textContent = '';
    document.getElementById('asignarError').classList.remove('active');
    
    // Primero obtener los detalles de la ruta para saber la zona
    try {
        const rutaResponse = await fetch(`${API_URL}/api/rutas/${rutaId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const ruta = await rutaResponse.json();
        const zona = ruta.zona;
        
        // Cargar conductores disponibles filtrados por zona
        const conductoresResponse = await fetch(`${API_URL}/api/conductores/disponibles?zona=${zona}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const conductores = await conductoresResponse.json();
        
        const select = document.getElementById('asignarConductor');
        
        if (!Array.isArray(conductores) || conductores.length === 0) {
            select.innerHTML = `<option value="">No hay conductores disponibles en zona ${zona}</option>`;
        } else {
            select.innerHTML = '<option value="">Seleccione un conductor...</option>' +
                conductores.map(c => `<option value="${c.id}">${c.nombre_completo} - ${c.cedula}</option>`).join('');
        }
        
        // Establecer fecha por defecto (mañana a las 8:00)
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(8, 0, 0, 0);
        document.getElementById('asignarFechaInicio').value = tomorrow.toISOString().slice(0, 16);
        
        document.getElementById('asignarModal').classList.add('active');
        
    } catch (error) {
        alert('Error al cargar conductores: ' + error.message);
    }
}

// Asignar conductor
document.getElementById('asignarForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const errorDiv = document.getElementById('asignarError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('active');
    
    const conductorId = parseInt(document.getElementById('asignarConductor').value);
    const tipoCamion = document.getElementById('asignarTipoCamion').value;
    const camionId = document.getElementById('asignarCamionId').value;
    const fechaInicio = document.getElementById('asignarFechaInicio').value;
    
    try {
        const body = {
            ruta_id: selectedRutaId,
            conductor_id: conductorId,
            camion_tipo: tipoCamion,
            camion_id: camionId
        };
        
        if (fechaInicio) {
            body.fecha_inicio = fechaInicio;
        }
        
        const response = await fetch(`${API_URL}/api/conductores/asignaciones/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al asignar conductor');
        }
        
        const result = await response.json();
        
        closeModal('asignarModal');
        alert(`✅ Conductor asignado exitosamente\n${fechaInicio ? '⏰ Inicio programado: ' + formatDate(fechaInicio) : ''}`);
        loadRutas();
        
    } catch (error) {
        showError('asignarError', error.message);
    }
});

// Ver detalles de ruta
async function showRutaDetalle(rutaId) {
    const contentDiv = document.getElementById('rutaDetalleContent');
    contentDiv.innerHTML = '<div class="loading">Cargando detalles...</div>';
    
    document.getElementById('rutaDetalleModal').classList.add('active');
    
    try {
        const response = await fetch(`${API_URL}/api/rutas/${rutaId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const ruta = await response.json();
        
        contentDiv.innerHTML = `
            <div class="card-info">
                <div class="info-row">
                    <span class="info-label">ID:</span>
                    <span class="info-value">#${ruta.id}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Zona:</span>
                    <span class="badge badge-${ruta.zona}">${ruta.zona}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Estado:</span>
                    <span class="badge badge-${ruta.estado}">${formatEstado(ruta.estado)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Gravedad Total:</span>
                    <span class="info-value">${ruta.suma_gravedad}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Camiones Usados:</span>
                    <span class="info-value">${ruta.camiones_usados}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Duración Estimada:</span>
                    <span class="info-value">${ruta.duracion_estimada || 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Distancia:</span>
                    <span class="info-value">${(ruta.costo_total_metros / 1000).toFixed(2)} km</span>
                </div>
            </div>
            
            ${ruta.puntos && ruta.puntos.length > 0 ? `
            <div class="ruta-points">
                <h4>Puntos de la Ruta (${ruta.puntos.length}):</h4>
                ${ruta.puntos.slice(0, 10).map(punto => `
                    <div class="point-item">
                        <div class="point-number">${punto.secuencia}</div>
                        <div>
                            <strong>${formatTipoPunto(punto.tipo_punto)}</strong>
                            ${punto.incidencia_id ? ` - Incidencia #${punto.incidencia_id} (${formatTipo(punto.tipo_incidencia)})` : ''}
                        </div>
                    </div>
                `).join('')}
                ${ruta.puntos.length > 10 ? `<p style="color: var(--secondary); font-size: 12px; margin-top: 10px;">... y ${ruta.puntos.length - 10} puntos más</p>` : ''}
            </div>
            ` : ''}
            
            ${ruta.asignaciones && ruta.asignaciones.length > 0 ? `
            <div class="ruta-points">
                <h4>Asignaciones:</h4>
                ${ruta.asignaciones.map(asig => `
                    <div class="point-item">
                        <div>
                            <strong>${asig.conductor_nombre || 'Conductor'}</strong>
                            <br>
                            <small>Camión: ${asig.camion_id} (${asig.camion_tipo})</small>
                            <br>
                            <small>Estado: <span class="badge badge-${asig.estado}">${formatEstado(asig.estado)}</span></small>
                            ${asig.fecha_inicio ? `<br><small>⏰ Inicio: ${formatDate(asig.fecha_inicio)}</small>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
            ` : ''}
        `;
        
    } catch (error) {
        contentDiv.innerHTML = `<div class="error-message active">Error al cargar detalles: ${error.message}</div>`;
    }
}

// ==================== CONDUCTORES ====================

async function loadConductores() {
    const container = document.getElementById('conductoresList');
    container.innerHTML = '<div class="loading">Cargando conductores...</div>';
    
    try {
        const response = await fetch(`${API_URL}/api/conductores/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        
        // Asegurar que conductores sea un array
        const conductores = Array.isArray(data) ? data : [];
        
        if (conductores.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>👷 No hay conductores</h3>
                    <p>No hay conductores registrados en el sistema</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre Completo</th>
                        <th>Cédula</th>
                        <th>Teléfono</th>
                        <th>Licencia</th>
                        <th>Zona Preferida</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                    ${conductores.map(c => `
                        <tr>
                            <td>#${c.id}</td>
                            <td>${c.nombre_completo}</td>
                            <td>${c.cedula}</td>
                            <td>${c.telefono}</td>
                            <td><span class="badge badge-info">Tipo ${c.licencia_tipo}</span></td>
                            <td><span class="badge badge-${c.zona_preferida}">${c.zona_preferida}</span></td>
                            <td><span class="badge badge-${c.estado === 'activo' ? 'completada' : 'cancelada'}">${c.estado}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
    } catch (error) {
        console.error('Error al cargar conductores:', error);
        container.innerHTML = `<div class="error-message active">Error al cargar conductores: ${error.message}<br><small>Verifica la consola del navegador (F12) para más detalles</small></div>`;
    }
}

// Mostrar modal de crear conductor
function showCreateConductorModal() {
    document.getElementById('createConductorForm').reset();
    document.getElementById('createConductorError').textContent = '';
    document.getElementById('createConductorError').classList.remove('active');
    document.getElementById('createConductorModal').classList.add('active');
}

// Crear conductor
document.getElementById('createConductorForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const errorDiv = document.getElementById('createConductorError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('active');
    
    const formData = {
        username: document.getElementById('newUsername').value,
        email: document.getElementById('newEmail').value,
        password: document.getElementById('newPassword').value,
        nombre_completo: document.getElementById('newNombreCompleto').value,
        cedula: document.getElementById('newCedula').value,
        telefono: document.getElementById('newTelefono').value,
        licencia_tipo: document.getElementById('newLicenciaTipo').value,
        zona_preferida: document.getElementById('newZonaPreferida').value
    };
    
    try {
        const response = await fetch(`${API_URL}/api/conductores/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al crear conductor');
        }
        
        const result = await response.json();
        
        closeModal('createConductorModal');
        alert('✅ Conductor creado exitosamente');
        loadConductores();
        
    } catch (error) {
        showError('createConductorError', error.message);
    }
});

// ==================== HORARIOS ====================

async function loadHorarios() {
    const container = document.getElementById('horariosContent');
    container.innerHTML = '<div class="loading">Cargando horarios...</div>';
    
    try {
        const zonaFilter = document.getElementById('filterHorarioZona').value;
        // Cargar todas las asignaciones de conductores
        const response = await fetch(`${API_URL}/api/conductores/asignaciones/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        let asignaciones = await response.json();
        if (!Array.isArray(asignaciones)) {
            asignaciones = [];
        }
        // Filtrar por zona si es necesario
        if (zonaFilter) {
            asignaciones = asignaciones.filter(a => a.ruta?.zona === zonaFilter);
        }
        // Filtrar solo asignaciones con fecha_inicio programada
        const asignacionesProgramadas = asignaciones.filter(a => a.fecha_inicio);
        // Agrupar por día y luego por conductor
        const asignacionesPorDia = {};
        asignacionesProgramadas.forEach(asignacion => {
            const fecha = new Date(asignacion.fecha_inicio);
            const diaKey = fecha.toISOString().split('T')[0]; // YYYY-MM-DD
            if (!asignacionesPorDia[diaKey]) {
                asignacionesPorDia[diaKey] = [];
            }
            asignacionesPorDia[diaKey].push(asignacion);
        });
        const diasOrdenados = Object.keys(asignacionesPorDia).sort();
        if (diasOrdenados.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No hay rutas programadas</h3>
                    <p>Asigna conductores a rutas con horarios para verlas aquí</p>
                </div>
            `;
            return;
        }
        let html = '<div class="schedule-container">';
        diasOrdenados.forEach(diaKey => {
            const asignacionesDia = asignacionesPorDia[diaKey];
            const fecha = new Date(diaKey);
            const nombreDia = fecha.toLocaleDateString('es-EC', { weekday: 'long' });
            const fechaFormato = fecha.toLocaleDateString('es-EC', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            html += `
                <div class="day-section">
                    <div class="day-header">
                        <div>
                            <div class="day-name">${nombreDia.charAt(0).toUpperCase() + nombreDia.slice(1)}</div>
                            <div class="day-date">${fechaFormato}</div>
                        </div>
                        <div class="day-count">${asignacionesDia.length} ruta${asignacionesDia.length !== 1 ? 's' : ''}</div>
                    </div>
                    <div class="schedule-items">
            `;
            // Agrupar por conductor
            const asignacionesPorConductor = {};
            asignacionesDia.forEach(asignacion => {
                const nombre = asignacion.conductor?.nombre_completo || 'Sin conductor';
                if (!asignacionesPorConductor[nombre]) {
                    asignacionesPorConductor[nombre] = [];
                }
                asignacionesPorConductor[nombre].push(asignacion);
            });
            // Mostrar por conductor
            Object.keys(asignacionesPorConductor).sort().forEach(nombreConductor => {
                html += `<div class="conductor-section">
                    <div class="conductor-header"><strong>👷 ${nombreConductor}</strong></div>
                `;
                // Ordenar por hora
                asignacionesPorConductor[nombreConductor].sort((a, b) => new Date(a.fecha_inicio) - new Date(b.fecha_inicio));
                asignacionesPorConductor[nombreConductor].forEach(asignacion => {
                    const horaInicio = new Date(asignacion.fecha_inicio).toLocaleTimeString('es-EC', {
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    html += `
                        <div class="schedule-item">
                            <div class="schedule-info">
                                <div class="schedule-time">🕐 ${horaInicio}</div>
                                <div class="schedule-details">
                                    <span class="schedule-detail">
                                        🗺️ Ruta #${asignacion.ruta_id}
                                    </span>
                                    <span class="schedule-detail">
                                        🚛 ${asignacion.camion_tipo === 'posterior' ? 'Posterior' : 'Lateral'} - ${asignacion.camion_id}
                                    </span>
                                    <span class="badge badge-${asignacion.ruta?.zona || 'oriental'}">
                                        ${(asignacion.ruta?.zona || 'N/A').toUpperCase()}
                                    </span>
                                    <span class="badge badge-${asignacion.estado}">
                                        ${formatEstado(asignacion.estado)}
                                    </span>
                                </div>
                            </div>
                            <div class="schedule-actions">
                                <button onclick="verRutaDetalle(${asignacion.ruta_id})" class="btn btn-info btn-sm">
                                    📍 Ver Ruta
                                </button>
                            </div>
                        </div>
                    `;
                });
                html += `</div>`;
            });
            html += `
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>Error al cargar horarios</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// ==================== ESTADÍSTICAS ====================

async function loadStats() {
    const container = document.getElementById('statsContent');
    container.innerHTML = '<div class="loading">Cargando estadísticas...</div>';
    
    try {
        // Cargar estadísticas de incidencias
        const response = await fetch(`${API_URL}/api/incidencias/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const incidencias = await response.json();
        
        // Cargar rutas
        const rutasResponse = await fetch(`${API_URL}/api/rutas/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const rutas = await rutasResponse.json();
        
        // Cargar umbrales
        const umbralesResponse = await fetch(`${API_URL}/api/incidencias/umbrales`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const umbrales = await umbralesResponse.json();
        
        // Calcular estadísticas
        const stats = {
            total_incidencias: incidencias.length,
            pendientes: incidencias.filter(i => i.estado === 'pendiente').length,
            validadas: incidencias.filter(i => i.estado === 'validada').length,
            completadas: incidencias.filter(i => i.estado === 'completada').length,
            total_rutas: rutas.length,
            rutas_planeadas: rutas.filter(r => r.estado === 'planeada').length,
            rutas_ejecucion: rutas.filter(r => r.estado === 'en_ejecucion').length,
            rutas_completadas: rutas.filter(r => r.estado === 'completada').length
        };
        
        container.innerHTML = `
            <div class="stat-card info">
                <h3>Total Incidencias</h3>
                <div class="stat-value">${stats.total_incidencias}</div>
            </div>
            <div class="stat-card warning">
                <h3>Pendientes de Validar</h3>
                <div class="stat-value">${stats.pendientes}</div>
            </div>
            <div class="stat-card">
                <h3>Validadas</h3>
                <div class="stat-value">${stats.validadas}</div>
            </div>
            <div class="stat-card success">
                <h3>Completadas</h3>
                <div class="stat-value">${stats.completadas}</div>
            </div>
            <div class="stat-card info">
                <h3>Total Rutas</h3>
                <div class="stat-value">${stats.total_rutas}</div>
            </div>
            <div class="stat-card">
                <h3>Rutas Planeadas</h3>
                <div class="stat-value">${stats.rutas_planeadas}</div>
            </div>
            <div class="stat-card warning">
                <h3>En Ejecución</h3>
                <div class="stat-value">${stats.rutas_ejecucion}</div>
            </div>
            <div class="stat-card success">
                <h3>Rutas Completadas</h3>
                <div class="stat-value">${stats.rutas_completadas}</div>
            </div>
            
            <!-- Sección de Umbrales -->
            <div class="umbral-section">
                <h2>⚖️ Umbrales de Gravedad por Zona</h2>
                <p class="umbral-description">Umbral configurado: <strong>${umbrales.umbral}</strong> puntos</p>
                
                <div class="umbral-cards">
                    <!-- Zona Oriental -->
                    <div class="umbral-card ${umbrales.oriental.supera_umbral ? 'supera' : ''}">
                        <h3>🌅 Zona Oriental</h3>
                        <div class="umbral-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${Math.min(umbrales.oriental.porcentaje, 100)}%"></div>
                            </div>
                            <div class="progress-label">${umbrales.oriental.porcentaje}%</div>
                        </div>
                        <div class="umbral-stats">
                            <div class="umbral-stat">
                                <span class="umbral-label">Gravedad Acumulada:</span>
                                <span class="umbral-value">${umbrales.oriental.gravedad_acumulada} / ${umbrales.umbral}</span>
                            </div>
                            <div class="umbral-stat">
                                <span class="umbral-label">Incidencias Validadas:</span>
                                <span class="umbral-value">${umbrales.oriental.incidencias_validadas}</span>
                            </div>
                            <div class="umbral-stat ${umbrales.oriental.supera_umbral ? 'success' : 'warning'}">
                                <span class="umbral-label">${umbrales.oriental.supera_umbral ? '✅ Supera umbral' : '⏳ Faltan'}:</span>
                                <span class="umbral-value">${umbrales.oriental.supera_umbral ? 'Ruta disponible' : umbrales.oriental.falta + ' puntos'}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Zona Occidental -->
                    <div class="umbral-card ${umbrales.occidental.supera_umbral ? 'supera' : ''}">
                        <h3>🌄 Zona Occidental</h3>
                        <div class="umbral-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${Math.min(umbrales.occidental.porcentaje, 100)}%"></div>
                            </div>
                            <div class="progress-label">${umbrales.occidental.porcentaje}%</div>
                        </div>
                        <div class="umbral-stats">
                            <div class="umbral-stat">
                                <span class="umbral-label">Gravedad Acumulada:</span>
                                <span class="umbral-value">${umbrales.occidental.gravedad_acumulada} / ${umbrales.umbral}</span>
                            </div>
                            <div class="umbral-stat">
                                <span class="umbral-label">Incidencias Validadas:</span>
                                <span class="umbral-value">${umbrales.occidental.incidencias_validadas}</span>
                            </div>
                            <div class="umbral-stat ${umbrales.occidental.supera_umbral ? 'success' : 'warning'}">
                                <span class="umbral-label">${umbrales.occidental.supera_umbral ? '✅ Supera umbral' : '⏳ Faltan'}:</span>
                                <span class="umbral-value">${umbrales.occidental.supera_umbral ? 'Ruta disponible' : umbrales.occidental.falta + ' puntos'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        container.innerHTML = `<div class="error-message active">Error al cargar estadísticas: ${error.message}</div>`;
    }
}

// ==================== UTILIDADES ====================

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function showError(elementId, message) {
    const errorDiv = document.getElementById(elementId);
    errorDiv.textContent = message;
    errorDiv.classList.add('active');
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('es-EC', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatEstado(estado) {
    const estados = {
        'pendiente': 'Pendiente',
        'validada': 'Validada',
        'asignada': 'Asignada',
        'completada': 'Completada',
        'cancelada': 'Cancelada',
        'planeada': 'Planeada',
        'en_ejecucion': 'En Ejecución',
        'asignado': 'Asignado',
        'iniciado': 'Iniciado',
        'completado': 'Completado'
    };
    return estados[estado] || estado;
}

function formatTipo(tipo) {
    const tipos = {
        'acopio': 'Acopio',
        'zona_critica': 'Zona Crítica',
        'animal_muerto': 'Animal Muerto'
    };
    return tipos[tipo] || tipo;
}

function formatTipoPunto(tipo) {
    const tipos = {
        'deposito': '🏭 Depósito',
        'incidencia': '📍 Incidencia'
    };
    return tipos[tipo] || tipo;
}

// Loading overlay functions
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.add('active');
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('active');
}

// Cerrar modales al hacer clic fuera
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// ==================== HORARIOS SYSTEM ====================

// Función para cambiar entre sub-tabs
function switchSubTab(tabName) {
    // Actualizar botones
    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Actualizar contenido
    document.querySelectorAll('.sub-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
    
    // Cargar datos según el tab
    switch(tabName) {
        case 'horarios-list':
            loadHorarios();
            break;
        case 'ejecuciones':
            loadEjecucionesHoy();
            break;
    }
}

// Event listeners para sub-tabs
document.querySelectorAll('.sub-tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const subtab = e.target.dataset.subtab;
        switchSubTab(subtab);
    });
});

// ==================== SECTORES ====================

// Cargar sectores
async function loadSectores() {
    if (!authToken) return;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/api/horarios/sectores`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Error al cargar sectores');
        
        const sectores = await response.json();
        displaySectores(sectores);
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al cargar sectores', 'error');
    } finally {
        hideLoading();
    }
}

// Mostrar sectores
function displaySectores(sectores) {
    const grid = document.getElementById('sectoresGrid');
    
    if (sectores.length === 0) {
        grid.innerHTML = '<div class="empty-day">No hay sectores registrados</div>';
        return;
    }
    
    grid.innerHTML = sectores.map(sector => {
        // Manejar coordenadas de manera segura
        let coordenadasInfo = 'N/A';
        try {
            if (sector.poligono && sector.poligono.coordinates && sector.poligono.coordinates[0]) {
                coordenadasInfo = `${sector.poligono.coordinates[0].length} puntos`;
            }
        } catch (e) {
            coordenadasInfo = 'Datos no disponibles';
        }
        
        return `
        <div class="sector-card">
            <div class="sector-header">
                <div class="sector-name">${sector.nombre}</div>
                <span class="sector-badge ${sector.zona}">${sector.zona.toUpperCase()}</span>
            </div>
            <div class="sector-info">
                <div class="sector-info-item">
                    🗺️ <strong>Descripción:</strong> ${sector.descripcion || 'Sin descripción'}
                </div>
                <div class="sector-info-item">
                    📊 <strong>Población:</strong> ${sector.poblacion_aproximada || 'N/A'} habitantes
                </div>
                <div class="sector-info-item">
                    📍 <strong>Coordenadas:</strong> ${coordenadasInfo}
                </div>
            </div>
            <div class="sector-actions">
                <button class="btn-primary btn-sm" onclick="verSectorMapa(${sector.id})">
                    🗺️ Ver en Mapa
                </button>
                <button class="btn-secondary btn-sm" onclick="editSector(${sector.id})">
                    ✏️ Editar
                </button>
            </div>
        </div>
        `;
    }).join('');
}

// Crear nuevo sector
async function createSector() {
    const errorDiv = document.getElementById('createSectorError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('active');
    
    try {
        const nombre = document.getElementById('sectorNombre').value.trim();
        const descripcion = document.getElementById('sectorDescripcion').value.trim();
        const zona = document.getElementById('sectorZona').value;
        const poblacion = document.getElementById('sectorPoblacion').value;
        const poligonoText = document.getElementById('sectorPoligono').value.trim();
        
        if (!nombre || !zona || !poligonoText) {
            errorDiv.textContent = 'Todos los campos obligatorios deben estar completos';
            errorDiv.classList.add('active');
            return;
        }
        
        // Parsear y validar GeoJSON
        let coordinates;
        try {
            coordinates = JSON.parse(poligonoText);
            if (!Array.isArray(coordinates) || coordinates.length < 3) {
                throw new Error('Debe tener al menos 3 puntos');
            }
        } catch (e) {
            errorDiv.textContent = 'Formato de coordenadas inválido. Debe ser un array JSON de [longitud, latitud]';
            errorDiv.classList.add('active');
            return;
        }
        
        const sectorData = {
            nombre,
            descripcion,
            zona,
            poblacion_aproximada: poblacion ? parseInt(poblacion) : null,
            poligono: {
                type: "Polygon",
                coordinates: [coordinates]
            }
        };
        
        showLoading();
        
        const response = await fetch(`${API_URL}/api/horarios/sectores`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(sectorData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al crear sector');
        }
        
        showMessage('Sector creado exitosamente', 'success');
        document.getElementById('createSectorModal').classList.remove('active');
        document.getElementById('createSectorForm').reset();
        loadSectores();
        
    } catch (error) {
        console.error('Error:', error);
        errorDiv.textContent = error.message;
        errorDiv.classList.add('active');
    } finally {
        hideLoading();
    }
}

// ==================== HORARIOS ====================

// Cargar rutas para dropdown
async function loadRutasDropdown() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_URL}/api/rutas`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Error al cargar rutas');
        
        const rutas = await response.json();
        const select = document.getElementById('horarioRuta');
        
        select.innerHTML = '<option value="">Seleccione una ruta...</option>' +
            rutas.map(ruta => 
                `<option value="${ruta.id}">
                    Ruta #${ruta.id} - ${ruta.zona.toUpperCase()} - ${ruta.camiones_usados} camión(es) - ${ruta.estado}
                </option>`
            ).join('');
            
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al cargar rutas', 'error');
    }
}

// Cargar horarios
async function loadHorarios() {
    if (!authToken) return;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/api/horarios?incluir_inactivos=true`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Error al cargar horarios');
        
        const horarios = await response.json();
        displayHorarios(horarios);
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al cargar horarios', 'error');
    } finally {
        hideLoading();
    }
}

// Mostrar horarios
function displayHorarios(horarios) {
    const container = document.getElementById('horariosTable');
    
    if (horarios.length === 0) {
        container.innerHTML = '<div class="empty-day">No hay horarios programados. Crea uno usando las rutas generadas.</div>';
        return;
    }
    
    container.innerHTML = horarios.map(horario => {
        const diasArray = horario.dias_semana.split(',');
        const diasNombres = ['L', 'M', 'X', 'J', 'V', 'S', 'D'];
        
        // Obtener información de la ruta o sector
        const nombreRuta = horario.sector ? horario.sector.nombre : 
                          horario.ruta_id ? `Ruta #${horario.ruta_id}` : 
                          'Sin asignar';
        
        return `
            <div class="horario-row">
                <div class="horario-sector">
                    �️ ${nombreRuta}
                </div>
                <div class="horario-dias">
                    ${diasNombres.map((dia, index) => `
                        <span class="dia-badge ${diasArray.includes((index + 1).toString()) ? 'active' : ''}">
                            ${dia}
                        </span>
                    `).join('')}
                </div>
                <div class="horario-tiempo">
                    🕐 ${horario.hora_inicio} - ${horario.hora_fin}
                </div>
                <div class="horario-info">
                    ${horario.tipo_recoleccion === 'organica' ? '🍃' : '♻️'} 
                    ${horario.tipo_recoleccion.charAt(0).toUpperCase() + horario.tipo_recoleccion.slice(1)}
                    ${horario.conductor ? '<br>👤 ' + horario.conductor.nombre_completo : ''}
                </div>
                <div>
                    <span class="horario-status ${horario.activo ? 'activo' : 'inactivo'}">
                        ${horario.activo ? 'ACTIVO' : 'INACTIVO'}
                    </span>
                </div>
                <div class="horario-actions">
                    <button class="btn-secondary btn-sm" onclick="openEditHorario(${horario.id})">
                        ✏️
                    </button>
                    <button class="btn-${horario.activo ? 'danger' : 'success'} btn-sm" 
                            onclick="toggleHorarioStatus(${horario.id}, ${!horario.activo})">
                        ${horario.activo ? '⏸️' : '▶️'}
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Cargar sectores para dropdown
async function loadSectoresDropdown() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_URL}/api/horarios/sectores`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Error al cargar sectores');
        
        const sectores = await response.json();
        const select = document.getElementById('horarioSector');
        
        select.innerHTML = '<option value="">Seleccione un sector...</option>' +
            sectores.map(sector => 
                `<option value="${sector.id}">${sector.nombre} (${sector.zona})</option>`
            ).join('');
            
    } catch (error) {
        console.error('Error:', error);
    }
}

// Cargar conductores para dropdown
async function loadConductoresDropdown() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_URL}/api/operadores/conductores`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Error al cargar conductores');
        
        const conductores = await response.json();
        const select = document.getElementById('horarioConductor');
        
        select.innerHTML = '<option value="">Sin conductor asignado</option>' +
            conductores.map(conductor => 
                `<option value="${conductor.id}">${conductor.nombre_completo}</option>`
            ).join('');
            
    } catch (error) {
        console.error('Error:', error);
    }
}

// Crear nuevo horario
async function createHorario() {
    const errorDiv = document.getElementById('createHorarioError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('active');
    
    try {
        const ruta_id = document.getElementById('horarioRuta').value;
        const tipo_recoleccion = document.getElementById('horarioTipo').value;
        const hora_inicio = document.getElementById('horarioInicio').value;
        const hora_fin = document.getElementById('horarioFin').value;
        const conductor_id = document.getElementById('horarioConductor').value;
        const camion_tipo = document.getElementById('horarioCamionTipo').value;
        
        // Obtener días seleccionados
        const diasCheckboxes = document.querySelectorAll('input[name="horarioDias"]:checked');
        if (diasCheckboxes.length === 0) {
            errorDiv.textContent = 'Debe seleccionar al menos un día';
            errorDiv.classList.add('active');
            return;
        }
        
        const dias_semana = Array.from(diasCheckboxes).map(cb => cb.value).join(',');
        
        if (!ruta_id || !tipo_recoleccion || !hora_inicio || !hora_fin || !conductor_id) {
            errorDiv.textContent = 'Todos los campos obligatorios deben estar completos';
            errorDiv.classList.add('active');
            return;
        }
        
        const horarioData = {
            ruta_id: parseInt(ruta_id),
            tipo_recoleccion,
            dias_semana,
            hora_inicio,
            hora_fin,
            conductor_id: parseInt(conductor_id),
            camion_tipo: camion_tipo || null
        };
        
        showLoading();
        
        const response = await fetch(`${API_URL}/api/horarios/rutas`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(horarioData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al crear horario');
        }
        
        showMessage('Horario creado exitosamente', 'success');
        document.getElementById('createHorarioModal').classList.remove('active');
        document.getElementById('createHorarioForm').reset();
        loadHorarios();
        
    } catch (error) {
        console.error('Error:', error);
        errorDiv.textContent = error.message;
        errorDiv.classList.add('active');
    } finally {
        hideLoading();
    }
}

// Abrir modal de editar horario
async function openEditHorario(horarioId) {
    try {
        showLoading();
        
        const response = await fetch(`${API_URL}/api/horarios/${horarioId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Error al cargar horario');
        
        const horario = await response.json();
        
        // Cargar dropdowns primero
        await loadSectoresDropdown();
        await loadConductoresDropdown();
        
        // Llenar formulario
        document.getElementById('editHorarioId').value = horario.id;
        document.getElementById('editHorarioSector').value = horario.sector_id;
        document.getElementById('editHorarioTipo').value = horario.tipo_recoleccion;
        document.getElementById('editHorarioInicio').value = horario.hora_inicio;
        document.getElementById('editHorarioFin').value = horario.hora_fin;
        document.getElementById('editHorarioConductor').value = horario.conductor_id || '';
        
        // Seleccionar días
        const diasArray = horario.dias_semana.split(',');
        document.querySelectorAll('input[name="editHorarioDias"]').forEach(checkbox => {
            checkbox.checked = diasArray.includes(checkbox.value);
        });
        
        document.getElementById('editHorarioModal').classList.add('active');
        
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al cargar horario', 'error');
    } finally {
        hideLoading();
    }
}

// Actualizar horario
async function updateHorario() {
    const errorDiv = document.getElementById('editHorarioError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('active');
    
    try {
        const horarioId = document.getElementById('editHorarioId').value;
        const sector_id = document.getElementById('editHorarioSector').value;
        const tipo_recoleccion = document.getElementById('editHorarioTipo').value;
        const hora_inicio = document.getElementById('editHorarioInicio').value;
        const hora_fin = document.getElementById('editHorarioFin').value;
        const conductor_id = document.getElementById('editHorarioConductor').value || null;
        
        // Obtener días seleccionados
        const diasCheckboxes = document.querySelectorAll('input[name="editHorarioDias"]:checked');
        if (diasCheckboxes.length === 0) {
            errorDiv.textContent = 'Debe seleccionar al menos un día';
            errorDiv.classList.add('active');
            return;
        }
        
        const dias_semana = Array.from(diasCheckboxes).map(cb => cb.value).join(',');
        
        const horarioData = {
            sector_id: parseInt(sector_id),
            tipo_recoleccion,
            dias_semana,
            hora_inicio,
            hora_fin,
            conductor_id: conductor_id ? parseInt(conductor_id) : null
        };
        
        showLoading();
        
        const response = await fetch(`${API_URL}/api/horarios/${horarioId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(horarioData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al actualizar horario');
        }
        
        showMessage('Horario actualizado exitosamente', 'success');
        document.getElementById('editHorarioModal').classList.remove('active');
        loadHorarios();
        
    } catch (error) {
        console.error('Error:', error);
        errorDiv.textContent = error.message;
        errorDiv.classList.add('active');
    } finally {
        hideLoading();
    }
}

// Activar/desactivar horario
async function toggleHorarioStatus(horarioId, activo) {
    try {
        showLoading();
        
        const response = await fetch(`${API_URL}/api/horarios/${horarioId}/${activo ? 'activar' : 'desactivar'}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Error al actualizar estado');
        
        showMessage(`Horario ${activo ? 'activado' : 'desactivado'} exitosamente`, 'success');
        loadHorarios();
        
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al actualizar estado', 'error');
    } finally {
        hideLoading();
    }
}

// ==================== EJECUCIONES ====================

// Cargar ejecuciones de hoy
async function loadEjecucionesHoy() {
    if (!authToken) return;
    
    showLoading();
    
    try {
        const hoy = new Date().toISOString().split('T')[0];
        const response = await fetch(`${API_URL}/api/horarios/ejecuciones?fecha=${hoy}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) throw new Error('Error al cargar ejecuciones');
        
        const ejecuciones = await response.json();
        displayEjecuciones(ejecuciones);
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al cargar ejecuciones', 'error');
    } finally {
        hideLoading();
    }
}

// Mostrar ejecuciones
function displayEjecuciones(ejecuciones) {
    const grid = document.getElementById('ejecucionesGrid');
    
    if (ejecuciones.length === 0) {
        grid.innerHTML = '<div class="empty-day">No hay ejecuciones programadas para hoy</div>';
        return;
    }
    
    grid.innerHTML = ejecuciones.map(ejecucion => {
        const cumplimiento = ejecucion.porcentaje_cumplimiento || 0;
        
        return `
            <div class="ejecucion-card">
                <div class="ejecucion-header">
                    <div class="ejecucion-sector">${ejecucion.sector.nombre}</div>
                    <span class="ejecucion-status ${ejecucion.estado}">
                        ${ejecucion.estado.toUpperCase().replace('_', ' ')}
                    </span>
                </div>
                <div class="ejecucion-info">
                    <div class="ejecucion-info-item">
                        🕐 <strong>Horario:</strong> ${ejecucion.hora_inicio} - ${ejecucion.hora_fin}
                    </div>
                    <div class="ejecucion-info-item">
                        ${ejecucion.tipo_recoleccion === 'organica' ? '🍃' : '♻️'} 
                        <strong>Tipo:</strong> ${ejecucion.tipo_recoleccion}
                    </div>
                    ${ejecucion.conductor ? `
                        <div class="ejecucion-info-item">
                            👤 <strong>Conductor:</strong> ${ejecucion.conductor.nombre_completo}
                        </div>
                    ` : ''}
                    ${ejecucion.hora_inicio_real ? `
                        <div class="ejecucion-info-item">
                            ▶️ <strong>Inicio real:</strong> ${ejecucion.hora_inicio_real}
                        </div>
                    ` : ''}
                    ${ejecucion.hora_fin_real ? `
                        <div class="ejecucion-info-item">
                            ⏹️ <strong>Fin real:</strong> ${ejecucion.hora_fin_real}
                        </div>
                    ` : ''}
                </div>
                ${ejecucion.estado === 'completada' ? `
                    <div class="ejecucion-progress">
                        <div class="progress-label">
                            <span>Cumplimiento</span>
                            <span><strong>${cumplimiento}%</strong></span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${cumplimiento}%"></div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

// ==================== INICIALIZACIÓN AL CARGAR DOM ====================
document.addEventListener('DOMContentLoaded', () => {
    // Event listeners para modales de horarios
    document.getElementById('createHorarioBtn')?.addEventListener('click', () => {
        document.getElementById('createHorarioForm').reset();
        loadRutasDropdown();
        loadConductoresDropdown();
        document.getElementById('createHorarioModal').classList.add('active');
    });

    document.getElementById('createHorarioForm')?.addEventListener('submit', (e) => {
        e.preventDefault();
        createHorario();
    });

    document.getElementById('editHorarioForm')?.addEventListener('submit', (e) => {
        e.preventDefault();
        updateHorario();
    });
});

// Función auxiliar para mostrar mensajes
function showMessage(message, type = 'info') {
    // Crear elemento de mensaje temporal
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type}`;
    messageDiv.textContent = message;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}


