/**
 * Configuración de la aplicación móvil
 * 
 * INSTRUCCIONES:
 * 1. Copia este archivo a tu proyecto Expo:
 *    D:\Octavo Semestre\Tesis\front_end_latacunga_clean\app_latacunga_clean\config.js
 * 
 * 2. Importa en tus componentes:
 *    import config from './config';
 * 
 * 3. Usa en tus peticiones:
 *    fetch(`${config.API_URL}/api/incidencias/`, { ... })
 */

// Configuración del entorno
const ENV = {
  dev: {
    API_URL: 'http://192.168.100.31:8000',  // Tu IP local para desarrollo
    DEBUG: true,
  },
  prod: {
    API_URL: 'https://epagal-backend-routing-latest.onrender.com',
    DEBUG: false,
  },
};

// Cambiar a 'prod' para usar el servidor de producción
const CURRENT_ENV = 'dev';

export default {
  ...ENV[CURRENT_ENV],
  
  // Endpoints principales
  endpoints: {
    // Incidencias
    incidencias: '/api/incidencias/',
    validarIncidencia: (id) => `/api/incidencias/${id}/validate`,
    
    // Rutas
    rutasPorZona: (zona) => `/api/rutas/zona/${zona}`,
    rutaDetalle: (id) => `/api/rutas/${id}`,
    rutaDetalles: (id) => `/api/rutas/${id}/detalles`,
    
    // Conductores
    conductores: '/api/conductores/',
    conductorPorId: (id) => `/api/conductores/${id}`,
  },
};

/**
 * EJEMPLO DE USO EN TU APP:
 * 
 * import config from './config';
 * 
 * // Crear incidencia
 * const crearIncidencia = async (datos) => {
 *   try {
 *     const response = await fetch(
 *       `${config.API_URL}${config.endpoints.incidencias}`,
 *       {
 *         method: 'POST',
 *         headers: {
 *           'Content-Type': 'application/json',
 *         },
 *         body: JSON.stringify(datos),
 *       }
 *     );
 *     const data = await response.json();
 *     return data;
 *   } catch (error) {
 *     if (config.DEBUG) {
 *       console.error('Error creando incidencia:', error);
 *     }
 *     throw error;
 *   }
 * };
 * 
 * // Validar incidencia
 * const validarIncidencia = async (id) => {
 *   const response = await fetch(
 *     `${config.API_URL}${config.endpoints.validarIncidencia(id)}`,
 *     { method: 'POST' }
 *   );
 *   return await response.json();
 * };
 * 
 * // Obtener rutas por zona
 * const obtenerRutas = async (zona) => {
 *   const response = await fetch(
 *     `${config.API_URL}${config.endpoints.rutasPorZona(zona)}`
 *   );
 *   return await response.json();
 * };
 */
