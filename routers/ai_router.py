"""
Router del Agente IA de Viajes
===============================
Expone los endpoints de IA que usan Google Gemini para interpretar
queries en lenguaje natural y armar propuestas de viaje completas.

Prefijo: /ai
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ai_agent import chat_turn, get_active_conversations, plan_trip

router = APIRouter()


# ── Modelos de request/response ────────────────────────────────────────────────

class PlanTripRequest(BaseModel):
    """Request para el endpoint de planificación de viaje."""

    query: str = Field(
        ...,
        description="Query en lenguaje natural (argentino o cualquier español)",
        min_length=5,
        examples=[
            "quiero ir a la playa en familia en junio",
            "che fijate si tengo libre este finde y armame algo para desconectar",
            "mi aniversario es en 2 meses, buscame algo romántico, presupuesto no importa",
        ],
    )


class ChatRequest(BaseModel):
    """Request para el endpoint de chat con contexto."""

    message: str = Field(
        ...,
        description="Mensaje del usuario (puede referenciar respuestas anteriores)",
        min_length=2,
        examples=[
            "y si voy el sábado mejor?",
            "dale, pero hotel más barato",
            "¿qué pasa si agrego un día más?",
        ],
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID de conversación existente (None para iniciar una nueva)",
        examples=["abc123", "f7e2a1b9"],
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/plan-trip",
    summary="Planificador de viajes con IA",
    description=(
        "Endpoint principal del agente IA. Interpreta una query en lenguaje "
        "natural, consulta el calendario del usuario, sus preferencias y el "
        "historial de viajes, decide el transporte óptimo y arma una propuesta "
        "completa de viaje (vuelo + hotel + alternativas).\n\n"
        "**Ejemplos de queries:**\n"
        "- *'quiero ir a la playa en familia en junio'*\n"
        "- *'che fijate si tengo libre este finde y armame algo para desconectar'*\n"
        "- *'este viernes no tengo nada, buscame escapada con mi mujer, "
        "si es lejos que haya vuelo'*\n"
        "- *'tengo una semana libre en julio, montaña con los chicos'*\n\n"
        "**Requiere:** `GEMINI_API_KEY` configurada en el entorno."
    ),
    status_code=status.HTTP_200_OK,
)
def plan_trip_endpoint(body: PlanTripRequest) -> dict:
    """
    Agente IA de viajes: interpreta el query y retorna una propuesta estructurada.
    """
    try:
        return plan_trip(body.query)
    except ValueError as exc:
        # GEMINI_API_KEY no configurada u otro error de configuración
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el agente IA: {str(exc)}",
        )


@router.post(
    "/chat",
    summary="Chat de viajes con contexto (multi-turno)",
    description=(
        "Endpoint de chat que mantiene el contexto de la conversación entre "
        "turnos. Podés iterar sobre una propuesta previa sin repetir todo.\n\n"
        "**Flujo típico:**\n"
        "1. Usuario: *'buscame escapada este finde'* → Gemini propone Colonia\n"
        "2. Usuario: *'y si voy el sábado mejor?'* → Gemini ajusta las fechas\n"
        "3. Usuario: *'dale, pero hotel más barato'* → Gemini busca alternativas\n\n"
        "Si `conversation_id` es `null`, se inicia una nueva conversación y "
        "el ID se retorna en la respuesta para usarlo en los turnos siguientes.\n\n"
        "**Requiere:** `GEMINI_API_KEY` configurada en el entorno."
    ),
    status_code=status.HTTP_200_OK,
)
def chat_endpoint(body: ChatRequest) -> dict:
    """
    Chat multi-turno con el agente IA manteniendo contexto de conversación.
    """
    try:
        result, conv_id = chat_turn(
            message=body.message,
            conversation_id=body.conversation_id or "",
        )
        return {
            "conversation_id": conv_id,
            "response": result,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el agente IA: {str(exc)}",
        )


@router.get(
    "/status",
    summary="Estado del agente IA",
    description="Información sobre las conversaciones activas y estado del agente.",
)
def ai_status() -> dict:
    """Retorna el estado del agente y las conversaciones activas."""
    import os
    key_configured = bool(os.getenv("GEMINI_API_KEY", ""))
    convs = get_active_conversations()
    return {
        "agent": "Asistente Personal de Viajes (Gemini)",
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
        "api_key_configured": key_configured,
        "status": "listo" if key_configured else "falta GEMINI_API_KEY",
        **convs,
    }
