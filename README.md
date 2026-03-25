# 🧳 Turismo MCP Server — Demo

> **Demo conceptual** de cómo una agencia de viajes puede implementar un **MCP Server** para integrarse con agentes de IA personales y ofrecer experiencias ultra-personalizadas.

---

## 🎯 ¿Qué es esto?

Este proyecto simula el caso de uso de **Model Context Protocol (MCP)** aplicado a una agencia de viajes.

En lugar de que la agencia desarrolle su propio chatbot (el modelo de hoy), expone su inventario de vuelos y hoteles como un **MCP Server**. Así, el agente de IA personal del usuario puede consultarlo directamente, combinando los datos de la agencia con el contexto privado del usuario (calendario, preferencias, historial) para generar propuestas de viaje altamente personalizadas.

---

## 🤔 El Problema: el chatbot en la web ya no alcanza

El modelo actual funciona así:

```
Usuario → entra a la web de la agencia → chatbot de la agencia → resultados
```

El problema es que **el chatbot de la agencia no te conoce**. No sabe:
- Que el próximo jueves tenés una reunión importante
- Que preferís ventana y viajás siempre con tu familia
- Que ya fuiste a Cancún dos veces y no querés repetir
- Que tenés un presupuesto mensual de viajes

Cada vez que entrás, empezás de cero.

---

## 💡 La Solución: invertir el paradigma con MCP

**Model Context Protocol (MCP)** es un estándar abierto creado por Anthropic que permite que agentes de IA se conecten a fuentes de datos externas de forma segura y estandarizada. Funciona como una "API para IAs".

Con MCP, el flujo cambia completamente:

```
Usuario → habla con SU agente personal (Claude, Gemini, GPT, etc.)
                    ↓ el agente ya conoce al usuario
              consulta el calendario del usuario
              consulta las preferencias guardadas
              consulta el MCP Server de la agencia  ←── acá está la clave
                    ↓
              arma una propuesta ultra-personalizada
```

**La agencia no necesita desarrollar IA propia.**
**El usuario no tiene que repetir sus preferencias.**
**El resultado es la personalización real.**

---

## 🏗️ Arquitectura del Demo

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENTE IA (Gemini)                      │
│            "Asistente Personal de Viajes"                   │
│                  POST /ai/plan-trip                         │
└──────────────────────┬──────────────────┬───────────────────┘
                       │                  │
          ┌────────────▼───┐    ┌─────────▼──────────┐
          │  DATOS USUARIO │    │   MCP SERVER       │
          │  (simulados)   │    │   (simulado)       │
          │                │    │                    │
          │ /user/prefs    │    │ /mcp/flights       │
          │ /user/calendar │    │ /mcp/hotels        │
          │ /user/history  │    │ /mcp/search        │
          │                │    │ /mcp/tools         │
          └────────────────┘    └────────────────────┘
          
          ↑ Lo que el agente     ↑ Lo que la agencia
            ya sabe del usuario    expone vía MCP
            (privado, del user)    (inventario público)
```

Este demo simula los **tres componentes** en una sola API FastAPI:

| Componente | Endpoints | Qué simula |
|---|---|---|
| **Datos del Usuario** | `/user/*` | Lo que el agente personal del usuario ya conoce (preferencias, calendario, historial) |
| **MCP Server de la Agencia** | `/mcp/*` | El inventario de vuelos y hoteles expuesto por la agencia via MCP |
| **Agente IA** | `/ai/*` | Gemini 2.0 Flash orquestando todo con function calling |

---

## 🚀 Quick Start

### 1. Clonar e instalar

```bash
git clone <repo>
cd turismo-mcp-demo

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar la API Key de Gemini

```bash
# Copiá el archivo de ejemplo
cp .env.example .env

# Editá .env y pegá tu clave
# Obtené la clave gratis en: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=tu-clave-aqui
```

```bash
# O exportala directamente:
export GEMINI_API_KEY="tu-clave-aqui"
```

### 3. Levantar el servidor

```bash
uvicorn main:app --reload --port 8001
```

Abrí el Swagger interactivo: **http://localhost:8001/docs** 🎉

---

## � CLI — Interfaz de Terminal

El proyecto incluye un CLI interactivo (`cli.py`) que muestra las respuestas del agente formateadas con colores y paneles en la terminal. Ideal para demos en vivo.

### Modo chat interactivo (recomendado para la demo 🎯)

```bash
python3 cli.py
```

Chat multi-turno: escribís como con un amigo, el agente responde y podés ir refinando la propuesta.

```
🧳 Asistente Personal de Viajes
   Powered by Google Gemini · Turismo MCP Demo

Vos: che fijate si tengo libre este finde y armame algo para desconectar

[agente consulta calendario, preferencias, hoteles...]

📍 Colonia del Sacramento, Uruguay
🏨 Hotel Boutique Vista Río ⭐⭐⭐⭐
🚗 Auto · 180km · USD 310 estimado
```

### Consulta directa (un solo comando)

```bash
python3 cli.py plan "escapada este finde con mi mujer, si hay mas de 400km busca vuelo"
```

### Ver estado del servidor

```bash
python3 cli.py status
```

### Apuntar a otro servidor

```bash
python3 cli.py --url http://otro-servidor:8001
```

### Comandos disponibles dentro del chat

| Comando | Acción |
|---|---|
| `reset` | Empezar una conversación nueva |
| `salir` / `chau` | Cerrar el CLI |

---

## �📡 Endpoints

### 🧑 Datos del Usuario
> Simulan lo que el agente personal del usuario ya conoce. En producción, estos datos vendrían del perfil del usuario en su agente (Google, Apple, Anthropic, etc.)

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/user/preferences` | Preferencias de viaje del usuario |
| `GET` | `/user/calendar?month=YYYY-MM` | Eventos del mes y fechas libres |
| `GET` | `/user/travel-history` | Historial de viajes con ratings |

### ✈️🏨 MCP Server — Inventario de la Agencia
> Simulan lo que la agencia expone a través del protocolo MCP. En producción, estos endpoints serían el MCP Server oficial de la agencia conectado a su base de datos real.

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/mcp/flights` | Buscar vuelos disponibles |
| `GET` | `/mcp/hotels` | Buscar hoteles disponibles |
| `POST` | `/mcp/search` | Búsqueda inteligente por preferencias |
| `GET` | `/mcp/tools` | Listado de tools disponibles (formato MCP) |

### 🤖 Agente IA (Gemini)
> El agente que une todo: interpreta lenguaje natural, consulta los datos del usuario y el MCP Server, y arma la propuesta final.

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/ai/plan-trip` | Planificador de viajes con lenguaje natural |
| `POST` | `/ai/chat` | Chat multi-turno con contexto de conversación |
| `GET` | `/ai/status` | Estado del agente y sesiones activas |

---

## 🎭 Casos de Uso — Ejemplos Reales

### Ejemplo 1: Escapada de Fin de Semana

> *"che fijate si tengo libre este finde y armame algo para desconectar, presupuesto bajo"*

**Con el CLI:**
```bash
python3 cli.py plan "che fijate si tengo libre este finde y armame algo para desconectar, presupuesto bajo"
```

**Con curl:**
```bash
curl -X POST http://localhost:8001/ai/plan-trip \
  -H "Content-Type: application/json" \
  -d '{"query": "che fijate si tengo libre este finde y armame algo para desconectar, presupuesto bajo"}'
```

El agente va a:
1. Revisar el calendario de marzo para ver si el sábado/domingo está libre
2. Consultar las preferencias del usuario (tipo de viaje, estilo)
3. Calcular que un finde = destino cercano → auto
4. Buscar hoteles en Colonia del Sacramento / Rosario / Mar del Plata
5. Retornar una propuesta con hotel + distancia en auto + alternativas

---

### Ejemplo 2: Viaje en Familia a la Playa

> *"quiero ir a la playa en junio con mi familia, que sea tranquilo y con pileta para los chicos"*

```bash
curl -X POST http://localhost:8001/ai/plan-trip \
  -H "Content-Type: application/json" \
  -d '{"query": "quiero ir a la playa en junio con mi familia, que sea tranquilo y con pileta para los chicos"}'
```

El agente va a:
1. Detectar "junio" y revisar disponibilidad en el calendario de junio
2. Identificar "familia + playa + pileta" → buscar hoteles kid-friendly con piscina
3. Consultar historial para no repetir destinos visitados
4. Evaluar distancia → ¿Cancún, Punta Cana o Mar del Plata?
5. Retornar paquetes ordenados por score de compatibilidad

---

### Ejemplo 3: Aniversario Romántico

> *"mi aniversario es en 2 meses, buscame algo romántico, presupuesto no importa"*

**Con el CLI:**
```bash
python3 cli.py plan "mi aniversario es en 2 meses, buscame algo romántico, presupuesto no importa"
```

**Con curl:**
```bash
curl -X POST http://localhost:8001/ai/plan-trip \
  -H "Content-Type: application/json" \
  -d '{"query": "mi aniversario es en 2 meses, buscame algo romántico, presupuesto no importa"}'
```

---

### Ejemplo 4: Escapada con Condición de Transporte

> *"este viernes no tengo nada, buscame una escapada con mi mujer, si hay que hacer más de 400km busca avión"*

**Con el CLI:**
```bash
python3 cli.py plan "este viernes no tengo nada, escapada con mi mujer, mas de 400km busca avion"
```

**Con curl:**
```bash
curl -X POST http://localhost:8001/ai/plan-trip \
  -H "Content-Type: application/json" \
  -d '{"query": "este viernes no tengo nada, buscame una escapada con mi mujer, si hay que hacer mas de 400km busca avion sino voy en auto"}'
```

---

### Ejemplo 5: Chat Multi-turno con el CLI

Esta es la forma más natural de interactuar con el agente:

```bash
python3 cli.py   # abrís el chat interactivo
```

```
Vos: buscame escapada este finde
[Agente propone Colonia del Sacramento]

Vos: y si voy el sábado mejor?
[Agente ajusta las fechas]

Vos: dale, pero hotel más barato
[Agente busca alternativas más económicas]

Vos: salir
```

**También con curl (turno a turno):**

```bash
# Turno 1: solicitud inicial
curl -X POST http://localhost:8001/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "buscame escapada este finde"}'

# → Respuesta incluye: "conversation_id": "a3f8c1b2"

# Turno 2: refinar la propuesta (misma conversación)
curl -X POST http://localhost:8001/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "y si voy el sábado mejor?", "conversation_id": "a3f8c1b2"}'

# Turno 3: ajustar presupuesto
curl -X POST http://localhost:8001/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "dale, pero buscame opciones de hotel más económicas", "conversation_id": "a3f8c1b2"}'
```

---

### Respuesta Ejemplo de `/ai/plan-trip`

```json
{
  "query": "che fijate si tengo libre este finde y armame algo para desconectar",
  "analysis": {
    "calendar_check": "El sábado 7 y domingo 8 de marzo están libres, sin compromisos",
    "travel_style": "escapada tranquila, perfil aventura/pareja",
    "transport_decision": "Destinos < 400km → auto. Más flexible y económico para finde corto.",
    "duration": "2-3 días (sábado a lunes)",
    "companions": "pareja",
    "budget": "económico/moderado según preferencias"
  },
  "proposal": {
    "destination": "Colonia del Sacramento, Uruguay",
    "reason": "A solo 180km de Buenos Aires, ideal para ir en auto por el túnel o el puente. Ciudad histórica, romántica y muy tranquila. Perfecta para desconectar sin apuros.",
    "dates": {
      "departure": "2026-03-07",
      "return": "2026-03-09"
    },
    "transport": {
      "mode": "auto",
      "reason": "180km desde BUE, menos de 2 horas. Auto es lo más cómodo y económico.",
      "flight_option": null
    },
    "hotel": {
      "name": "Hotel Boutique Posada del Angel",
      "stars": 4,
      "price_per_night": 95,
      "price_total": 190,
      "amenities": ["wifi gratuito", "desayuno incluido", "terraza con vista al río"],
      "why": "Céntrico, encantador y con desayuno incluido. Ideal para explorar la ciudad a pie."
    },
    "total_estimate_usd": 310,
    "alternatives": [
      {
        "destination": "Rosario, Argentina",
        "reason": "300km, ciudad vibrante con buena gastronomía y costera del Paraná",
        "distance_km": 300
      },
      {
        "destination": "San Antonio de Areco",
        "reason": "110km, pueblo gaucho con mucho encanto, perfecto para desconectar",
        "distance_km": 110
      }
    ]
  },
  "agent_note": "Colonia es un golazo para este finde, te va a encantar. ¡Que la pasen bomba!"
}
```

---

## 🔮 Visión a Futuro: Cómo Sería en Producción

### Lo que cambiaría:

| Componente | Demo (Este Proyecto) | Producción Real |
|---|---|---|
| Datos del usuario | Generados aleatoriamente | Perfil real del agente personal (Google AI, Claude, etc.) |
| Inventario de viajes | Datos random en memoria | Base de datos real de vuelos y hoteles (GDS, Amadeus, etc.) |
| Autenticación | Sin auth | OAuth 2.0 con consentimiento del usuario |
| Protocolo MCP | REST API simplificada | Protocolo MCP oficial (JSON-RPC sobre SSE) |
| Agente IA | Gemini con function calling | Multiples agentes (Claude, GPT, Gemini) conectados via MCP |
| Transporte | Mock de distancias | Google Maps / Distance Matrix API |

### El flujo real sería:

```
Usuario: "Gemini, busquemos un viaje para las vacaciones de julio"

Gemini:
  → lee tu calendario en Google Calendar  (OAuth, sin compartir datos)
  → lee tus preferencias de tu perfil
  → llama al MCP Server de la agencia  (tool: search_packages)
  → llama al MCP Server del banco       (tool: check_budget)
  → arma propuesta → pide confirmación → reserva directamente
```

**La agencia solo necesita mantener su MCP Server actualizado.** El sistema operativo de IA del usuario hace el resto.

---

## 🛠️ Tech Stack

| Tecnología | Uso |
|---|---|
| **FastAPI** | Framework API REST, documentación automática con Swagger |
| **Google Gemini 2.0 Flash** | Agente IA con function calling para procesamiento de lenguaje natural |
| **Pydantic v2** | Validación y serialización de datos |
| **HTTPX** | Llamadas HTTP internas (agente → endpoints MCP) |
| **Uvicorn** | Servidor ASGI de alta performance |
| **Python 3.10+** | Lenguaje base |

---

## ⚠️ Limitaciones del Demo

Este es un **prototipo conceptual**, no un sistema de producción:

- 📊 **Datos generados aleatoriamente** — cada request devuelve datos distintos
- 💾 **Sin base de datos** — todo en memoria, se reinicia con el servidor
- 🔐 **Sin autenticación real** — cualquiera puede llamar a los endpoints
- 📡 **MCP simplificado** — implementado como REST API en lugar del protocolo MCP oficial (JSON-RPC sobre SSE)
- 📍 **Distancias mockeadas** — el cálculo de km es aproximado / estimado
- 🌐 **Sin datos reales de vuelos** — precios y disponibilidad son ficticios

---

## 📚 Referencias

- [🔗 Model Context Protocol — Sitio Oficial](https://modelcontextprotocol.io/)
- [📖 Anthropic MCP Docs](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
- [⚡ Google Gemini Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [🛠️ google-genai SDK (nuevo)](https://github.com/googleapis/python-genai)
- [🚀 FastAPI Docs](https://fastapi.tiangolo.com/)

---

## 📁 Estructura del Proyecto

```
mcp_mock/
├── main.py                 # FastAPI app: CORS, routers, carga .env
├── models.py               # Schemas Pydantic (usuario, vuelos, hoteles, MCP tools)
├── data_generator.py       # Generación de datos random realistas
├── ai_agent.py             # Agente Gemini: tools, function calling, loop
├── cli.py                  # CLI interactivo con Rich (modo chat y consulta directa)
├── routers/
│   ├── user_router.py      # GET /user/* (datos del usuario)
│   ├── mcp_router.py       # GET|POST /mcp/* (inventario de la agencia)
│   └── ai_router.py        # POST /ai/* (agente IA)
├── requirements.txt
├── .env.example            # Template de variables de entorno
├── .env                    # Variables de entorno reales (no commitear)
└── README.md
```

---

## � Autor

**Matías Vagliviello** — Demo para presentación del concepto MCP Server aplicado a agencias de viajes.

---

> 💡 **TL;DR:** Este demo muestra que el futuro no es "la agencia tiene IA". Es "el usuario tiene IA, y la agencia le da acceso a su inventario vía MCP para que esa IA trabaje para el usuario". La agencia de turismo se vuelve compatible con todos los agentes del mundo sin desarrollar ninguno.

---

## 🚧 ¿A dónde va esto?

Este proyecto es un mock conceptual, pero está diseñado para escalar a un **MCP Server completo y production-ready**.

El siguiente paso es convertir los datos random y el protocolo simplificado en un sistema real con base de datos, ciclo de vida de bookings (hold → pago → confirmación → cancelación), stock management y protocolo MCP oficial.

👉 **[Ver Roadmap completo →](README_ROADMAP.md)**
