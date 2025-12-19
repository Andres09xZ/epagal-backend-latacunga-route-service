// Configuración
const API_URL = 'http://localhost:9000';
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
    
    try {
        const response = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            throw new Error('Credenciales inválidas');
        }
        
        const data = await response.json();
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
            alert(`✅ Incidencia validada exitosamente\n🗺️ Se generó la ruta #${result.ruta_generada_id}`);
        } else {
            alert('✅ Incidencia validada exitosamente');
        }
        
        loadIncidencias();
        
    } catch (error) {
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
                            <span class="info-label">Asignaciones:</span>
                            <span class="info-value">${ruta.asignaciones.length}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
                <div class="card-footer">
                    ${ruta.estado === 'planeada' ? `
                        <button onclick="showAsignarModal(${ruta.id})" class="btn btn-primary btn-sm">👷 Asignar Conductor</button>
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
    
    // Cargar conductores disponibles
    try {
        const response = await fetch(`${API_URL}/api/conductores/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const conductores = await response.json();
        
        const select = document.getElementById('asignarConductor');
        select.innerHTML = '<option value="">Seleccione un conductor...</option>' +
            conductores
                .filter(c => c.estado === 'activo')
                .map(c => `<option value="${c.id}">${c.nombre_completo} - ${c.cedula}</option>`)
                .join('');
        
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

// Cerrar modales al hacer clic fuera
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});
