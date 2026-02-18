# Pipeline DevSecOps - EPAGAL Backend Latacunga

## Diagrama del Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              TRIGGER: Push a main/develop o PR a main                   │
└─────────────────────────┬───────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW 1: DevSecOps Pipeline                                  │
│                         (devsecops.yml)                                                 │
│                                                                                         │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  PASO 1           │  │  PASO 2           │  │  PASO 3           │                    │
│  │  Secret Scanning  │  │  Dependency Check │  │  SAST             │                    │
│  │                   │  │  (SCA)            │  │                   │                    │
│  │  • TruffleHog     │  │  • pip-audit      │  │  • Bandit         │                    │
│  │  • Gitleaks       │  │  • Safety         │  │  • Semgrep        │                    │
│  │  • Grep manual    │  │  • pip-licenses   │  │  • Flake8         │                    │
│  │                   │  │  • pip outdated   │  │  • SQL Injection  │                    │
│  │  Analiza:         │  │                   │  │  • XSS patterns   │                    │
│  │  Passwords,       │  │  Analiza:         │  │  • Config inseg.  │                    │
│  │  API keys,        │  │  CVEs conocidos,  │  │                   │                    │
│  │  tokens, URIs     │  │  licencias,       │  │  Analiza:         │                    │
│  │  de conexión      │  │  versiones        │  │  Código fuente    │                    │
│  │                   │  │  desactualizadas  │  │  estáticamente    │                    │
│  └────────┬──────────┘  └────────┬──────────┘  └────────┬──────────┘                    │
│           │                      │                      │                               │
│           │    ┌─────────────────┼──────────────────────┘                                │
│           │    │                 │                                                       │
│           ▼    ▼                 ▼                                                       │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  PASO 4           │  │  PASO 5           │  │  PASO 6           │                    │
│  │  SQL Security     │  │  Testing &        │  │  Container        │                    │
│  │                   │  │  Validation       │  │  Security         │                    │
│  │  • SQLFluff       │  │  • pytest         │  │  • Hadolint       │                    │
│  │  • Grep avanzado  │  │  • Python import  │  │  • Trivy (imagen) │                    │
│  │                   │  │    validation     │  │  • Trivy (fs)     │                    │
│  │  Analiza:         │  │  • FastAPI init   │  │  • Best practices │                    │
│  │  SQL migrations,  │  │  • Security config│  │                   │                    │
│  │  text(f"..."),    │  │    validation     │  │  Analiza:         │                    │
│  │  execute(f"..."), │  │                   │  │  Dockerfile,      │                    │
│  │  DROP sin IF,     │  │  Analiza:         │  │  imagen Docker,   │                    │
│  │  GRANT ALL,       │  │  Integridad de    │  │  CVEs en paquetes │                    │
│  │  credenciales     │  │  la app, config   │  │  del SO, secrets  │                    │
│  │  en .sql          │  │  de seguridad     │  │  en filesystem    │                    │
│  └────────┬──────────┘  └────────┬──────────┘  └────────┬──────────┘                    │
│           │                      │                      │                               │
│           └──────────────────────┼──────────────────────┘                                │
│                                  ▼                                                      │
│                    ┌──────────────────────────┐                                          │
│                    │  RESUMEN DE SEGURIDAD    │                                          │
│                    │  (Security Summary)      │                                          │
│                    │                          │                                          │
│                    │  Evalúa los 6 pasos:     │                                          │
│                    │  ✓ Passed / ✗ Failed     │                                          │
│                    │                          │                                          │
│                    │  Si alguno FALLA:        │                                          │
│                    │  → exit 1 (bloquea)      │                                          │
│                    └────────────┬─────────────┘                                          │
│                                 │                                                       │
└─────────────────────────────────┼───────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    │                            │
                    ▼                            ▼
          ┌─────────────────┐          ┌─────────────────┐
          │  ✓ SUCCESS      │          │  ✗ FAILURE      │
          │                 │          │                 │
          │  Dispara        │          │  Deploy         │
          │  workflow_run   │          │  BLOQUEADO      │
          └────────┬────────┘          │                 │
                   │                   │  No se ejecuta  │
                   ▼                   │  deploy.yml     │
┌──────────────────────────────────┐   └─────────────────┘
│  WORKFLOW 2: Build and Deploy    │
│  (deploy.yml)                    │
│                                  │
│  ┌────────────────────────────┐  │
│  │  SECURITY GATE             │  │
│  │  Verifica:                 │  │
│  │  workflow_run.conclusion   │  │
│  │  == 'success'              │  │
│  └─────────────┬──────────────┘  │
│                │                 │
│                ▼                 │
│  ┌────────────────────────────┐  │
│  │  BUILD & PUSH              │  │
│  │  • Docker Buildx           │  │
│  │  • Login Docker Hub        │  │
│  │  • Build + Push imagen     │  │
│  │                            │  │
│  │  Imagen:                   │  │
│  │  mrengineer09/             │  │
│  │  epagal-backend-routing    │  │
│  └─────────────┬──────────────┘  │
│                │                 │
│                ▼                 │
│  ┌────────────────────────────┐  │
│  │  DEPLOY TO RENDER          │  │
│  │  • Validar secrets         │  │
│  │  • Deploy via API          │  │
│  │  • Logs + health checks    │  │
│  │  • Test endpoints          │  │
│  └─────────────┬──────────────┘  │
│                │                 │
│                ▼                 │
│  ┌────────────────────────────┐  │
│  │  NOTIFY                    │  │
│  │  Resumen del despliegue    │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

---

## Detalle de cada Etapa de Seguridad

---

### PASO 1: Secret Scanning (Escaneo de Secretos)

**Objetivo:** Detectar credenciales, tokens, claves API y otros secretos que hayan sido expuestos en el código fuente o en el historial de Git.

| Herramienta | Versión/Acción | Qué analiza |
|---|---|---|
| **TruffleHog** | `trufflesecurity/trufflehog@main` | Escanea todo el historial de commits de Git buscando secretos verificados (passwords, API keys, tokens) usando detección de alta entropía y patrones conocidos. Solo reporta secretos que pueda verificar como válidos (`--only-verified`). |
| **Gitleaks** | `gitleaks/gitleaks-action@v2` | Escanea el código fuente actual y los commits usando reglas configurables (`.gitleaks.toml`). Detecta: URIs de PostgreSQL con credenciales, API keys, JWT secrets, tokens de Docker/Render. Soporta allowlists por path y por commit. |
| **Búsqueda manual (grep)** | Script bash personalizado | Complementa las herramientas anteriores buscando patrones específicos del proyecto: `password=`, `api_key=`, `token=`, `postgresql://`, `mysql://`, `mongodb://` en archivos Python de `app/`. También verifica que `.env` esté en `.gitignore`. |

**Configuración especial:**
- `.gitleaks.toml` define reglas personalizadas y allowlists para archivos de documentación, migraciones SQL, tests y workflows de CI.
- Commits históricos con secretos ya remediados están en la allowlist para evitar falsos positivos.

**¿Qué bloquea?** Si TruffleHog o Gitleaks detectan un secreto activo → el paso falla → el pipeline se bloquea.

---

### PASO 2: Dependency Check — SCA (Software Composition Analysis)

**Objetivo:** Verificar que las dependencias de terceros (paquetes pip) no tengan vulnerabilidades conocidas (CVEs), estén actualizadas y tengan licencias compatibles.

| Herramienta | Versión | Qué analiza |
|---|---|---|
| **pip-audit** | Última versión estable | Audita `requirements.txt` contra la base de datos de vulnerabilidades de PyPI (OSV/Advisory Database). Genera reportes en formato columnas y JSON. Identifica CVEs con severidad, versiones afectadas y versiones parcheadas. |
| **Safety** | Última versión estable | Segundo motor de verificación de CVEs. Usa la base de datos Safety DB (independiente de pip-audit) para cruzar vulnerabilidades. Genera un reporte completo (`--full-report`) con descripción detallada de cada CVE. |
| **pip list --outdated** | Incluido en pip | Lista todas las dependencias que tienen versiones más recientes disponibles. Permite identificar paquetes desactualizados que podrían tener parches de seguridad pendientes. |
| **pip-licenses** | Última versión estable | Analiza las licencias de todas las dependencias instaladas. Muestra la licencia de cada paquete en formato tabla con URLs, útil para verificar compatibilidad legal (MIT, Apache, GPL, etc.). |

**Artefactos generados:**
- `pip-audit-report.json` — Reporte de auditoría en JSON (se sube como artifact, retención 30 días).

**¿Qué bloquea?** Este paso no bloquea directamente (usa `|| true`), pero si el job falla por otro motivo, se reporta como advertencia en el resumen.

---

### PASO 3: SAST (Static Application Security Testing)

**Objetivo:** Analizar el código fuente de la aplicación sin ejecutarlo para detectar vulnerabilidades de seguridad, patrones peligrosos y errores de calidad.

| Herramienta | Versión | Qué analiza |
|---|---|---|
| **Bandit** | Última estable | Analizador de seguridad específico para Python. Escanea `app/` buscando: uso de `eval()`, `exec()`, `subprocess` inseguro, binding a `0.0.0.0`, SQL injection, hashes débiles (MD5, SHA1), permisos de archivos inseguros, uso de `assert` en producción. Genera reportes en pantalla, JSON y HTML. Filtra por severidad ALTA y CRÍTICA. |
| **Semgrep** | Última estable (via pip) | Motor SAST avanzado con reglas de la comunidad. Ejecuta 6 packs de reglas simultáneamente: `p/python` (reglas generales Python), `p/flask` (seguridad de frameworks web), `p/sql-injection` (inyección SQL), `p/xss` (Cross-Site Scripting), `p/secrets` (secretos en código), `p/owasp-top-ten` (OWASP Top 10 2021). Dos pasadas: una que bloquea en ERROR y otra informativa con todos los niveles. |
| **Flake8** | Última estable | Linter de calidad de código Python. Configurado para detectar solo errores críticos: `E9` (errores de sintaxis), `F63` (comparaciones inválidas), `F7` (errores de flujo), `F82` (variables no definidas), `W6` (deprecaciones). Max line length: 120 caracteres. |
| **Análisis de SQL Injection (grep)** | Script bash personalizado | Busca 4 patrones peligrosos de SQL Injection en `app/`: f-strings con SQL (`f"SELECT..."`), `.format()` con SQL, concatenación de strings con SQL (`"SELECT..." + var`), y `%s` formatting en consultas SQL. |
| **Análisis de XSS (grep)** | Script bash personalizado | Busca patrones de Cross-Site Scripting: `render_template_string()` (Jinja2 inseguro), `Markup()` sin `escape()`, `innerHTML/outerHTML/document.write` en archivos HTML/JS del dashboard. |
| **Config inseguras (grep)** | Script bash personalizado | Verifica: `debug=True` hardcodeado, `SECRET_KEY` hardcodeada, CORS con wildcard `*`, URLs HTTP en lugar de HTTPS (excluyendo localhost y OSRM que son servicios locales legítimos). |

**Artefactos generados:**
- `bandit-report.json` — Reporte detallado en JSON
- `bandit-report.html` — Reporte visual en HTML

**¿Qué bloquea?** Semgrep bloquea si detecta findings de severidad ERROR. Los análisis manuales son informativos.

---

### PASO 4: SQL Security (Seguridad SQL)

**Objetivo:** Verificar la seguridad de las consultas SQL tanto en el código Python como en los archivos de migración SQL.

| Herramienta | Versión | Qué analiza |
|---|---|---|
| **SQLFluff** | Última estable | Linter de SQL configurado para dialecto PostgreSQL. Ejecuta reglas específicas sobre los archivos en `migrations/` y `database/`: `LT01` (espaciado), `LT02` (indentación), `LT04` (coma trailing), `LT09` (subconsultas), `AM01/AM02` (ambigüedad de columnas), `CV01/CV02` (convenciones), `ST06` (orden SELECT). Verifica calidad y consistencia del SQL. |
| **Análisis avanzado SQL Injection (grep)** | Script bash personalizado | Busca 5 patrones críticos de inyección SQL específicos de SQLAlchemy/Python: (1) `text(f"...")` — inyección directa con f-strings, (2) `text(...).format()` — inyección con .format(), (3) `text(...+ variable)` — concatenación peligrosa, (4) `.execute(f"...")` — ejecución directa con f-strings, (5) `execute(... % ...)` — operador % en SQL. También cuenta las consultas parametrizadas seguras (`bindparam`, `params=`, `:variable`). |
| **Seguridad en archivos SQL (grep)** | Script bash personalizado | Verifica archivos en `migrations/` y `database/`: (1) `DROP TABLE/DATABASE` sin `IF EXISTS` (puede causar errores en producción), (2) `GRANT ALL` o `SUPERUSER` (privilegios excesivos), (3) Credenciales hardcodeadas en archivos `.sql` (excluyendo placeholders como `$BCRYPT_HASH`). |

**¿Qué bloquea?** Si se detectan patrones de SQL Injection en el código Python → `exit 1` → **bloquea el pipeline**. Las advertencias en archivos SQL son informativas.

---

### PASO 5: Testing & Validation (Pruebas y Validación de Seguridad)

**Objetivo:** Verificar la integridad estructural de la aplicación, que los módulos se importan correctamente, que FastAPI se inicializa sin errores, y que la configuración de seguridad es correcta.

| Verificación | Herramienta | Qué analiza |
|---|---|---|
| **Importación de módulos** | Python `__import__()` | Verifica que los 5 módulos principales se pueden importar sin errores: `app`, `app.main`, `app.database`, `app.models`, `app.schemas`. Usa variables de entorno ficticias (`DB_URL`, `JWT_SECRET`) para que la importación funcione en CI sin base de datos real. Detecta: imports rotos, dependencias faltantes, errores de sintaxis. |
| **Inicialización FastAPI** | Python script | Importa `app.main.app` y verifica: título de la aplicación, versión, número de rutas registradas. Lista todos los endpoints con sus métodos HTTP. Confirma que la aplicación puede arrancar sin errores de configuración. |
| **Descubrimiento de tests** | `pytest --collect-only` | Ejecuta pytest en modo de descubrimiento sobre `tests/` y `features/` sin ejecutar tests. Verifica que los archivos de test tienen sintaxis válida y que pytest los reconoce. |
| **Tests unitarios** | `pytest` | Ejecuta tests que no requieren servicios externos (DB, OSRM). Usa `--timeout=15` para evitar tests colgados, `-k "not integration and not slow"` para filtrar, `--ignore=test_osrm_connection.py` para omitir tests de conexión externa. |
| **Archivos críticos de seguridad** | Python script | Verifica que existen los 3 archivos críticos (`auth_service.py`, `database.py`, `main.py`) y que no contienen credenciales hardcodeadas. Busca patrones de `password=` sin `environ`/`getenv` en cada línea. |
| **Configuración de seguridad** | Python script | 4 verificaciones: (1) `.gitignore` contiene `.env`, `__pycache__`, `*.pyc`/`*.py[cod]`, (2) `auth_service.py` usa `environ`/`getenv` para SECRET_KEY, (3) `.env` no está en el repositorio, (4) `Dockerfile` no tiene `ENV SECRET` ni `ENV PASSWORD`. |

**Variables de entorno en CI:**
```yaml
env:
  DB_URL: "postgresql://ci_user:ci_pass@localhost:5432/ci_test_db"
  JWT_SECRET: "ci-testing-secret-key-not-real"
  SECRET_KEY: "ci-testing-secret-key-not-real"
```
> Estas son credenciales ficticias que permiten que los imports funcionen sin una base de datos real.

**¿Qué bloquea?** Si los imports fallan, si FastAPI no se inicializa, si archivos críticos están ausentes, o si la configuración de seguridad tiene fallas → `exit 1` → **bloquea el pipeline**.

---

### PASO 6: Container Security (Seguridad de Contenedores)

**Objetivo:** Analizar la seguridad del Dockerfile, la imagen Docker construida y las mejores prácticas de contenedorización.

| Herramienta | Versión/Acción | Qué analiza |
|---|---|---|
| **Hadolint** | `hadolint/hadolint-action@v3.1.0` | Linter de Dockerfile basado en mejores prácticas de Docker. Analiza instrucciones del Dockerfile buscando: uso de `latest` sin fijar versión, `apt-get` sin `--no-install-recommends`, falta de limpieza de caché, `COPY` inseguro, `ADD` vs `COPY`, falta de `USER` no-root. Ignora reglas: `DL3008` (pin de versiones apt), `DL3013` (pin de versiones pip), `DL3042` (pip cache). Umbral: solo falla en `error`. |
| **Trivy (imagen)** | `aquasecurity/trivy-action@0.28.0` | Escáner de vulnerabilidades de contenedores. Construye la imagen Docker (`epagal-backend:security-scan`) y escanea todas las capas buscando CVEs en: paquetes del SO (Debian/Ubuntu), bibliotecas del sistema (libpq, libgeos, etc.), paquetes Python instalados. Filtra por severidad `CRITICAL` y `HIGH`. Genera reporte en tabla y SARIF. |
| **Trivy (filesystem)** | `aquasecurity/trivy-action@0.28.0` | Escanea el código fuente y archivos de configuración del repositorio (sin construir imagen). Busca: secretos en archivos, configuraciones inseguras, vulnerabilidades en dependencias a nivel de filesystem. |
| **Best Practices (grep)** | Script bash personalizado | 6 verificaciones de mejores prácticas del Dockerfile: (1) Usa imagen base reducida (`slim`/`alpine`), (2) Define usuario no-root (`USER`), (3) Define `HEALTHCHECK`, (4) No copia `.env` al contenedor, (5) Existe `.dockerignore`, (6) pip usa `--no-cache-dir`. Si copia `.env` → fallo crítico. Las demás son advertencias. |

**Artefactos generados:**
- `trivy-results.sarif` — Reporte SARIF de Trivy (compatible con GitHub Security tab, retención 30 días).

**¿Qué bloquea?** Si Hadolint detecta errores críticos o si se copia `.env` al contenedor → fallo. Trivy usa `exit-code: 0` (no bloquea, solo informa). Las advertencias de best practices no bloquean.

---

### Security Summary (Resumen de Seguridad)

**Objetivo:** Consolidar los resultados de los 6 pasos y decidir si el despliegue se permite o se bloquea.

| Evaluación | Resultado | Acción |
|---|---|---|
| Todos los pasos `success` | ✓ APROBADO | Se dispara `deploy.yml` |
| Dependency Check `failure` (únicamente) | ⚠ APROBADO CON ADVERTENCIAS | Se dispara `deploy.yml` |
| Cualquier otro paso `failure` | ✗ FALLIDO | `exit 1` → Deploy BLOQUEADO |

---

### Security Gate (Puerta de Seguridad — deploy.yml)

**Objetivo:** Última verificación antes de construir y desplegar. Garantiza que el pipeline DevSecOps se completó exitosamente.

| Condición | Resultado |
|---|---|
| `workflow_run.conclusion == 'success'` AND `head_branch == 'main'` | ✓ Procede a Build & Push Docker Hub → Deploy Render |
| `workflow_run.conclusion != 'success'` | ✗ El workflow `deploy.yml` ni siquiera se ejecuta |
| `workflow_dispatch` (manual) | ⚠ Se omite verificación (despliegue de emergencia) |

---

## Resumen de Herramientas

| # | Herramienta | Tipo | Categoría OWASP | Lenguaje/Target |
|---|---|---|---|---|
| 1 | **TruffleHog** | Secret Scanner | A07:2021 | Git history |
| 2 | **Gitleaks** | Secret Scanner | A07:2021 | Código fuente + Git |
| 3 | **pip-audit** | SCA | A06:2021 | Python dependencies |
| 4 | **Safety** | SCA | A06:2021 | Python dependencies |
| 5 | **pip-licenses** | License Checker | Compliance | Python dependencies |
| 6 | **Bandit** | SAST | A03:2021 | Python source code |
| 7 | **Semgrep** | SAST | A03:2021, A01-A10 | Python source code |
| 8 | **Flake8** | Linter/SAST | Code Quality | Python source code |
| 9 | **SQLFluff** | SQL Linter | A03:2021 | SQL files |
| 10 | **pytest** | Testing Framework | Validation | Python tests |
| 11 | **Hadolint** | Container Linter | A05:2021 | Dockerfile |
| 12 | **Trivy** | Container Scanner | A06:2021 | Docker image + filesystem |

---

## Mapeo OWASP Top 10 (2021)

| Riesgo OWASP | Pasos que lo cubren | Herramientas |
|---|---|---|
| **A01 - Broken Access Control** | Paso 3, Paso 5 | Semgrep (p/owasp-top-ten), config validation |
| **A02 - Cryptographic Failures** | Paso 1, Paso 3 | TruffleHog, Gitleaks, Bandit (hashes débiles) |
| **A03 - Injection (SQLi/XSS)** | Paso 3, Paso 4 | Semgrep, Bandit, SQLFluff, grep patterns |
| **A04 - Insecure Design** | Paso 5, Paso 6 | Testing validation, Dockerfile best practices |
| **A05 - Security Misconfiguration** | Paso 3, Paso 5, Paso 6 | Config analysis, Hadolint, security config check |
| **A06 - Vulnerable Components** | Paso 2, Paso 6 | pip-audit, Safety, Trivy |
| **A07 - Auth Failures** | Paso 1, Paso 5 | Secret scanning, auth_service validation |
| **A08 - Software Integrity** | Paso 2, Paso 5 | pip-audit, Safety, import validation |
| **A09 - Logging Failures** | Paso 3 | Bandit, Flake8 |
| **A10 - SSRF** | Paso 3 | Semgrep (p/owasp-top-ten) |

---

## Flujo Completo

```
Desarrollador hace push a main
         │
         ▼
   DevSecOps Pipeline
         │
         ├── Paso 1: ¿Hay secretos expuestos?          → Sí → ✗ BLOQUEA
         ├── Paso 2: ¿Dependencias vulnerables?         → Info (advertencia)
         ├── Paso 3: ¿Vulnerabilidades en código?       → Sí → ✗ BLOQUEA
         ├── Paso 4: ¿SQL Injection en código/SQL?      → Sí → ✗ BLOQUEA
         ├── Paso 5: ¿App se inicializa correctamente?  → No → ✗ BLOQUEA
         ├── Paso 6: ¿Dockerfile/imagen seguros?        → Crítico → ✗ BLOQUEA
         │
         ▼
   Security Summary
         │
         ├── Algún paso falló → ✗ Deploy BLOQUEADO
         │
         └── Todos pasaron → ✓ Trigger deploy.yml
                                    │
                                    ├── Security Gate (verifica conclusión)
                                    ├── Build & Push a Docker Hub
                                    ├── Deploy a Render
                                    └── Health checks + notificación
```

---

## Archivos de Configuración del Pipeline

| Archivo | Propósito |
|---|---|
| `.github/workflows/devsecops.yml` | Pipeline principal de seguridad (6 pasos + resumen) |
| `.github/workflows/deploy.yml` | Pipeline de despliegue (gated por DevSecOps) |
| `.gitleaks.toml` | Configuración de Gitleaks (allowlists, reglas personalizadas) |
| `.bandit` | Configuración de Bandit (exclusiones, skips) |
| `.dockerignore` | Archivos excluidos de la imagen Docker |
| `.gitignore` | Archivos excluidos del repositorio |
| `.env.example` | Plantilla de variables de entorno (sin credenciales reales) |

---

*Documento generado para el proyecto de tesis - EPAGAL Backend Latacunga Route Service*
*Pipeline implementado con GitHub Actions sobre el repositorio: `Andres09xZ/epagal-backend-latacunga-route-service`*
