# 🔄 CI/CD Pipeline con DevSecOps - EPAGAL

**Versión:** 1.0.0  
**Fecha:** 3 de febrero de 2026  
**Estado:** Documentado

---

## 📊 Diagrama General del Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CICLO DE VIDA CI/CD DEVSECOPS                    │
│                                                                       │
│  PLAN → CODE → BUILD → TEST → SECURITY → DEPLOY → MONITOR → PLAN   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Pipeline Completo: De Código a Producción

```
FASE 1: PLAN & CODE
═══════════════════════════════════════════════════════════════════════

Developer:
    ┌─────────────────────────────────────┐
    │  1. Crear Feature Branch             │
    │     git checkout -b feature/new-fix  │
    └──────────────────┬──────────────────┘
                       │
    ┌──────────────────▼──────────────────┐
    │  2. Escribir Código                  │
    │     - Nueva funcionalidad            │
    │     - Tests unitarios                │
    │     - Documentación                  │
    └──────────────────┬──────────────────┘
                       │
    ┌──────────────────▼──────────────────┐
    │  3. Validación Local (Pre-commit)    │
    │     - Black (formateo)               │
    │     - isort (imports)                │
    │     - Flake8 (linting)               │
    │     - Bandit (seguridad)             │
    │     - Gitleaks (secretos)            │
    │     - detect-secrets (credenciales)  │
    └──────────────────┬──────────────────┘
                       │
    ┌──────────────────▼──────────────────┐
    │  4. Git Commit & Push                │
    │     git commit -m "feature: desc"    │
    │     git push origin feature/...      │
    └──────────────────┬──────────────────┘
                       │


FASE 2: BUILD - GitHub Actions
═══════════════════════════════════════════════════════════════════════

                       │
    ┌──────────────────▼──────────────────┐
    │  1. Trigger: Pull Request Abierto    │
    │     - Push a rama de features        │
    │     - Automático en GitHub           │
    └──────────────────┬──────────────────┘
                       │
    ┌──────────────────▼──────────────────┐
    │  2. Setup: Ambiente de Construcción  │
    │     - Checkout código                │
    │     - Setup Python 3.13              │
    │     - Install dependencias           │
    │     - Setup PostgreSQL (opcional)    │
    └──────────────────┬──────────────────┘
                       │


FASE 3: SECURITY (DevSecOps) ⚡
═══════════════════════════════════════════════════════════════════════

                       │
                       ├─────────────────────────────────────┐
                       │                                     │
    ┌──────────────────▼───────────────┐                    │
    │  3.1 SAST (Static Analysis)       │                    │
    │  ─────────────────────────────    │                    │
    │  ├─ CodeQL                        │                    │
    │  │  └─ Análisis avanzado código   │                    │
    │  ├─ Bandit                        │                    │
    │  │  └─ Seguridad Python           │                    │
    │  └─ Semgrep                       │                    │
    │     └─ Patterns peligrosos        │                    │
    └──────────────────┬────────────────┘                    │
                       │                                     │
    ┌──────────────────▼───────────────┐                    │
    │  3.2 Secret Scanning              │                    │
    │  ─────────────────────────────    │                    │
    │  ├─ Gitleaks                      │                    │
    │  │  └─ Detecta credenciales       │                    │
    │  ├─ TruffleHog                    │                    │
    │  │  └─ Búsqueda avanzada secrets  │                    │
    │  └─ GitHub Secret Scanning        │                    │
    │     └─ Alertas nativas GitHub     │                    │
    └──────────────────┬────────────────┘                    │
                       │                                     │
    ┌──────────────────▼───────────────┐                    │
    │  3.3 SCA (Dependency Analysis)    │                    │
    │  ─────────────────────────────    │                    │
    │  ├─ Safety                        │                    │
    │  │  └─ Vulnerabilidades Python    │                    │
    │  ├─ pip-audit                     │                    │
    │  │  └─ Auditoría de paquetes      │                    │
    │  ├─ pip-licenses                  │                    │
    │  │  └─ Cumplimiento de licencias  │                    │
    │  └─ Dependabot                    │                    │
    │     └─ Alertas semanales          │                    │
    └──────────────────┬────────────────┘                    │
                       │                                     │
    ┌──────────────────▼───────────────┐                    │
    │  3.4 Code Quality                 │                    │
    │  ─────────────────────────────    │                    │
    │  ├─ Pylint                        │                    │
    │  │  └─ Análisis de código         │                    │
    │  ├─ Black                         │                    │
    │  │  └─ Formatting                 │                    │
    │  └─ Flake8                        │                    │
    │     └─ Linting                    │                    │
    └──────────────────┬────────────────┘                    │
                       │                                     │
                       └──────────────────────┬──────────────┘
                                              │
                       ┌──────────────────────▼──────────────┐
                       │  3.5 DECISION GATE: ¿TODO PASÓ?     │
                       │                                      │
                       │  ✅ TODOS LOS CHECKS PASARON         │
                       │    └─ Continuar a siguiente fase     │
                       │                                      │
                       │  ❌ ALGUNO FALLÓ                     │
                       │    └─ Bloquear merge a main          │
                       │    └─ Notificar developer            │
                       │    └─ Requiere fix antes de merge    │
                       └──────────────────┬───────────────────┘
                                          │


FASE 4: BUILD & TEST
═══════════════════════════════════════════════════════════════════════

                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  4.1 Build de Aplicación                               │
    │  ──────────────────────────────────────                │
    │  ├─ pip install -r requirements.txt                    │
    │  ├─ Compilar artefactos (si aplica)                    │
    │  └─ Generar documentación                              │
    └─────────────────────────────────────┬──────────────────┘
                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  4.2 Tests Unitarios                                   │
    │  ──────────────────────────────────────                │
    │  ├─ pytest tests/                                      │
    │  ├─ Coverage > 80%                                     │
    │  └─ Coverage report                                    │
    └─────────────────────────────────────┬──────────────────┘
                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  4.3 Integración Tests                                 │
    │  ──────────────────────────────────────                │
    │  ├─ API endpoints                                      │
    │  ├─ Database integration                               │
    │  └─ External services (OSRM, etc)                      │
    └─────────────────────────────────────┬──────────────────┘
                                          │


FASE 5: CONTAINER SECURITY
═══════════════════════════════════════════════════════════════════════

                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  5.1 Build Docker Image                                │
    │  ──────────────────────────────────────                │
    │  ├─ docker build -t app:latest .                       │
    │  ├─ Dockerfile análisis (Hadolint)                     │
    │  ├─ Multi-stage build                                  │
    │  └─ Minimal base image (python:3.13-slim)              │
    └─────────────────────────────────────┬──────────────────┘
                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  5.2 Container Security Scan (Trivy)                   │
    │  ──────────────────────────────────────                │
    │  ├─ Vulnerabilidades OS                                │
    │  ├─ Vulnerabilidades aplicación                        │
    │  ├─ Configuración segura                               │
    │  └─ CRITICAL/HIGH → Bloquea deploy                     │
    └─────────────────────────────────────┬──────────────────┘
                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  5.3 Hadolint (Dockerfile Best Practices)              │
    │  ──────────────────────────────────────                │
    │  ├─ Health checks                                      │
    │  ├─ User sin privilegios                               │
    │  ├─ Minimal layers                                     │
    │  └─ Seguridad en configuración                         │
    └─────────────────────────────────────┬──────────────────┘
                                          │


FASE 6: DEPLOY (Condicional)
═══════════════════════════════════════════════════════════════════════

                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  6.1 Push a Docker Hub                                 │
    │  ──────────────────────────────────────                │
    │  ├─ Tag: feature-sha (rama)                            │
    │  └─ SOLO si rama = main                                │
    └─────────────────────────────────────┬──────────────────┘
                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  6.2 Deploy a Staging (rama develop)                   │
    │  ──────────────────────────────────────                │
    │  ├─ Render deploy                                      │
    │  ├─ Health checks                                      │
    │  └─ Smoke tests                                        │
    └─────────────────────────────────────┬──────────────────┘
                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  6.3 Deploy a Producción (rama main)                   │
    │  ──────────────────────────────────────                │
    │  ├─ Tag: v1.x.x (semantic versioning)                  │
    │  ├─ Release notes                                      │
    │  ├─ Render production deploy                           │
    │  └─ Blue-green deployment                              │
    └─────────────────────────────────────┬──────────────────┘
                                          │


FASE 7: MONITOR & OBSERVE
═══════════════════════════════════════════════════════════════════════

                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  7.1 Health Checks                                     │
    │  ──────────────────────────────────────                │
    │  ├─ Endpoints disponibles                              │
    │  ├─ Base de datos conectada                            │
    │  ├─ OSRM respondiendo                                  │
    │  └─ Servicios externos OK                              │
    └─────────────────────────────────────┬──────────────────┘
                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  7.2 Logs & Monitoring                                 │
    │  ──────────────────────────────────────                │
    │  ├─ Logs de aplicación                                 │
    │  ├─ Errores y excepciones                              │
    │  ├─ Performance metrics                                │
    │  └─ Alertas (si hay problemas)                         │
    └─────────────────────────────────────┬──────────────────┘
                                          │
    ┌─────────────────────────────────────▼──────────────────┐
    │  7.3 Seguridad Continua                                │
    │  ──────────────────────────────────────                │
    │  ├─ Dependabot alerts (semanal)                        │
    │  ├─ Secret scanning                                    │
    │  ├─ Vulnerability scanning                             │
    │  └─ Compliance checks                                  │
    └─────────────────────────────────────┬──────────────────┘
                                          │
                       ┌──────────────────▼──────────────────┐
                       │  ✅ CICLO COMPLETO                  │
                       │                                      │
                       │  Volver a PLAN para siguiente fix    │
                       └──────────────────────────────────────┘
```

---

## 📍 Ramas y Ciclo de Vida

```
┌──────────────────────────────────────────────────────────────────┐
│                        GIT WORKFLOW                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  main (Producción)                                              │
│  │                                                              │
│  ├─ 1.0.0 (v1.0.0)          ← Release to Production            │
│  │  ├─ Fix: hotfix/critical  ← Emergency fixes                │
│  │  └─ Tag: v1.0.x          ← Hotfix releases                 │
│  │                                                              │
│  develop (Staging/Testing)                                      │
│  │                                                              │
│  ├─ Deploy automático        ← Cada push a develop            │
│  ├─ Feature branches:                                           │
│  │  ├─ feature/auth          ← Nueva funcionalidad            │
│  │  ├─ feature/incidencias   ← Nueva funcionalidad            │
│  │  └─ feature/otro          ← Nueva funcionalidad            │
│  │                                                              │
│  └─ Release branches:                                           │
│     └─ release/v1.0          ← Preparación para production     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo Detallado por Rama

### Feature Branch (feature/*)
```
1. Developer crea rama
   git checkout -b feature/mi-funcionalidad

2. Desarrolla y commitea
   git commit -m "feature: nueva funcionalidad"

3. Push a GitHub
   git push origin feature/mi-funcionalidad

4. Pull Request automático
   - Trigger: GitHub Actions
   - Ejecución: Todos los tests y seguridad
   - Resultado: ✅ o ❌

5. Code Review
   - Team revisa cambios
   - Aprueba o solicita cambios

6. Merge a develop
   - Automático si todo pasó
   - Deploy a staging
```

### Develop Branch
```
1. Cada push a develop
   - Trigger: GitHub Actions
   - Ejecución: Pipeline completo
   - Deploy automático: Staging

2. Testing en Staging
   - Smoke tests
   - Integration tests
   - Manual QA

3. Cuando está listo para producción
   - Crear release branch
   - Merge a main
   - Deploy a producción
```

### Main Branch (Producción)
```
1. Solo merge desde release branches
   - Requiere todas las pruebas pasadas
   - Requiere aprobación manual

2. Automáticamente:
   - Build Docker image
   - Push a Docker Hub
   - Deploy a Producción
   - Create release en GitHub

3. Monitoreo:
   - Health checks
   - Logs
   - Alertas
```

---

## 🎯 Gates y Decisiones

```
┌─────────────────────────────────────┐
│  GATE 1: Code Quality               │
├─────────────────────────────────────┤
│  ✅ Black formatting OK             │
│  ✅ isort imports OK                │
│  ✅ Flake8 linting OK               │
│  ✅ Pylint score > 7.0              │
│  ─────────────────────────────────  │
│  ❌ Si falla → Bloquear merge       │
│  📋 Resultado: Report en PR         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  GATE 2: Security (SAST)            │
├─────────────────────────────────────┤
│  ✅ CodeQL: 0 alerts CRITICAL       │
│  ✅ Bandit: 0 HIGH severity         │
│  ✅ Semgrep: 0 issues               │
│  ─────────────────────────────────  │
│  ❌ Si falla → Bloquear merge       │
│  📋 Resultado: SARIF report         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  GATE 3: Secrets                    │
├─────────────────────────────────────┤
│  ✅ Gitleaks: 0 secrets             │
│  ✅ TruffleHog: 0 credentials       │
│  ✅ GitHub Secret Scanning: OK      │
│  ─────────────────────────────────  │
│  ❌ Si falla → Bloquear merge       │
│  📋 Resultado: Alert notifications  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  GATE 4: Dependencies (SCA)         │
├─────────────────────────────────────┤
│  ✅ Safety: 0 vulnerabilities       │
│  ✅ pip-audit: 0 vulnerabilities    │
│  ✅ Licenses: All OK                │
│  ─────────────────────────────────  │
│  ❌ Si falla → Bloquear merge       │
│  📋 Resultado: Dependency report    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  GATE 5: Tests                      │
├─────────────────────────────────────┤
│  ✅ Unit tests: 100%                │
│  ✅ Integration tests: 100%         │
│  ✅ Coverage: > 80%                 │
│  ─────────────────────────────────  │
│  ❌ Si falla → Bloquear merge       │
│  📋 Resultado: Test report          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  GATE 6: Container Security         │
├─────────────────────────────────────┤
│  ✅ Trivy: 0 CRITICAL               │
│  ✅ Hadolint: 0 errors              │
│  ✅ Image size: < 500MB             │
│  ─────────────────────────────────  │
│  ❌ Si falla → Bloquear deploy      │
│  📋 Resultado: Security report      │
└─────────────────────────────────────┘

        ↓ TODAS PASAN ↓

┌─────────────────────────────────────┐
│  ✅ LISTO PARA MERGE                │
│  ✅ LISTO PARA DEPLOY A STAGING     │
│  ✅ LISTO PARA DEPLOY A PRODUCCIÓN  │
└─────────────────────────────────────┘
```

---

## 📊 Matriz de Responsabilidades

| Fase | Responsable | Herramienta | Duración | Acción Fallo |
|------|-------------|------------|----------|--------------|
| **CODE** | Developer | Local PC | 5-30 min | Fix local |
| **PRE-COMMIT** | Developer | git hooks | 30-60 seg | Retry |
| **SAST** | Workflow | CodeQL + Bandit + Semgrep | 3-5 min | Bloquear merge |
| **SECRETS** | Workflow | Gitleaks + TruffleHog | 1-2 min | Bloquear merge |
| **SCA** | Workflow | Safety + pip-audit | 1-2 min | Bloquear merge |
| **CODE QUALITY** | Workflow | Pylint + Black + Flake8 | 1-2 min | Bloquear merge |
| **TESTS** | Workflow | pytest | 3-5 min | Bloquear merge |
| **CONTAINER** | Workflow | Trivy + Hadolint | 2-3 min | Bloquear deploy |
| **DEPLOY** | Workflow | Render API | 5-10 min | Manual review |
| **MONITOR** | Production | Logs + Alerts | Continuo | Hotfix |

---

## 📈 Métricas del Pipeline

```
PERFORMANCE:
├─ Total Pipeline: 20-30 minutos (incluyendo deploy)
├─ Security checks: 8-12 minutos
├─ Tests: 5-10 minutos
├─ Container build: 3-5 minutos
└─ Deploy: 5-10 minutos

RELIABILITY:
├─ Success rate: > 95%
├─ Mean time to deploy (MTTR): < 30 min
├─ Mean time to recovery (MTTR): < 15 min
└─ Uptime: > 99.5%

SECURITY:
├─ Vulnerabilities detected: 100%
├─ Secrets caught: 100%
├─ False positives: < 5%
└─ Time to remediate: < 24 horas

QUALITY:
├─ Code coverage: > 80%
├─ Test pass rate: 100%
├─ Build success rate: 95%+
└─ Deployment success rate: 98%+
```

---

## 🔐 DevSecOps Lifecycle

```
                    PLAN
                     │
        ┌────────────┼────────────┐
        │            │            │
       CODE        BUILD       SECURITY
        │            │            │
        └────────────┼────────────┘
                     │
                  DEPLOY
                     │
        ┌────────────┼────────────┐
        │            │            │
     MONITOR    MAINTAIN      IMPROVE
        │            │            │
        └────────────┼────────────┘
                     │
                   PLAN (Ciclo)
```

**Cada fase con seguridad integrada (Shift-Left):**

1. **PLAN:** Análisis de riesgos de seguridad
2. **CODE:** Pre-commit hooks en local
3. **BUILD:** SAST en CI/CD
4. **SECURITY:** Secretos, SCA, container scanning
5. **DEPLOY:** Validaciones finales
6. **MONITOR:** Detección de anomalías
7. **MAINTAIN:** Parcheo de vulnerabilidades
8. **IMPROVE:** Análisis post-mortem

---

## 🎯 Beneficios de Este Pipeline

```
✅ Automatización Completa
   └─ 0% manual, 100% automatizado

✅ Shift-Left Security
   └─ Detecta issues lo antes posible

✅ Fast Feedback
   └─ Resultados en < 30 minutos

✅ Quality Gate
   └─ Solo código seguro a producción

✅ Compliance
   └─ OWASP, CWE, PCI-DSS compliant

✅ Visibility
   └─ Reportes en cada paso

✅ Scalability
   └─ Soporta múltiples equipos

✅ Cost Optimization
   └─ Detecta issues temprano = costo ↓
```

---

## 📞 Próximos Pasos

- [ ] Implementar security.yml workflow
- [ ] Configurar pre-commit hooks localmente
- [ ] Entrenar al team en pipeline
- [ ] Monitorear primeros deployments
- [ ] Ajustar según resultados

---

**Versión:** 1.0.0  
**Fecha:** 3 de febrero de 2026  
**Autor:** EPAGAL Development Team
