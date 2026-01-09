Feature: Sistema de Geofencing y Alertas GPS
  Como operador de EPAGAL
  Quiero recibir alertas automáticas cuando los conductores se desvían
  Para tomar acciones correctivas inmediatas

  Background:
    Given el sistema de geofencing está activo
    And existen las siguientes configuraciones de alertas:
      | parametro                  | valor |
      | velocidad_maxima_kmh       | 80    |
      | distancia_desviacion_m     | 500   |
      | tiempo_parada_min          | 15    |
      | precision_minima_gps_m     | 50    |

  # ===================================================================
  # ESCENARIOS: Detección de Desviación de Ruta
  # ===================================================================

  Scenario: Conductor dentro de ruta planificada - Sin alerta
    Given el conductor "Juan Pérez" con ID 1 tiene una ruta asignada
    And la ruta pasa por los siguientes puntos:
      | orden | latitud   | longitud  | descripcion       |
      | 1     | -0.9356   | -78.6217  | Depósito EPAGAL   |
      | 2     | -0.9365   | -78.6215  | Incidencia A      |
      | 3     | -0.9375   | -78.6210  | Incidencia B      |
    When el conductor reporta su posición GPS:
      | latitud   | longitud  | precision_m | velocidad_kmh |
      | -0.9360   | -78.6216  | 10          | 35            |
    Then NO se genera ninguna alerta
    And la distancia a la ruta es menor a 100 metros
    And el estado del conductor es "en_ruta_normal"

  Scenario: Conductor se desvía 600 metros - Alerta generada
    Given el conductor "María López" con ID 2 tiene una ruta asignada
    And la ruta va desde (-0.9356, -78.6217) hasta (-0.9375, -78.6210)
    When el conductor reporta su posición GPS:
      | latitud   | longitud  | precision_m | velocidad_kmh |
      | -0.9400   | -78.6150  | 15          | 40            |
    Then se genera una alerta de tipo "desviacion_ruta"
    And la alerta contiene:
      | campo                      | valor esperado        |
      | severidad                  | warning               |
      | distancia_desviacion_m     | aproximadamente 600   |
      | conductor_id               | 2                     |
      | latitud_actual             | -0.9400               |
      | longitud_actual            | -78.6150              |
    And se notifica al operador en tiempo real
    And se registra el evento en la base de datos

  Scenario: Conductor se desvía múltiples veces - Escalamiento de severidad
    Given el conductor con ID 3 tiene ruta asignada
    And se generó 1 alerta de desviación hace 5 minutos
    When el conductor se desvía nuevamente 700 metros
    Then se genera una alerta con severidad "critical"
    And el contador de desviaciones incrementa a 2
    And se envía notificación push al supervisor

  Scenario: Conductor regresa a la ruta después de desviación
    Given el conductor con ID 4 tiene alerta activa de desviación
    And se desvió 600 metros hace 3 minutos
    When el conductor reporta posición dentro de la ruta:
      | latitud   | longitud  | precision_m |
      | -0.9365   | -78.6215  | 12          |
    Then la alerta se marca como "resuelta"
    And se registra el tiempo de desviación: 3 minutos
    And se calcula el exceso de distancia recorrida

  # ===================================================================
  # ESCENARIOS: Control de Velocidad
  # ===================================================================

  Scenario: Conductor respeta límite de velocidad - Sin alerta
    Given el conductor con ID 5 está en ruta
    When el conductor reporta velocidad de 75 km/h
    Then NO se genera alerta de velocidad
    And se registra la velocidad en el historial

  Scenario: Conductor excede límite de velocidad - Alerta generada
    Given el conductor "Carlos Sánchez" con ID 6 está en ruta
    And el límite de velocidad es 80 km/h
    When el conductor reporta su posición:
      | latitud   | longitud  | velocidad_kmh | precision_m |
      | -0.9370   | -78.6220  | 95            | 8           |
    Then se genera una alerta de tipo "velocidad_excesiva"
    And la alerta contiene:
      | campo               | valor |
      | severidad           | warning |
      | velocidad_actual    | 95    |
      | velocidad_maxima    | 80    |
      | exceso_kmh          | 15    |
      | conductor_id        | 6     |
    And se envía notificación al conductor
    And se registra el evento con timestamp

  Scenario: Conductor excede velocidad crítica - Alerta severa
    Given el conductor con ID 7 está en ruta
    When el conductor reporta velocidad de 120 km/h
    Then se genera una alerta con severidad "critical"
    And se envía notificación inmediata al supervisor
    And se registra como incidente de seguridad
    And se sugiere acción: "Contactar conductor inmediatamente"

  Scenario: Múltiples excesos de velocidad - Patrón de conducción peligrosa
    Given el conductor con ID 8 tiene ruta asignada
    And se generaron 3 alertas de velocidad en los últimos 30 minutos
    When el conductor excede nuevamente el límite
    Then se genera alerta con severidad "critical"
    And se marca al conductor con "patrón_conduccion_peligrosa"
    And se recomienda: "Evaluar para re-capacitación"

  # ===================================================================
  # ESCENARIOS: Detección de Paradas Prolongadas
  # ===================================================================

  Scenario: Conductor hace parada corta - Sin alerta
    Given el conductor con ID 9 está en ruta
    When el conductor permanece detenido durante 8 minutos en:
      | latitud   | longitud  |
      | -0.9365   | -78.6215  |
    Then NO se genera alerta de parada prolongada
    And se registra la parada como normal

  Scenario: Conductor hace parada prolongada sin justificación - Alerta
    Given el conductor "Ana Martínez" con ID 10 está en ruta
    And no hay incidencias programadas en su posición actual
    When el conductor permanece detenido durante 20 minutos en:
      | latitud   | longitud  |
      | -0.9380   | -78.6200  |
    Then se genera una alerta de tipo "parada_prolongada"
    And la alerta contiene:
      | campo                  | valor |
      | severidad              | info  |
      | duracion_minutos       | 20    |
      | conductor_id           | 10    |
      | latitud                | -0.9380 |
      | longitud               | -78.6200 |
    And se solicita confirmación al conductor
    And se registra como posible anomalía

  Scenario: Conductor detenido en ubicación de incidencia - Sin alerta
    Given el conductor con ID 11 está en ruta
    And la próxima incidencia está en (-0.9365, -78.6215)
    And el tiempo estimado de trabajo es 30 minutos
    When el conductor permanece detenido 25 minutos en:
      | latitud   | longitud  |
      | -0.9365   | -78.6215  |
    Then NO se genera alerta de parada prolongada
    And se registra como "trabajando_en_incidencia"

  Scenario: Conductor detenido fuera de horario laboral - Alerta crítica
    Given el conductor con ID 12 está en ruta
    And la hora actual es 22:30
    And el horario laboral termina a las 16:00
    When el conductor permanece detenido 60 minutos
    Then se genera alerta con severidad "critical"
    And se notifica al supervisor de turno
    And se registra como posible incidente de seguridad

  # ===================================================================
  # ESCENARIOS: Zonas Geográficas Restringidas
  # ===================================================================

  Scenario: Conductor entra a zona de cobertura correcta
    Given el conductor con ID 13 está asignado a zona "occidental"
    When el conductor reporta posición en:
      | latitud   | longitud  |
      | -0.9356   | -78.6217  |
    Then la posición está dentro de zona "occidental"
    And NO se genera alerta de zona

  Scenario: Conductor sale del área de cobertura de EPAGAL - Alerta
    Given el conductor con ID 14 está en ruta
    And el área de cobertura de EPAGAL está delimitada por:
      | latitud   | longitud  |
      | -0.9200   | -78.6300  |
      | -0.9200   | -78.5900  |
      | -0.9500   | -78.5900  |
      | -0.9500   | -78.6300  |
    When el conductor reporta posición en:
      | latitud   | longitud  |
      | -1.0000   | -79.0000  |
    Then se genera alerta de tipo "fuera_zona_cobertura"
    And la alerta tiene severidad "critical"
    And se solicita explicación al conductor

  Scenario: Conductor entra a zona de otra cuadrilla - Alerta
    Given el conductor con ID 15 está asignado a zona "occidental"
    And la zona "oriental" está asignada a otras cuadrillas
    When el conductor reporta posición en zona "oriental":
      | latitud   | longitud  |
      | -0.9400   | -78.6000  |
    Then se genera alerta de tipo "zona_incorrecta"
    And se notifica al operador
    And se sugiere reasignación de ruta

  # ===================================================================
  # ESCENARIOS: Precisión GPS y Validación de Datos
  # ===================================================================

  Scenario: GPS con buena precisión - Datos aceptados
    Given el conductor con ID 16 está en ruta
    When el conductor reporta posición con precisión de 10 metros
    Then los datos GPS se aceptan
    And se procesa la posición normalmente

  Scenario: GPS con baja precisión - Alerta de calidad de datos
    Given el conductor con ID 17 está en ruta
    And la precisión mínima requerida es 50 metros
    When el conductor reporta posición con precisión de 200 metros
    Then se genera alerta de tipo "precision_gps_baja"
    And la posición NO se usa para cálculos críticos
    And se notifica al conductor para mejorar señal GPS

  Scenario: Posición GPS inválida - Rechazo de datos
    Given el conductor con ID 18 intenta enviar posición
    When el conductor reporta coordenadas:
      | latitud   | longitud  |
      | 200.0     | -500.0    |
    Then los datos son rechazados con código 422
    And el mensaje de error es "Coordenadas GPS inválidas"
    And NO se procesa la actualización

  Scenario: Salto temporal en posiciones GPS - Detección de anomalía
    Given el conductor con ID 19 envió última posición hace 30 segundos en:
      | latitud   | longitud  |
      | -0.9356   | -78.6217  |
    When el conductor reporta nueva posición:
      | latitud   | longitud  | velocidad_kmh |
      | -0.9500   | -78.5900  | 45            |
    Then se detecta "salto_temporal_anomalo"
    And se calcula que la distancia requeriría velocidad > 300 km/h
    And se genera alerta de datos inconsistentes

  # ===================================================================
  # ESCENARIOS: Integración con Sistema de Rutas
  # ===================================================================

  Scenario: Calcular ETA dinámico con posición actual
    Given el conductor con ID 20 está en ruta
    And la próxima incidencia está en (-0.9375, -78.6210)
    And el conductor está en (-0.9356, -78.6217)
    When el sistema calcula el ETA
    Then la distancia restante es aproximadamente 2.1 km
    And el tiempo estimado es entre 3 y 5 minutos
    And el ETA se actualiza en el dashboard

  Scenario: Re-optimizar ruta ante desviación significativa
    Given el conductor con ID 21 tiene 5 incidencias pendientes
    And se desvió 2 km de la ruta original
    When el operador solicita re-optimización
    Then el sistema calcula nueva ruta desde posición actual
    And se envía la nueva ruta al conductor
    And se recalculan todos los ETAs

  # ===================================================================
  # ESCENARIOS: Historial y Reportes
  # ===================================================================

  Scenario: Consultar historial de alertas de un conductor
    Given el conductor con ID 22 trabajó durante enero 2026
    And se generaron 15 alertas en ese período:
      | tipo                | cantidad |
      | desviacion_ruta     | 8        |
      | velocidad_excesiva  | 5        |
      | parada_prolongada   | 2        |
    When consulto el historial de alertas del conductor
    Then obtengo las 15 alertas ordenadas por fecha
    And puedo filtrar por tipo de alerta
    And puedo ver detalles geográficos en mapa

  Scenario: Generar reporte de seguridad mensual
    Given existen 50 conductores activos
    And se generaron 200 alertas en el último mes
    When genero reporte de seguridad de geofencing
    Then obtengo estadísticas:
      | métrica                        | valor |
      | total_alertas                  | 200   |
      | conductores_con_alertas        | 35    |
      | promedio_alertas_por_conductor | 5.7   |
      | tipo_más_frecuente             | desviacion_ruta |
    And se identifican conductores con mayor número de alertas
    And se sugieren acciones correctivas
