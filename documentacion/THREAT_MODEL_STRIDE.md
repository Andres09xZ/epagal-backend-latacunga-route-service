# 🛡️ Modelo de Amenazas STRIDE - EPAGAL Backend Latacunga

## 📋 Información del Sistema

| Campo | Detalle |
|-------|---------|
| **Sistema** | Sistema de Gestión de Rutas de Recolección - EPAGAL Latacunga |
| **Versión** | 2.0.1 |
| **Fecha** | Enero 2025 |
| **Autor** | Equipo DevSecOps |
| **Stack** | Python 3.11 + FastAPI + PostgreSQL/PostGIS + Docker |

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐     HTTPS      ┌──────────────────┐     TCP/SSL     ┌──────────────────┐
│   App Móvil     │ ──────────────►│  FastAPI Backend  │ ──────────────►│  PostgreSQL/     │
│   (Flutter)     │                │  (Render.com)     │                │  PostGIS (Neon)  │
└─────────────────┘                └──────┬───────────┘                └──────────────────┘
                                          │
                                          │ HTTP (interno)
                                          ▼
                                   ┌──────────────────┐
                                   │  OSRM Service    │
                                   │  (Docker local)  │
                                   └──────────────────┘
```

### Componentes Principales

| ID | Componente | Tecnología | Ubicación |
|----|-----------|------------|-----------|
| C1 | API Backend | FastAPI 0.115.x | Render.com (PaaS) |
| C2 | Base de Datos | PostgreSQL 16 + PostGIS | Neon Cloud |
| C3 | Motor de Rutas | OSRM | Docker Container |
| C4 | App Móvil | Flutter/React Native | Dispositivos Android |
| C5 | Pipeline CI/CD | GitHub Actions | GitHub Cloud |
| C6 | Registry Docker | Docker Hub | Docker Cloud |

### Flujos de Datos

| ID | Origen | Destino | Protocolo | Datos |
|----|--------|---------|-----------|-------|
| F1 | App Móvil → API | HTTPS/REST | Credenciales, ubicación GPS, incidencias |
| F2 | API → Base de Datos | TCP/SSL | Queries SQL, datos de rutas y usuarios |
| F3 | API → OSRM | HTTP | Coordenadas GPS para cálculo de rutas |
| F4 | GitHub → CI/CD | HTTPS | Código fuente, secretos CI |
| F5 | CI/CD → Docker Hub | HTTPS | Imagen Docker construida |
| F6 | CI/CD → Render | HTTPS | Deploy webhook, configuración |

---

## 🔍 Análisis STRIDE por Componente

### C1: API Backend (FastAPI en Render.com)

#### S - Suplantación de Identidad (Spoofing)

| ID | Amenaza | Probabilidad | Impacto | Riesgo | Mitigación |
|----|---------|-------------|---------|--------|------------|
| S1.1 | Atacante obtiene tokens JWT y suplanta usuarios | Media | Alto | **Alto** | ✅ Tokens con expiración, HTTPBearer scheme, validación en `get_current_user()` |
| S1.2 | Fuerza bruta en endpoint `/api/auth/login` | Alta | Alto | **Alto** | ⚠️ **Pendiente**: Implementar rate limiting con slowapi |
| S1.3 | Suplantación de rol admin | Baja | Crítico | **Alto** | ✅ Verificación de rol en `get_current_admin()` |
| S1.4 | Token replay attack | Media | Medio | **Medio** | ⚠️ **Parcial**: Tokens expiran pero no hay blacklist de tokens revocados |

#### T - Manipulación (Tampering)

| ID | Amenaza | Probabilidad | Impacto | Riesgo | Mitigación |
|----|---------|-------------|---------|--------|------------|
| T1.1 | Inyección SQL a través de parámetros de API | Baja | Crítico | **Medio** | ✅ SQLAlchemy ORM, queries parametrizadas, Semgrep SAST |
| T1.2 | Manipulación de coordenadas GPS en reportes | Media | Medio | **Medio** | ⚠️ **Parcial**: Validación de schemas Pydantic, falta validación de rango geográfico |
| T1.3 | Modificación de datos en tránsito | Baja | Alto | **Medio** | ✅ HTTPS obligatorio en Render.com |
| T1.4 | Mass assignment en modelos | Baja | Alto | **Medio** | ✅ Schemas Pydantic separados para request/response |

#### R - Repudiación (Repudiation)

| ID | Amenaza | Probabilidad | Impacto | Riesgo | Mitigación |
|----|---------|-------------|---------|--------|------------|
| R1.1 | Conductor niega haber reportado una incidencia | Media | Medio | **Medio** | ⚠️ **Parcial**: Se registra usuario pero no hay audit trail completo |
| R1.2 | Admin niega cambios en configuración | Media | Alto | **Alto** | ❌ **No implementado**: Falta logging de auditoría para acciones admin |
| R1.3 | Falta de trazabilidad en cambios de rutas | Media | Medio | **Medio** | ⚠️ **Parcial**: Git history pero sin audit log en aplicación |

#### I - Divulgación de Información (Information Disclosure)

| ID | Amenaza | Probabilidad | Impacto | Riesgo | Mitigación |
|----|---------|-------------|---------|--------|------------|
| I1.1 | Exposición de stack traces en errores | Baja | Medio | **Bajo** | ✅ FastAPI manejo de errores, verificado en DAST |
| I1.2 | Exposición de endpoints en OpenAPI/docs | Media | Bajo | **Bajo** | ⚠️ **Parcial**: `/docs` y `/openapi.json` accesibles (útil en desarrollo) |
| I1.3 | Secretos expuestos en código fuente | Baja | Crítico | **Medio** | ✅ Gitleaks + TruffleHog en pipeline, variables de entorno |
| I1.4 | Datos sensibles en logs | Media | Medio | **Medio** | ⚠️ **Parcial**: No hay política clara de logging sanitizado |

#### D - Denegación de Servicio (Denial of Service)

| ID | Amenaza | Probabilidad | Impacto | Riesgo | Mitigación |
|----|---------|-------------|---------|--------|------------|
| D1.1 | Flood de peticiones a la API | Alta | Alto | **Alto** | ⚠️ **Pendiente**: Rate limiting con slowapi |
| D1.2 | Queries costosas (cálculo de rutas masivo) | Media | Alto | **Alto** | ⚠️ **Parcial**: No hay límite de cálculos de ruta simultáneos |
| D1.3 | Render free tier sleep/cold start | Alta | Medio | **Medio** | ⚠️ **Inherente**: Limitación del plan gratuito |

#### E - Elevación de Privilegios (Elevation of Privilege)

| ID | Amenaza | Probabilidad | Impacto | Riesgo | Mitigación |
|----|---------|-------------|---------|--------|------------|
| E1.1 | Conductor accede a funciones de admin | Baja | Crítico | **Medio** | ✅ `get_current_admin()` verifica rol en cada endpoint admin |
| E1.2 | IDOR - Acceso a datos de otros usuarios | Media | Alto | **Alto** | ⚠️ **Parcial**: Depende de la implementación por endpoint |
| E1.3 | Escalada a través de JWT manipulado | Baja | Crítico | **Medio** | ✅ Firma JWT con SECRET_KEY, validación con python-jose |

---

### C2: Base de Datos (PostgreSQL/Neon)

| Cat | ID | Amenaza | Riesgo | Mitigación |
|-----|-----|---------|--------|------------|
| S | S2.1 | Acceso no autorizado a la base de datos | **Medio** | ✅ Neon Cloud con SSL obligatorio, credenciales en variables de entorno |
| T | T2.1 | Inyección SQL directa | **Bajo** | ✅ SQLAlchemy ORM, parameterized queries verificadas por Semgrep |
| T | T2.2 | Modificación directa de datos en Neon | **Bajo** | ✅ Acceso restringido por Neon IAM |
| I | I2.1 | Backup de datos expuestos | **Medio** | ✅ Neon gestiona backups cifrados |
| I | I2.2 | Connection string expuesta | **Bajo** | ✅ Gitleaks + TruffleHog detectan credenciales |
| D | D2.1 | Agotamiento de conexiones pool | **Medio** | ✅ Pool configurado en database.py (pool_size, max_overflow) |

---

### C3: OSRM Service (Docker)

| Cat | ID | Amenaza | Riesgo | Mitigación |
|-----|-----|---------|--------|------------|
| S | S3.1 | Acceso externo al servicio OSRM | **Bajo** | ✅ Solo accesible desde red interna Docker |
| T | T3.1 | Manipulación de datos de mapas | **Bajo** | ✅ Datos OSM precargados y verificados |
| D | D3.1 | Queries de rutas extremadamente largas | **Medio** | ⚠️ **Parcial**: Sin límite de distancia en peticiones |
| I | I3.1 | OSRM usa HTTP sin cifrar | **Bajo** | ✅ Comunicación interna, `# nosemgrep` documentado |

---

### C5: Pipeline CI/CD (GitHub Actions)

| Cat | ID | Amenaza | Riesgo | Mitigación |
|-----|-----|---------|--------|------------|
| S | S5.1 | Compromiso de GitHub Actions secrets | **Medio** | ✅ Secrets cifrados, rotación periódica recomendada |
| T | T5.1 | Supply chain attack en actions | **Medio** | ✅ Dependabot monitorea github-actions, versiones pinneadas |
| T | T5.2 | Inyección en workflow scripts | **Bajo** | ✅ No se usan inputs de usuario directos en scripts |
| I | I5.1 | Logs de CI exponen secretos | **Bajo** | ✅ GitHub enmascara secrets automáticamente |
| E | E5.1 | PR malicioso ejecuta código en pipeline | **Medio** | ✅ Pipeline solo se ejecuta en push a main (no en PRs de forks) |

---

### C6: Docker Registry (Docker Hub)

| Cat | ID | Amenaza | Riesgo | Mitigación |
|-----|-----|---------|--------|------------|
| S | S6.1 | Imagen Docker suplantada | **Medio** | ⚠️ **Parcial**: No se usa Docker Content Trust (firma de imágenes) |
| T | T6.1 | Imagen base comprometida | **Medio** | ✅ Trivy escanea imagen, Dependabot monitorea base image |
| I | I6.1 | Secretos embebidos en imagen | **Bajo** | ✅ Trivy fs scan + .dockerignore configurado |

---

## 📊 Matriz de Riesgo Consolidada

```
         │ Bajo    │ Medio   │ Alto    │ Crítico
─────────┼─────────┼─────────┼─────────┼─────────
Muy Alta │         │ D1.3    │ S1.2    │
         │         │         │ D1.1    │
─────────┼─────────┼─────────┼─────────┼─────────
Alta     │         │         │         │
─────────┼─────────┼─────────┼─────────┼─────────
Media    │ I1.2    │ T1.2    │ R1.2    │
         │         │ R1.1    │ E1.2    │
         │         │ R1.3    │         │
         │         │ I1.4    │         │
─────────┼─────────┼─────────┼─────────┼─────────
Baja     │ I1.1    │ T1.1    │         │
         │ I3.1    │ S1.4    │         │
         │ T3.1    │ I1.3    │         │
         │         │ E1.3    │         │
```

---

## 🎯 Top 10 Riesgos Prioritarios

| # | ID | Amenaza | Riesgo | Estado | Acción Requerida |
|---|-----|---------|--------|--------|-----------------|
| 1 | S1.2 | Fuerza bruta en login | **Alto** | 🔄 En progreso | Implementar rate limiting con slowapi |
| 2 | D1.1 | Flood de peticiones | **Alto** | 🔄 En progreso | Rate limiting global |
| 3 | R1.2 | Sin audit log de admin | **Alto** | ❌ Pendiente | Implementar audit logging |
| 4 | E1.2 | IDOR en endpoints | **Alto** | ⚠️ Parcial | Revisar autorización por recurso |
| 5 | S1.4 | Token replay | **Medio** | ⚠️ Parcial | Considerar token blacklist |
| 6 | D1.2 | Queries costosas | **Medio** | ⚠️ Parcial | Limitar cálculos de ruta |
| 7 | T1.2 | GPS spoofing | **Medio** | ⚠️ Parcial | Validar rango geográfico Latacunga |
| 8 | I1.4 | Datos sensibles en logs | **Medio** | ⚠️ Parcial | Política de sanitización de logs |
| 9 | S6.1 | Imagen Docker sin firmar | **Medio** | ⚠️ Parcial | Evaluar Docker Content Trust |
| 10 | I1.2 | OpenAPI público | **Bajo** | ⚠️ Parcial | Desactivar `/docs` en producción |

---

## ✅ Controles Existentes

| Control | Herramienta | Fase DevSecOps | Amenazas Mitigadas |
|---------|------------|----------------|---------------------|
| Escaneo de secretos | Gitleaks + TruffleHog | Code | I1.3, I2.2 |
| Análisis de dependencias | pip-audit + Safety | Build | T6.1 |
| SAST | Bandit + Semgrep | Build | T1.1, T2.1 |
| Seguridad SQL | SQLFluff + grep | Test | T1.1, T2.1 |
| Testing de seguridad | pytest + validaciones | Test | T1.4, I1.1 |
| Seguridad de contenedor | Hadolint + Trivy | Deploy | T6.1, I6.1 |
| DAST | OWASP ZAP | Test | I1.1, I1.2, D1.1 |
| Monitoreo dependencias | Dependabot | Monitor | T6.1, S6.1 |
| Pre-commit hooks | Gitleaks + Bandit + Flake8 | Code | I1.3, T1.1 |
| Autenticación JWT | python-jose + HTTPBearer | Runtime | S1.1, S1.3, E1.1 |
| RBAC | get_current_admin() | Runtime | E1.1, E1.3 |
| CORS configurado | FastAPI CORSMiddleware | Runtime | Varios |
| HTTPS | Render.com TLS | Runtime | T1.3 |

---

## 🗺️ Mapeo OWASP Top 10 (2021)

| OWASP | Categoría | Amenazas Relacionadas | Cobertura |
|-------|-----------|----------------------|-----------|
| A01 | Broken Access Control | E1.1, E1.2, S1.1 | ✅ Parcial |
| A02 | Cryptographic Failures | I1.3, I2.2 | ✅ Cubierto |
| A03 | Injection | T1.1, T2.1 | ✅ Cubierto |
| A04 | Insecure Design | R1.2, T1.2 | ⚠️ Parcial |
| A05 | Security Misconfiguration | I1.2, I3.1 | ✅ Parcial |
| A06 | Vulnerable Components | T6.1 | ✅ Cubierto |
| A07 | Auth & Identification Failures | S1.2, S1.4 | ⚠️ Parcial |
| A08 | Software & Data Integrity | T5.1, S6.1 | ✅ Parcial |
| A09 | Security Logging & Monitoring | R1.1, R1.2, I1.4 | ❌ Débil |
| A10 | SSRF | Bajo riesgo (OSRM interno) | ✅ Cubierto |

---

## 📝 Plan de Remediación

### Prioridad Alta (Implementar ahora)
1. **Rate Limiting** → slowapi en endpoints críticos
2. **Audit Logging** → Registrar acciones de admin con timestamp y usuario

### Prioridad Media (Sprint siguiente)
3. **Validación geográfica** → Coordenadas dentro del rango de Latacunga
4. **Sanitización de logs** → Filtrar datos sensibles antes de log
5. **IDOR review** → Auditar autorización por recurso en cada endpoint

### Prioridad Baja (Backlog)
6. **Token blacklist** → Redis para revocar tokens
7. **Docker Content Trust** → Firmar imágenes
8. **Desactivar /docs en prod** → Configurar por variable de entorno

---

*Documento generado como parte del proceso DevSecOps - Fase Plan*
*Última actualización: Enero 2025*
