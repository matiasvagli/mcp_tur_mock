"""
Turismo MCP Mock API
====================
API de demostración que simula:
  - Datos del usuario (preferencias, calendario, historial)
  - Servidor MCP de Turismo (vuelos, hoteles, búsqueda inteligente)

Todos los datos son generados aleatoriamente en cada request.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Carga automática del archivo .env si existe
load_dotenv()

from routers import user_router, mcp_router, ai_router

app = FastAPI(
    title="Turismo MCP Mock API",
    description=(
        "API de demostración para el concepto de MCP Server aplicado a "
        "una agencia de viajes. Simula datos de usuario y el inventario "
        "expuesto por el servidor MCP de Turismo."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Permite llamadas desde cualquier origen (útil para demos con frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(user_router.router, prefix="/user", tags=["Usuario"])
app.include_router(mcp_router.router, prefix="/mcp", tags=["MCP Server"])
app.include_router(ai_router.router, prefix="/ai", tags=["Agente IA 🤖"])


@app.get("/", tags=["Root"])
def root():
    """Health-check y descripción general de la API."""
    return {
        "service": "Turismo MCP Mock API",
        "version": "1.0.0",
        "description": "API de demostración del concepto MCP Server para agencias de viaje",
        "docs": "/docs",
        "endpoints": {
            "usuario": [
                "GET /user/preferences",
                "GET /user/calendar?month=YYYY-MM",
                "GET /user/travel-history",
            ],
            "mcp_server": [
                "GET /mcp/flights?origin=XXX&destination=YYY&date=YYYY-MM-DD&passengers=N",
                "GET /mcp/hotels?destination=XXX&checkin=YYYY-MM-DD&nights=N&guests=N",
                "POST /mcp/search",
                "GET /mcp/tools",
            ],
            "agente_ia": [
                "POST /ai/plan-trip",
                "POST /ai/chat",
                "GET /ai/status",
            ],
        },
    }
