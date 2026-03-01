"""
Router de datos del USUARIO
===========================
Expone endpoints que simulan lo que una IA personal
ya sabe del usuario (preferencias, calendario, historial).

Prefijo: /user
"""

from fastapi import APIRouter, Query

from data_generator import generar_calendario, generar_historial, generar_preferencias
from models import CalendarioMes, HistorialViajes, PreferenciasUsuario

router = APIRouter()


@router.get(
    "/preferences",
    response_model=PreferenciasUsuario,
    summary="Preferencias del usuario",
    description=(
        "Retorna las preferencias de viaje personalizadas del usuario: "
        "tipo de destino favorito, estilo de viaje, presupuesto habitual, "
        "idiomas, clase de vuelo, etc. Los datos son generados aleatoriamente "
        "en cada request para simular distintos perfiles de usuario."
    ),
)
def get_preferences() -> PreferenciasUsuario:
    """Genera y retorna preferencias de viaje aleatorias del usuario."""
    return generar_preferencias()


@router.get(
    "/calendar",
    response_model=CalendarioMes,
    summary="Calendario mensual del usuario",
    description=(
        "Retorna entre 3 y 5 eventos del mes indicado (reuniones, cumpleaños, "
        "feriados, compromisos personales) junto con las ventanas de fechas libres "
        "para viajar. Parámetro `month` en formato YYYY-MM."
    ),
)
def get_calendar(
    month: str = Query(
        default="2026-07",
        description="Mes a consultar en formato YYYY-MM",
        examples=["2026-07", "2026-12"],
        pattern=r"^\d{4}-\d{2}$",
    ),
) -> CalendarioMes:
    """Genera el calendario del mes con eventos random y ventanas libres."""
    return generar_calendario(month)


@router.get(
    "/travel-history",
    response_model=HistorialViajes,
    summary="Historial de viajes del usuario",
    description=(
        "Retorna entre 2 y 3 viajes realizados por el usuario en los últimos "
        "24 meses. Incluye destino, aerolínea, hotel, precio pagado, rating y "
        "fotos (URLs simuladas de Unsplash)."
    ),
)
def get_travel_history() -> HistorialViajes:
    """Genera un historial de viajes pasados de forma aleatoria."""
    return generar_historial()
