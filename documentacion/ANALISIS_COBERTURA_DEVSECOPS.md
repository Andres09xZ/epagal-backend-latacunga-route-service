# Análisis de Cobertura del Ciclo de Vida DevSecOps

## Referencia: Modelo de 6 Fases DevSecOps

```
            ┌──────────────────────────────────────────────────┐
            │              PRE-PRODUCCIÓN                      │
            │                                                  │
            │    ┌─────────┐                                   │
            │    │ 1. PLAN │ Threat modeling,                  │
            │    │         │ change impact analysis            │
            │    └─────────┘                                   │
            │                                                  │
            │    ┌──────────┐                                  │
            │    │ 2. BUILD │ Pre-commit hooks, SCA, SAST,     │
            │    │          │ code review, container security, │
            │    │          │ vulnerability scanning, DAST     │
            │    └──────────┘                                  │
            │                                                  │
            │    ┌─────────┐                                   │
            │    │ 3. TEST │ DAST                              │
            │    │         │                                   │
            │    └─────────┘                                   │
            │                                                  │
            ├──────────────────────────────────────────────────┤
            │              PRODUCCIÓN                          │
            │                                                  │
            │    ┌───────────┐                                 │
            │    │ 4. DEPLOY │ Access and configuration        │
            │    │           │ management, chaos engineering,  │
            │    │           │ pen testing                     │
            │    └───────────┘                                 │
            │                                                  │
            │    ┌───────────┐                                 │
            │    │ 5. OPERATE│ Log collection, RASP,           │
            │    │           │ Patching, WAF                   │
            │    └───────────┘                                 │
            │                                                  │
            │    ┌───────────┐                                 │
            │    │ 6. MONITOR│ SIEM, vulnerability monitoring, │
            │    │           │ access control                  │
            │    └───────────┘                                 │
            │                                                  │
            └──────────────────────────────────────────────────┘
```

---

## Evaluación por Fase

### ✅ = Implementado | ⚠️ = Parcialmente implementado | ❌ = No implementado

---

### FASE 1: PLAN (Pre-producción)

| Actividad esperada | Estado | Implementación actual | Observación |
|---|---|---|---|
| Threat modeling | ✅ | Documento STRIDE completo en `documentacion/THREAT_MODEL_STRIDE.md` | Cubre los 6 componentes del sistema, mapeo OWASP Top 10, Top 10 riesgos priorizados |
| Change impact analysis | ⚠️ | Pull Requests en GitHub, pero sin análisis formal de impacto de seguridad | Los PRs a `main` disparan el pipeline DevSecOps, lo cual es una forma automatizada de análisis de impacto |

**Cobertura de la fase: ~55%** ↑ (antes: 20%)

**Mejoras implementadas:**
- ✅ Documento formal de modelado de amenazas STRIDE
- ✅ Matriz de riesgo consolidada con priorización
- ✅ Mapeo completo a OWASP Top 10 (2021)
- ✅ Plan de remediación con prioridades

---

### FASE 2: BUILD (Pre-producción)

| Actividad esperada | Estado | Implementación actual | Herramientas |
|---|---|---|---|
| Pre-commit hooks | ✅ | `.pre-commit-config.yaml` configurado con Gitleaks, Bandit, Flake8 y pre-commit-hooks | Validación local antes de cada commit |
| Software Composition Analysis (SCA) | ✅ | **Paso 2 del pipeline** — Análisis completo de dependencias | pip-audit, Safety, pip-licenses |
| SAST | ✅ | **Paso 3 del pipeline** — Análisis estático completo con múltiples herramientas | Bandit, Semgrep (6 packs OWASP), Flake8 |
| Code review | ⚠️ | GitHub PRs disponibles pero no hay branch protection rules que exijan reviews | No hay política obligatoria de code review |
| Container security | ✅ | **Paso 6 del pipeline** — Lint de Dockerfile + escaneo de imagen | Hadolint, Trivy |
| Vulnerability scanning | ✅ | **Pasos 1, 2, 3, 4, 6** — Escaneo multicapa | TruffleHog, Gitleaks, pip-audit, Semgrep, Trivy |
| DAST | ✅ | **Paso 7 del pipeline** — Escaneo dinámico de la aplicación en producción | OWASP ZAP (API scan + baseline scan + verificación custom) |

**Cobertura de la fase: ~90%** ↑ (antes: 65%)

**Mejoras implementadas:**
- ✅ Pre-commit hooks con Gitleaks, Bandit, Flake8 y validaciones de archivos
- ✅ DAST con OWASP ZAP (escaneo de API y baseline)
- ⚠️ Pendiente: Branch protection rules con code review obligatorio

---

### FASE 3: TEST (Pre-producción)

| Actividad esperada | Estado | Implementación actual | Herramientas |
|---|---|---|---|
| DAST | ✅ | **Paso 7 del pipeline** — OWASP ZAP API scan + baseline scan contra producción | OWASP ZAP (zaproxy/action-api-scan, zaproxy/action-baseline) |
| Tests de seguridad funcionales | ✅ | **Paso 5 del pipeline** — Validación de imports, inicialización FastAPI, configuración de seguridad | pytest, scripts de validación Python |
| Tests de integración de seguridad | ⚠️ | Tests existentes son de integración manual (requieren servidor), no se ejecutan en CI completamente | pytest con tests manuales en `tests/` |
| Verificación de headers | ✅ | **Paso 7 DAST** — Verificación automática de X-Content-Type-Options, X-Frame-Options, HSTS, CORS | Scripts custom en pipeline |

**Cobertura de la fase: ~70%** ↑ (antes: 25%)

**Mejoras implementadas:**
- ✅ DAST con OWASP ZAP (API scan + baseline scan)
- ✅ Verificación automática de security headers
- ✅ Verificación de protección de endpoints autenticados
- ✅ Verificación de manejo seguro de errores

---

### FASE 4: DEPLOY (Producción)

| Actividad esperada | Estado | Implementación actual | Herramientas |
|---|---|---|---|
| Access management | ⚠️ | Secrets de GitHub para DOCKER_USERNAME, DOCKER_PASSWORD, RENDER_API_KEY, SERVICE_ID | GitHub Secrets, pero no hay rotación automatizada |
| Configuration management | ✅ | Variables de entorno para configuración, `.env` excluido del repo, Dockerfile seguro | dotenv, GitHub Secrets, .dockerignore |
| Security gate (deploy gating) | ✅ | **deploy.yml** solo se ejecuta si DevSecOps Pipeline pasa exitosamente | workflow_run + security-gate job |
| Chaos engineering | ❌ | No hay pruebas de resiliencia ni caos | No se usa Chaos Monkey, Litmus ni similar |
| Pen testing | ❌ | No hay pruebas de penetración automatizadas | Mencionado en Product Backlog como pendiente |

**Cobertura de la fase: ~45%**

**¿Qué falta?**
- Rotación automatizada de secretos
- Pruebas de penetración (al menos automatizadas con ZAP)
- Pruebas de resiliencia/caos básicas (health check recovery)

---

### FASE 5: OPERATE (Producción)

| Actividad esperada | Estado | Implementación actual | Herramientas |
|---|---|---|---|
| Log collection | ⚠️ | La app usa `logging` de Python, Render captura stdout | logging estándar de Python, Render logs |
| RASP (Runtime App Self-Protection) | ⚠️ | Rate limiting implementado con slowapi (5/min login, 200/min global) + Security Headers Middleware | slowapi, SecurityHeadersMiddleware |
| Patching | ✅ | Dependabot monitorea pip, github-actions y docker; pip-audit y Safety detectan vulnerabilidades | GitHub Dependabot, pip-audit, Safety |
| WAF (Web Application Firewall) | ❌ | No hay WAF frente a la aplicación | Render no incluye WAF en el plan gratuito |

**Cobertura de la fase: ~45%** ↑ (antes: 20%)

**Mejoras implementadas:**
- ✅ Rate limiting con slowapi (protección contra fuerza bruta y DDoS)
- ✅ Security Headers Middleware (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, etc.)
- ✅ Dependabot para patching automatizado de dependencias
- ⚠️ Pendiente: WAF con Cloudflare free tier, centralización de logs

---

### FASE 6: MONITOR (Producción)

| Actividad esperada | Estado | Implementación actual | Herramientas |
|---|---|---|---|
| SIEM | ❌ | No hay sistema de gestión de eventos de seguridad | No se usa Splunk, ELK, Wazuh |
| Vulnerability monitoring | ✅ | Dependabot monitorea vulnerabilidades en pip, github-actions y docker semanalmente | GitHub Dependabot + DevSecOps pipeline en cada push |
| Access control | ⚠️ | JWT para autenticación de API, pero no hay auditoría de accesos | python-jose, passlib[bcrypt] |

**Cobertura de la fase: ~40%** ↑ (antes: 15%)

**Mejoras implementadas:**
- ✅ Dependabot para monitoreo continuo de vulnerabilidades (pip, github-actions, docker)
- ✅ Pipeline automatizado en cada push como capa adicional
- ⚠️ Pendiente: SIEM, auditoría de accesos

---

## Resumen de Cobertura

```
┌────────────────────────────────────────────────────────────────────────┐
│                  COBERTURA DEL CICLO DEVSECOPS                        │
├──────────────┬───────────┬────────┬────────────────────────────────────┤
│ Fase         │ Anterior  │ Actual │ Barra de progreso                 │
├──────────────┼───────────┼────────┼────────────────────────────────────┤
│ 1. Plan      │    20%    │  55%   │ █████▌░░░░  (+35%)                │
│ 2. Build     │    65%    │  90%   │ █████████░  (+25%)                │
│ 3. Test      │    25%    │  70%   │ ███████░░░  (+45%)                │
│ 4. Deploy    │    45%    │  45%   │ ████▌░░░░░  (sin cambios)         │
│ 5. Operate   │    20%    │  45%   │ ████▌░░░░░  (+25%)                │
│ 6. Monitor   │    15%    │  40%   │ ████░░░░░░  (+25%)                │
├──────────────┼───────────┼────────┼────────────────────────────────────┤
│ PROMEDIO     │    32%    │  58%   │ █████▊░░░░  (+26%)                │
└──────────────┴───────────┴────────┴────────────────────────────────────┘
```

### Mejora por implementación

| Implementación | Fases impactadas | Mejora |
|---|---|---|
| Dependabot | Monitor (+25%), Operate (+patching) | Monitoreo continuo de vulnerabilidades |
| Pre-commit hooks | Build (+pre-commit) | Detección temprana antes del commit |
| OWASP ZAP DAST | Build (+DAST), Test (+45%) | Testing dinámico de seguridad |
| Threat Model STRIDE | Plan (+35%) | Análisis formal de amenazas |
| Rate Limiting (slowapi) | Operate (+RASP) | Protección runtime contra fuerza bruta |
| Security Headers | Operate (+headers) | Protección HTTP a nivel de respuesta |

---

## Mapa de lo implementado vs lo faltante

```
    IMPLEMENTADO (✅)                          FALTANTE (❌)
    ═══════════════                            ═══════════════

    PRE-PRODUCCIÓN                             PRE-PRODUCCIÓN
    ──────────────                             ──────────────
    ✅ Threat Model STRIDE (documentado)       ❌ Code review obligatorio
    ✅ Pre-commit hooks (Gitleaks, Bandit,     ❌ Fuzzing de API
       Flake8, pre-commit-hooks)
    ✅ SCA (pip-audit, Safety)
    ✅ SAST (Bandit, Semgrep, Flake8)
    ✅ Secret Scanning (TruffleHog, Gitleaks)
    ✅ SQL Security (SQLFluff, grep)
    ✅ Container Security (Hadolint, Trivy)
    ✅ DAST (OWASP ZAP API + baseline scan)
    ✅ Testing validación (pytest, imports)
    ✅ Security config validation
    ✅ Security Headers verification

    PRODUCCIÓN                                 PRODUCCIÓN
    ──────────────                             ──────────────
    ✅ Security Gate (workflow_run)             ❌ SIEM
    ✅ Deploy gating                           ❌ WAF
    ✅ GitHub Secrets management               ❌ Chaos engineering
    ✅ Health checks post-deploy               ❌ Pen testing manual
    ✅ Rate limiting (slowapi)                 ❌ Log centralization
    ✅ Security Headers Middleware             ❌ Access auditing
    ✅ Dependabot (pip, actions, docker)
    ✅ JWT authentication + RBAC
    ⚠️ Logging básico (stdout)
```

---

## Fortalezas del Pipeline Actual

1. **Build es la fase más fuerte (90%)** — 14 herramientas de seguridad cubren SCA, SAST, secretos, SQL, contenedores, DAST y pre-commit
2. **Test mejoró significativamente (70%)** — OWASP ZAP provee testing dinámico real contra la app en producción
3. **Deploy gating funciona correctamente** — El despliegue se bloquea si la seguridad falla
4. **Pipeline automatizado de 7 pasos** — Desde secretos hasta DAST, todo se ejecuta en cada push
5. **Múltiples capas de defensa** — Cada tipo de vulnerabilidad se verifica con al menos 2 herramientas
6. **Artefactos de auditoría** — Se generan reportes JSON, HTML, SARIF y ZAP para trazabilidad
7. **Protección runtime** — Rate limiting y security headers protegen la app en producción
8. **Monitoreo continuo** — Dependabot verifica vulnerabilidades semanalmente de forma automática
9. **Threat Model documentado** — Análisis formal STRIDE cubre los 6 componentes del sistema

## Debilidades Remanentes

1. **No hay WAF** — La API está expuesta directamente sin firewall de aplicación web
2. **No hay SIEM** — Sin sistema centralizado de gestión de eventos de seguridad
3. **Code review no es obligatorio** — Falta branch protection con reviewers requeridos
4. **Logs no centralizados** — Los logs quedan en stdout de Render sin persistencia
5. **No hay auditoría de accesos** — No se registra quién accedió a qué endpoint

---

## Recomendaciones Pendientes (para futuras iteraciones)

### Prioridad ALTA (activación rápida)

| # | Acción | Fase | Esfuerzo | Herramienta sugerida |
|---|---|---|---|---|
| 1 | Activar branch protection | Build | 10 min | GitHub Settings → Branch protection rules |

### Prioridad MEDIA (mejora significativa)

| # | Acción | Fase | Esfuerzo | Herramienta sugerida |
|---|---|---|---|---|
| 2 | WAF con Cloudflare | Operate | 1-2 horas | Cloudflare free tier DNS proxy |
| 3 | Centralizar logs | Operate | 2 horas | Papertrail o Render Log Streams |

### Prioridad BAJA (ideal para producción real)

| # | Acción | Fase | Esfuerzo | Herramienta sugerida |
|---|---|---|---|---|
| 4 | SIEM básico | Monitor | 3-4 horas | Wazuh o ELK en Docker |
| 5 | Auditoría de accesos | Monitor | 2-3 horas | Middleware custom de logging |
| 6 | Fuzzing de API | Test | 2-3 horas | RESTler, Schemathesis |

---

*Análisis actualizado sobre el repositorio `Andres09xZ/epagal-backend-latacunga-route-service` — Branch: main*
*Análisis inicial: Febrero 2026 | Actualización: Febrero 2026 (post-implementación de recomendaciones)*
