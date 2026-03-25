# 🗺️ Roadmap: Turismo MCP Server Full-Featured

## 📋 Objetivo General

Convertir el mock actual (FastAPI + Gemini + datos random) en un MCP Server completo que soporte todo el ciclo de vida de bookings: **búsqueda → reserva temporal (hold) → confirmación con pago → modificaciones → cancelaciones**.

---

## 🏗️ Arquitectura Target

```
┌─────────────────────────────────────────────────────────┐
│            CLIENT (Claude / Cursor / Gemini)            │
└────────────────────────┬────────────────────────────────┘
                         │
                    MCP Protocol
                  (JSON-RPC / SSE)
                         │
┌────────────────────────▼────────────────────────────────┐
│                  MCP SERVER LAYER                        │
│        - Tool registration (search, hold, confirm...)   │
│        - Request/response handling                       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Search   │  │ Booking  │  │ Policies │  │ Changes │ │
│  │ Service  │  │ Service  │  │ Service  │  │ Service │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    DATA LAYER                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │  SQLite (in-memory)                             │   │
│  │  - flights (origin, dest, date, seats, price)   │   │
│  │  - hotels (city, name, rooms, price)            │   │
│  │  - holds (id, type, item_id, expires_at)        │   │
│  │  - bookings (id, hold_id, status, payment)      │   │
│  │  - policies (item_id, cancellation_rules)       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Sprints Detallados

### Sprint 0: Setup & Data Foundation (Día 1)
**Objetivo:** Tener una DB fake pero consistente que se pueda consultar

#### Tasks:
- [ ] **0.1 - Schema de DB**
  - Diseñar modelos SQLAlchemy: `Flight`, `Hotel`, `Hold`, `Booking`, `CancellationPolicy`
  - Decidir qué campos tiene cada tabla

- [ ] **0.2 - Seed script**
  - Generar 1000+ vuelos fake (10 rutas principales × 60 días × 3 vuelos/día)
  - Generar 500+ hoteles fake (20 ciudades × 25 hoteles/ciudad)
  - Generar políticas de cancelación por hotel/aerolínea

- [ ] **0.3 - DB initialization**
  - SQLite in-memory que se popula al startup
  - Script de seed ejecutable standalone para testing

#### Entregables:
```
turismo-mcp/
├── database.py           # Engine, SessionLocal, Base
├── models.py             # Flight, Hotel, Hold, Booking, Policy (SQLAlchemy)
├── seed.py               # Generación de datos fake + insert
└── test_db.py            # Script para verificar que el seed funciona
```

**Definición de Done:** Corrés `python seed.py` y tenés 1500+ registros en SQLite. Corrés queries básicos y devuelven datos.

---

### Sprint 1: Core Booking Lifecycle (Días 2-3)
**Objetivo:** Implementar el flujo básico: search → hold → confirm

#### Tasks:
- [ ] **1.1 - Refactor search tools para usar DB**
  - `search_flights(origin, dest, date)` → query a tabla `flights`
  - `search_hotels(city, checkin, checkout)` → query a tabla `hotels`
  - Devolver resultados reales desde DB (no random)

- [ ] **1.2 - Implementar `create_hold`**
  - Input: `type` (flight/hotel), `item_id`, `guest_info`, `dates`
  - Validar que el item existe en DB y tiene stock
  - Crear registro en tabla `holds` con `expires_at = now() + 30min`
  - Decrementar stock temporalmente (marcar como "on hold")
  - Devolver: `hold_id`, `expires_at`, `payment_link`, `total_price`

- [ ] **1.3 - TTL para holds expirados**
  - Background task (APScheduler o similar) que cada 5 min hace:
  ```sql
  UPDATE holds SET status='EXPIRED' 
  WHERE expires_at < NOW() AND status='ACTIVE'
  ```
  - Cuando expira un hold → **liberar stock** (seats/rooms)

- [ ] **1.4 - Implementar `confirm_booking`**
  - Input: `hold_id`, `payment_token` (mock)
  - Validar que hold existe, no expiró, y no fue usado
  - Crear registro en tabla `bookings` con `status=CONFIRMED`
  - Actualizar hold status → `CONFIRMED`
  - Decrementar stock definitivamente
  - Devolver: `booking_id`, `confirmation_number`, resumen

- [ ] **1.5 - Payment mock page**
  - Endpoint `/pay/{hold_id}` que renderiza HTML form básico
  - `POST /pay/{hold_id}/confirm` → llama a `confirm_booking()`
  - Mock de email de confirmación (log to console o archivo)

#### Entregables:
```
turismo-mcp/
├── services/
│   ├── search_service.py       # Queries a flights/hotels DB
│   ├── booking_service.py      # create_hold, confirm_booking
│   └── ttl_service.py          # Background task para expirar holds
├── routers/
│   ├── payment_router.py       # /pay/{hold_id} mock endpoints
│   └── booking_router.py       # REST wrappers (para testing)
└── templates/
    └── payment.html            # Form de pago simulado
```

**Definición de Done:**
- Podés buscar un vuelo
- Crear hold (stock baja temporalmente)
- Hold expira después de 30 min (stock vuelve)
- Confirmar booking desde payment page mock
- Todo logueado y observable

---

### Sprint 2: Policies & Modifications (Día 4)
**Objetivo:** Agregar policies engine y soporte para cambios/cancelaciones

#### Tasks:
- [ ] **2.1 - Policies engine**
  - Seedear políticas de cancelación por hotel/aerolínea
  - Modelo `CancellationPolicy` con reglas por días antes de checkin
  - `get_cancellation_policy(item_id)` tool

- [ ] **2.2 - Cancel booking**
  - `cancel_booking(booking_id, reason)`
  - Calcular refund según policy + días restantes
  - Liberar stock (rooms/seats vuelven al pool)
  - Crear registro de cancelación con refund amount

- [ ] **2.3 - Modify booking (auto)**
  - `modify_booking(booking_id, changes)` para casos simples
  - Validar: nueva fecha tiene stock disponible
  - Calcular fee de modificación según policy
  - Actualizar booking + ajustar stock

- [ ] **2.4 - Request change (manual)**
  - `request_change(booking_id, changes, message)` para casos complejos
  - Crear tabla `change_requests` con status `PENDING`
  - Devolver `ticket_id` + estimated response time
  - Mock de notificación a ops team (log)

#### Entregables:
```
turismo-mcp/
├── services/
│   ├── policy_service.py       # get_policy, calculate_refund, calculate_fee
│   └── change_service.py       # modify_booking, request_change, cancel
├── models.py                    # +ChangeRequest, +CancellationPolicy
└── seed.py                      # +policies seed data
```

**Definición de Done:**
- Tool `get_cancellation_policy` devuelve reglas del item
- Podés cancelar un booking y el refund se calcula correctamente
- Podés modificar fechas (si hay stock) con fee aplicado
- Cambios complejos crean tickets para review manual

---

### Sprint 3: MCP Protocol Integration (Días 5-6)
**Objetivo:** Exponer todo vía MCP oficial, no solo REST

#### Tasks:
- [ ] **3.1 - Elegir transport layer**
  - Opción A: `mcp` Python SDK (stdio transport)
  - Opción B: Custom SSE implementation
  - Recomendación: **Opción A** (más estándar)

- [ ] **3.2 - MCP Server setup**
  - Instalar `mcp` SDK: `pip install mcp`
  - Crear `mcp_server.py` con tool registration
  - Mapear cada business logic function a MCP tool

- [ ] **3.3 - Tool definitions**
  - Definir schema de cada tool (inputs/outputs en JSON Schema)
  - Tools a exponer:
    - `search_flights`
    - `search_hotels`
    - `create_hold`
    - `confirm_booking`
    - `cancel_booking`
    - `modify_booking`
    - `request_change`
    - `get_cancellation_policy`
    - `get_booking_status`

- [ ] **3.4 - Testing con cliente MCP**
  - Configurar Claude Desktop / Cursor para conectarse
  - Test end-to-end: buscar → hold → confirm desde Claude
  - Debuggear issues de serialización/protocol

#### Entregables:
```
turismo-mcp/
├── mcp_server.py               # MCP Server con tool registration
├── claude_desktop_config.json  # Ejemplo de config para Claude Desktop
└── README_MCP.md               # Docs de cómo conectarse vía MCP
```

**Definición de Done:**
- Servidor MCP corriendo y escuchando en stdio
- Claude Desktop puede descubrir y llamar todos los tools
- Un booking completo funciona end-to-end desde Claude chat

---

### Sprint 4: Observability & Polish (Día 7)
**Objetivo:** Logging, métricas, docs y demo material

#### Tasks:
- [ ] **4.1 - Structured logging**
  - Reemplazar `print()` con logging estructurado (JSON)
  - Log levels apropiados (DEBUG, INFO, WARNING, ERROR)
  - Logs de eventos críticos: `hold_created`, `booking_confirmed`, `hold_expired`

- [ ] **4.2 - Métricas básicas**
  - Contador: holds creados, bookings confirmados, cancelaciones
  - Tasa de conversión: holds → bookings
  - Tiempo promedio hold → confirm
  - Guardar en tabla `metrics` o logs

- [ ] **4.3 - Documentación completa**
  - README actualizado con:
    - Architecture diagram
    - Setup instructions
    - MCP integration guide
    - Todos los tools documentados con ejemplos
  - Diagramas de secuencia (search → hold → confirm)

- [ ] **4.4 - Video demo**
  - Screen recording (5-7 min) mostrando:
    - CLI: buscar vuelo
    - CLI: crear hold
    - Browser: payment page mock
    - CLI: booking confirmado
    - CLI: cancelar con refund calculation
  - Subir a YouTube unlisted

#### Entregables:
```
turismo-mcp/
├── docs/
│   ├── ARCHITECTURE.md         # Diagramas + explicación de componentes
│   ├── TOOLS_REFERENCE.md      # Cada tool documentado
│   └── diagrams/               # Sequence diagrams (Mermaid o PNG)
├── demo_video.mp4
└── README.md                   # Actualizado con todo
```

**Definición de Done:**
- Logs estructurados en todos los servicios
- README tiene todo lo necesario para que alguien clone y corra
- Video demo publicado y linkeado en README

---

## 📊 Métricas de Éxito del Proyecto

Al final del roadmap deberías poder:

**✅ Desde Claude Desktop:**
- Buscar vuelos/hoteles en lenguaje natural
- Crear hold de un vuelo
- Recibir payment link
- Confirmar booking (mock payment)
- Consultar cancellation policy
- Modificar o cancelar booking

**✅ Desde el código:**
- DB con 1500+ registros fake pero consistentes
- Stock management funcional (decrements/increments)
- TTL automático para holds expirados
- MCP protocol oficial implementado

**✅ Observabilidad:**
- Logs estructurados de todos los eventos
- Métricas de conversión calculables
- Docs completas para reproducir

---

## 🛠️ Stack Final

| Capa | Tecnología |
|---|---|
| MCP Protocol | `mcp` Python SDK |
| API Layer | FastAPI (REST para debug) |
| Business Logic | Python services (clean architecture) |
| Database | SQLite in-memory (SQLAlchemy ORM) |
| Background Jobs | APScheduler (TTL expiration) |
| AI Agent | Gemini 2.0 Flash (function calling) |
| Payment Mock | HTML form + webhook endpoint |
| Logging | `structlog` (JSON output) |
