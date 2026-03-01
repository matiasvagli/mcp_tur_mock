"""
Agente de IA - Asistente Personal de Viajes
============================================
Usa Google Gemini 2.0 Flash con Function Calling (SDK google-genai)
para interpretar queries en lenguaje natural argentino y armar propuestas
de viaje completas consultando el calendario, preferencias e inventario MCP.

Flujo de cada request:
  1. Usuario manda query natural.
  2. Gemini decide qué tools llamar (calendario, preferencias, vuelos, etc.)
  3. El agente ejecuta las tools como llamadas HTTP internas al propio servidor.
  4. Gemini procesa los resultados y genera la propuesta estructurada en JSON.
"""

from __future__ import annotations

import json
import os
import random
import uuid
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

import httpx
from google import genai
from google.genai import types as gentypes

# ── Config ─────────────────────────────────────────────────────────────────────

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Historial de conversaciones en memoria { conversation_id → [contents] }
_conversation_store: dict[str, list] = defaultdict(list)


def _get_client() -> genai.Client:
    """Crea y retorna un cliente Gemini. Falla con mensaje claro si no hay API key."""
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY no configurada. "
            "Exportala con: export GEMINI_API_KEY='tu-clave' "
            "o creá un archivo .env basado en .env.example"
        )
    return genai.Client(api_key=GEMINI_API_KEY)


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _http_get(path: str, params: dict | None = None) -> dict:
    try:
        r = httpx.get(f"{BASE_URL}{path}", params=params or {}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}


# ── Implementación de las tools ────────────────────────────────────────────────

def get_user_calendar(month: str) -> dict:
    """Consulta el calendario del usuario para el mes indicado (YYYY-MM)."""
    return _http_get("/user/calendar", {"month": month})


def get_user_preferences() -> dict:
    """Obtiene las preferencias de viaje del usuario."""
    return _http_get("/user/preferences")


def get_user_travel_history() -> dict:
    """Recupera el historial de viajes pasados del usuario."""
    return _http_get("/user/travel-history")


def search_flights(
    origin: str,
    destination: str,
    date_str: str,
    passengers: int = 2,
) -> dict:
    """Busca vuelos disponibles entre dos aeropuertos."""
    return _http_get(
        "/mcp/flights",
        {
            "origin": origin,
            "destination": destination,
            "date": date_str,
            "passengers": passengers,
        },
    )


def search_hotels(
    destination: str,
    checkin: str,
    nights: int,
    guests: int = 2,
) -> dict:
    """Busca hoteles disponibles en el destino para las fechas indicadas."""
    return _http_get(
        "/mcp/hotels",
        {
            "destination": destination,
            "checkin": checkin,
            "nights": nights,
            "guests": guests,
        },
    )


def calculate_driving_distance(origin: str, destination: str) -> dict:
    """
    Calcula la distancia aproximada en km entre dos ciudades.
    < 450km → auto recomendado. >= 450km → avión recomendado.
    """
    distances_from_bue: dict[str, int] = {
        "montevideo": 230, "colonia del sacramento": 180, "rosario": 300,
        "córdoba": 700, "mendoza": 1050, "mar del plata": 400,
        "bariloche": 1660, "ushuaia": 3240, "salta": 1580, "iguazú": 1340,
        "punta del este": 330, "asunción": 1200, "santiago": 1140,
        "lima": 3700, "río de janeiro": 2000, "são paulo": 1760,
        "miami": 8500, "nueva york": 10400, "madrid": 10100, "barcelona": 10200,
        "paris": 11000, "roma": 11200, "tigre": 30, "luján": 70,
        "pilar": 55, "san antonio de areco": 110, "villa gesell": 380,
        "miramar": 430, "necochea": 500, "santa rosa": 600,
        "cancún": 9200, "punta cana": 7800, "cartagena": 5100,
        "buenos aires": 0,
    }
    dest_lower = destination.lower().strip()
    km = None
    for key, val in distances_from_bue.items():
        if key in dest_lower or dest_lower in key:
            km = val + random.randint(-20, 20)
            break
    if km is None:
        km = random.randint(400, 1000)

    return {
        "origin": origin,
        "destination": destination,
        "distance_km": km,
        "transport_recommendation": "auto" if km < 450 else "avión",
        "note": "Distancia aproximada. < 450km → auto. >= 450km → avión.",
    }


# ── Mapa tools ejecutables ─────────────────────────────────────────────────────

TOOL_FUNCTIONS: dict[str, Any] = {
    "get_user_calendar": get_user_calendar,
    "get_user_preferences": get_user_preferences,
    "get_user_travel_history": get_user_travel_history,
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "calculate_driving_distance": calculate_driving_distance,
}

# ── Definición de tools para Gemini (nuevo SDK) ────────────────────────────────

GEMINI_TOOLS = [
    gentypes.Tool(
        function_declarations=[
            gentypes.FunctionDeclaration(
                name="get_user_calendar",
                description=(
                    "Consulta el calendario del usuario para ver eventos y fechas libres. "
                    "SIEMPRE llamar antes de sugerir fechas."
                ),
                parameters=gentypes.Schema(
                    type="OBJECT",
                    properties={
                        "month": gentypes.Schema(
                            type="STRING",
                            description="Mes a consultar en formato YYYY-MM. Ej: '2026-03'",
                        )
                    },
                    required=["month"],
                ),
            ),
            gentypes.FunctionDeclaration(
                name="get_user_preferences",
                description=(
                    "Obtiene las preferencias de viaje del usuario: tipo de destino, "
                    "estilo, presupuesto y preferencias personales."
                ),
                parameters=gentypes.Schema(type="OBJECT", properties={}),
            ),
            gentypes.FunctionDeclaration(
                name="get_user_travel_history",
                description="Recupera el historial de viajes pasados para evitar repetir destinos recientes.",
                parameters=gentypes.Schema(type="OBJECT", properties={}),
            ),
            gentypes.FunctionDeclaration(
                name="search_flights",
                description=(
                    "Busca opciones de vuelo entre dos aeropuertos. "
                    "Usar cuando el destino está a más de 400km o el usuario menciona avión."
                ),
                parameters=gentypes.Schema(
                    type="OBJECT",
                    properties={
                        "origin": gentypes.Schema(
                            type="STRING",
                            description="Código IATA del aeropuerto de origen. Ej: 'BUE'",
                        ),
                        "destination": gentypes.Schema(
                            type="STRING",
                            description="Código IATA del aeropuerto de destino. Ej: 'MIA'",
                        ),
                        "date_str": gentypes.Schema(
                            type="STRING",
                            description="Fecha de salida en formato YYYY-MM-DD",
                        ),
                        "passengers": gentypes.Schema(
                            type="INTEGER",
                            description="Cantidad de pasajeros (por defecto 2)",
                        ),
                    },
                    required=["origin", "destination", "date_str"],
                ),
            ),
            gentypes.FunctionDeclaration(
                name="search_hotels",
                description="Busca hoteles disponibles en el destino elegido para las fechas del viaje.",
                parameters=gentypes.Schema(
                    type="OBJECT",
                    properties={
                        "destination": gentypes.Schema(
                            type="STRING",
                            description="Ciudad o código IATA del destino. Ej: 'CUN' o 'Cancún'",
                        ),
                        "checkin": gentypes.Schema(
                            type="STRING",
                            description="Fecha de check-in en formato YYYY-MM-DD",
                        ),
                        "nights": gentypes.Schema(
                            type="INTEGER",
                            description="Cantidad de noches de estadía",
                        ),
                        "guests": gentypes.Schema(
                            type="INTEGER",
                            description="Cantidad de huéspedes (por defecto 2)",
                        ),
                    },
                    required=["destination", "checkin", "nights"],
                ),
            ),
            gentypes.FunctionDeclaration(
                name="calculate_driving_distance",
                description=(
                    "Calcula la distancia aproximada en km entre dos ciudades para decidir "
                    "si conviene auto o avión. Usar cuando hay duda sobre el transporte."
                ),
                parameters=gentypes.Schema(
                    type="OBJECT",
                    properties={
                        "origin": gentypes.Schema(
                            type="STRING",
                            description="Ciudad de origen. Ej: 'Buenos Aires'",
                        ),
                        "destination": gentypes.Schema(
                            type="STRING",
                            description="Ciudad de destino. Ej: 'Mar del Plata'",
                        ),
                    },
                    required=["origin", "destination"],
                ),
            ),
        ]
    )
]

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""Sos el asistente personal de viajes del usuario. Hablás argentino, sos copado y muy resolutivo.

HOY ES: {date.today().isoformat()} (Argentina, UTC-3)

TU PROCESO OBLIGATORIO (en este orden):
1. Interpretá la query: fechas relativas, duración, compañía, presupuesto, tipo de viaje.
2. Llamá a get_user_preferences() para entender el estilo del usuario.
3. Calculá el mes correspondiente y llamá a get_user_calendar(month) para ver disponibilidad REAL.
4. Llamá a get_user_travel_history() para evitar repetir destinos recientes.
5. Si no está claro el transporte, llamá a calculate_driving_distance() para decidir.
   - < 450km → auto. >= 450km → avión. Salvo que el usuario diga otra cosa.
6. Buscá hoteles con search_hotels() SIEMPRE.
7. Si el transporte es avión, buscá vuelos con search_flights().
8. Armá y retorná el JSON final.

REGLAS DE FECHAS RELATIVAS:
- "Este viernes" → próximo viernes desde hoy ({date.today().isoformat()})
- "Este finde / fin de semana" → próximo sábado
- "La semana que viene" → lunes de la próxima semana
- "En 2 meses" → misma fecha + 2 meses
- "En junio" → primer fin de semana de junio del año corriente

RESPUESTA FINAL: Siempre terminá con este JSON entre ```json ... ```, sin nada después:
```json
{{
  "query": "<query original>",
  "analysis": {{
    "calendar_check": "<resumen de disponibilidad encontrada>",
    "travel_style": "<estilo de viaje detectado>",
    "transport_decision": "<auto o avión y por qué>",
    "duration": "<duración detectada>",
    "companions": "<con quién viaja>",
    "budget": "<presupuesto detectado o inferido>"
  }},
  "proposal": {{
    "destination": "<ciudad, país>",
    "reason": "<por qué este destino, 2-3 oraciones>",
    "dates": {{
      "departure": "YYYY-MM-DD",
      "return": "YYYY-MM-DD"
    }},
    "transport": {{
      "mode": "auto|avión|barco",
      "reason": "<por qué este modo>",
      "flight_option": null
    }},
    "hotel": {{
      "name": "<nombre del hotel>",
      "stars": 0,
      "price_per_night": 0.0,
      "price_total": 0.0,
      "amenities": ["..."],
      "why": "<por qué este hotel específico>"
    }},
    "total_estimate_usd": 0.0,
    "alternatives": [
      {{
        "destination": "<ciudad alternativa>",
        "reason": "<por qué es buena alternativa>",
        "distance_km": 0
      }}
    ]
  }},
  "agent_note": "<comentario final en argentino copado>"
}}
```"""


# ── Ejecutor de tool calls ─────────────────────────────────────────────────────

def _execute_tool_call(fn_name: str, fn_args: dict) -> str:
    """Ejecuta la tool y retorna el resultado como string JSON."""
    fn = TOOL_FUNCTIONS.get(fn_name)
    if not fn:
        return json.dumps({"error": f"Tool '{fn_name}' no encontrada."})
    try:
        result = fn(**fn_args)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _parse_response(text: str) -> dict:
    """Extrae el JSON estructurado de la respuesta de Gemini."""
    import re
    match = re.search(r"```json\s*([\s\S]+?)\s*```", text)
    raw = match.group(1) if match else text
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: buscar cualquier bloque JSON en el texto
        match2 = re.search(r"\{[\s\S]+\}", text)
        if match2:
            try:
                return json.loads(match2.group(0))
            except Exception:
                pass
        return {
            "query": "",
            "analysis": {},
            "proposal": {"raw_response": text},
            "agent_note": "Respuesta en formato libre.",
        }


# ── Loop de function calling ───────────────────────────────────────────────────

def _run_agent(
    user_message: str,
    history: list | None = None,
) -> tuple[dict, list]:
    """
    Ejecuta el loop completo de Gemini con function calling.

    Args:
        user_message: Query del usuario.
        history: Historial previo de conversación.

    Returns:
        (respuesta_estructurada, historial_actualizado)
    """
    client = _get_client()

    # Construir el historial de contents para la API
    contents: list = list(history or [])
    contents.append(
        gentypes.Content(
            role="user",
            parts=[gentypes.Part(text=user_message)],
        )
    )

    config = gentypes.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=GEMINI_TOOLS,
        tool_config=gentypes.ToolConfig(
            function_calling_config=gentypes.FunctionCallingConfig(mode="AUTO")
        ),
        temperature=0.7,
    )

    max_iterations = 12
    for _ in range(max_iterations):
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]
        # Agregar respuesta del modelo al historial
        contents.append(candidate.content)

        # Verificar si hay function calls
        function_calls = [
            p for p in candidate.content.parts
            if p.function_call is not None
        ]

        if not function_calls:
            # No hay más tool calls → Gemini terminó
            break

        # Ejecutar todas las tools y preparar respuestas
        tool_response_parts = []
        for part in function_calls:
            fn_name = part.function_call.name
            fn_args = dict(part.function_call.args)
            result_str = _execute_tool_call(fn_name, fn_args)

            tool_response_parts.append(
                gentypes.Part(
                    function_response=gentypes.FunctionResponse(
                        name=fn_name,
                        response={"result": result_str},
                    )
                )
            )

        # Agregar respuestas de tools al historial
        contents.append(
            gentypes.Content(role="user", parts=tool_response_parts)
        )

    # Extraer texto final de la última respuesta
    final_text = ""
    for part in candidate.content.parts:
        if hasattr(part, "text") and part.text:
            final_text += part.text

    structured = _parse_response(final_text)
    return structured, contents


# ── Funciones públicas ─────────────────────────────────────────────────────────

def plan_trip(query: str) -> dict:
    """Planifica un viaje a partir de una query en lenguaje natural."""
    result, _ = _run_agent(query)
    if not result.get("query"):
        result["query"] = query
    return result


def chat_turn(message: str, conversation_id: str) -> tuple[dict, str]:
    """
    Procesa un turno de conversación manteniendo el contexto en memoria.

    Returns:
        (respuesta_estructurada, conversation_id)
    """
    if not conversation_id:
        conversation_id = str(uuid.uuid4())[:8]

    history = _conversation_store.get(conversation_id, [])
    result, new_history = _run_agent(message, history)
    _conversation_store[conversation_id] = new_history

    if not result.get("query"):
        result["query"] = message

    return result, conversation_id


def get_active_conversations() -> dict:
    return {
        "active_conversations": len(_conversation_store),
        "conversation_ids": list(_conversation_store.keys()),
    }
