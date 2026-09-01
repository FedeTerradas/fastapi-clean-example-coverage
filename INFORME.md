# Informe Práctico: Cobertura de Pruebas, Análisis Estático con Codacy e Integración Continua (CI/CD)

---

## 1. Descripción General del Repositorio (`fastapi-clean-example`)

El proyecto base utilizado es [fastapi-clean-example](https://github.com/ivan-borovets/fastapi-clean-example), una API REST de ejemplo desarrollada en **Python 3.13** y **FastAPI**, diseñada siguiendo principios de **Clean Architecture**, **Domain-Driven Design (DDD)** y **CQRS**.

```
                           ┌──────────────────────────────┐
                           │      Inbound Layer (HTTP)    │
                           │     (FastAPI Routers, DTOs)  │
                           └──────────────┬───────────────┘
                                          │
                                          ▼
                           ┌──────────────────────────────┐
                           │       Core (Application)     │
                           │   Commands, Queries, Services│
                           └──────────────┬───────────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
     ┌───────────────────────────┐                 ┌───────────────────────────┐
     │   Domain / Value Objects  │                 │    Outbound Adapters      │
     │  UtcDatetime, RawPassword │                 │  PostgreSQL, SQLAlchemy,  │
     │      User Entities        │                 │    Bcrypt, JWT Processor  │
     └───────────────────────────┘                 └───────────────────────────┘
```

### ¿Qué hace la aplicación?
Es un sistema completo de gestión de usuarios y autenticación con control de acceso:
- **Gestión de Cuentas:** Registro (`sign_up`), inicio de sesión (`log_in`), cierre de sesión (`log_out`) y cambio de contraseña (`change_password`).
- **Administración de Usuarios:** Creación, activación, desactivación, listado paginado y asignación/revocación de permisos de administrador (RBAC).
- **Seguridad:** Hashing seguro de contraseñas con **Bcrypt + Salt + Pepper HMAC-SHA384** y soporte de contraseñas sin límite de 72 bytes mediante pre-hashing. Manejo de sesiones y tokens JWT.

### Patrones de Arquitectura Implementados:
1. **Clean Architecture / Inversión de Dependencias (DIP):** El núcleo de negocio (`core`) no conoce detalles de infraestructura (bases de datos ni frameworks web). Usa el contenedor de inyección de dependencias `dishka`.
2. **Tactical DDD:** Lógica de negocio encapsulada en *Value Objects* inmutables (`UtcDatetime`, `RawPassword`, `Username`) y *Entities* (`User`).
3. **CQRS (Command Query Responsibility Segregation):** Separación estricta entre operaciones de escritura (*Commands*) y operaciones de lectura (*Queries*).
4. **Unit of Work (UoW):** Control transaccional desacoplado (`sqla_transaction_manager`, `sqla_flusher`).

---

## 2. Desarrollo de la Tarea Paso a Paso

### Paso 1: Clonar y Configurar el Entorno Local
- Se instaló **`uv`** (el gestor de paquetes de alto rendimiento para Python).
- Se clonó el repositorio y se ejecutó `uv sync` para resolver e instalar 92 dependencias fijadas.

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
git clone https://github.com/ivan-borovets/fastapi-clean-example.git
cd fastapi-clean-example
uv sync
```

---

### Paso 2: Ejecutar Pruebas Existentes con Cobertura
Se ejecutó el conjunto de pruebas unitarias configurado en `pyproject.toml` usando `pytest` y `pytest-cov`:

```bash
uv run pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml
```

* **Resultado inicial:** 117 tests aprobados. Cobertura global de código: **25%**.
* *(Nota: El 25% inicial corresponde a que los tests unitarios no abarcan los módulos de persistencia PostgreSQL ni endpoints HTTP, los cuales están en `tests/integration` y requieren Docker).*

---

### Paso 3: Generación e Inspección del Informe de Cobertura
Se generaron dos formatos de informe:
- **`coverage.xml`**: Formato estándar para herramientas de CI/CD y análisis estático.
- **`htmlcov/index.html`**: Informe visual interactivo que detalla línea por línea:
  - 🟩 **Verde**: Líneas cubiertas por tests.
  - 🟥 **Rojo**: Líneas nunca ejecutadas (gaps de cobertura).
  - 🟨 **Amarillo**: Ramas condicionales (`if/else`) cubiertas parcialmente.

#### Gaps detectados en módulos unitarios:
1. **`src/app/core/common/value_objects/utc_datetime.py`** (77% de cobertura):
   - Líneas 27-30 (`__lt__` y el guard `NotImplemented` para tipos incompatibles sin probar).
2. **`src/app/outbound/adapters/bcrypt_password_hasher.py`** (25% de cobertura):
   - Líneas 61-71 (el bloque de timeout del semáforo y lanzamiento de `PasswordHasherBusyError` sin probar).

---

### Paso 4: Análisis Estático y Sugerencias de Mejora con Codacy
Se conectó el repositorio público con **Codacy**, el cual analizó el código utilizando linters automatizados (**Bandit**, **Semgrep**, **Trivy**). 

Codacy reportó los siguientes hallazgos y sugerencias:

| Herramienta / Regla | Archivo / Componente | Diagnóstico y Sugerencia de Mejora |
|---|---|---|
| **Bandit `B101`** | Archivos de tests (`tests/*`) | Detecta uso de `assert`. *Diagnóstico:* En producción `assert` se desactiva con `-O`, pero en tests con `pytest` es el estándar. *Mejora:* Excluir `tests/` de la regla B101 en la configuración de Bandit. |
| **Bandit `B105`** | `tests/unit/main/config/test_loader.py` | Detecta strings que simulan contraseñas (`"test-password"`). *Mejora:* Utilizar generadores dinámicos o variables mock para evitar falsos positivos de secretos expuestos. |
| **Semgrep YAML** | `.github/workflows/*.yml` | Acciones de GitHub referenciadas por tag (ej. `@v4`) en vez de commit SHA. *Mejora:* Fijar acciones con el commit SHA inmutable para prevenir ataques de cadena de suministro. |
| **Trivy Vulnerabilities** | `uv.lock` (`starlette`, `cryptography`, `pyjwt`) | Dependencias transitivas con CVEs reportados. *Mejora:* Ejecutar `uv lock --upgrade` para actualizar a versiones seguras. |
| **Semgrep Python** | `tests/integration/.../conftest.py` | Uso de `sqlalchemy.text`. *Mejora:* Usar parámetros vinculados (`bindparams`) para mitigar riesgos potenciales de inyección SQL. |

---

### Paso 5: Implementación de Nuevas Pruebas con Cobertura Mejorada
Para subsanar los gaps identificados en el Paso 3, se agregaron **2 nuevos archivos de pruebas (6 tests en total)**:

#### 1. [`tests/unit/core/common/value_objects/test_utc_datetime_ordering.py`](file:///C:/Users/feder/.gemini/antigravity/scratch/fastapi-clean-example/tests/unit/core/common/value_objects/test_utc_datetime_ordering.py)
- `test_earlier_utcdatetime_is_less_than_later`: Valida la comparación `<` correcta entre instancias.
- `test_later_utcdatetime_is_not_less_than_earlier`: Valida el resultado `False` en orden inverso.
- `test_equal_utcdatetimes_are_not_less_than_each_other`: Valida igualdad en el operador `<`.
- `test_lt_returns_not_implemented_for_incompatible_type`: Valida que comparar con un tipo no compatible retorne `NotImplemented` y lance `TypeError`.
- **Impacto:** `utc_datetime.py` pasó de **77% a 100%** de cobertura.

#### 2. [`tests/unit/outbound/test_bcrypt_password_hasher_busy.py`](file:///C:/Users/feder/.gemini/antigravity/scratch/fastapi-clean-example/tests/unit/outbound/test_bcrypt_password_hasher_busy.py)
- `test_raises_password_hasher_busy_error_when_semaphore_is_exhausted`: Simula la saturación de workers bloqueando el semáforo y comprueba que se lance `PasswordHasherBusyError`.
- `test_semaphore_is_released_after_successful_hash`: Comprueba que el bloque `finally` libere el semáforo tras ejecutar el hash.
- **Impacto:** `bcrypt_password_hasher.py` pasó de **25% a 100%** de cobertura.

#### 📈 Resultado Global:
- **Total de pruebas:** Pasó de **117 a 123 tests** (100% pasando).
- **Cobertura total unitaria:** Se incrementó del **25% al 27%**.

---

### Paso 6: Integración Continua con GitHub Actions
Se creó el workflow [`.github/workflows/tests-coverage.yml`](file:///C:/Users/feder/.gemini/antigravity/scratch/fastapi-clean-example/.github/workflows/tests-coverage.yml):

```yaml
name: Tests & Coverage

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  unit-tests:
    name: Unit Tests + Coverage
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install dependencies
        run: uv sync

      - name: Run unit tests with coverage
        run: |
          uv run pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-fail-under=27

      - name: Upload coverage report to Codacy
        uses: codacy/codacy-coverage-reporter-action@v1
        if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository
        with:
          project-token: ${{ secrets.CODACY_PROJECT_TOKEN }}
          coverage-reports: coverage.xml

      - name: Upload HTML coverage report as artifact
        uses: actions/upload-artifact@v4
        with:
          name: coverage-html-report
          path: htmlcov/
          retention-days: 14
```

### Automatizaciones logradas:
1. **Ejecución en cada Push / PR:** Corre el suite en Ubuntu con `uv`.
2. **Control de Calidad (Quality Gate):** El build falla si la cobertura cae por debajo del 27%.
3. **Reporte Automático a Codacy:** Envía `coverage.xml` mediante el secreto `CODACY_PROJECT_TOKEN`.
4. **Artefactos descargables:** Publica el reporte HTML para consulta directa desde GitHub.

---

## 3. Repositorio Remoto y Enlaces

* **Repositorio en GitHub:** [https://github.com/FedeTerradas/fastapi-clean-example-coverage](https://github.com/FedeTerradas/fastapi-clean-example-coverage)
* **Ejecución de CI (Actions):** [GitHub Actions Runs](https://github.com/FedeTerradas/fastapi-clean-example-coverage/actions)
* **Dashboard de Codacy:** [Codacy Project Overview](https://app.codacy.com/gh/FedeTerradas/fastapi-clean-example-coverage/dashboard)
