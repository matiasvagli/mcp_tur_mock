"""
Router del MCP SERVER (Turismo)
================================
Expone endpoints que simulan lo que el servidor MCP de Turismo
pone a disposición de los agentes IA: inventario de vuelos,
hoteles, búsqueda inteligente y descripción de herramientas.

Prefijo: /mcp
"""

from fastapi import APIRouter, Query

from data_generator import (
    generar_busqueda_inteligente,
    generar_hoteles,
    generar_tools,
    generar_vuelos,
)
from models import (
    BusquedaRequest,
    MCPToolsResponse,
    ResultadoBusqueda,
    ResultadoHoteles,
    ResultadoVuelos,
)

router = APIRouter()


@router.get(
    "/flights",
    response_model=ResultadoVuelos,
    summary="Buscar vuelos disponibles",
    description=(
        "Retorna entre 5 y 8 opciones de vuelo para la ruta y fecha indicadas. "
        "Incluye aerolínea, horarios, escalas, precios por persona y total, "
        "equipaje y puntualidad histórica. Los resultados se ordenan por precio. "
        "\n\n**Destinos soportados:** BUE, CUN, MIA, MAD, BCN, GIG, SCL, LIM, "
        "CUZ, PTY, BOG, CTG, MVD, PDP, MDQ, BRC, USH, MDZ, IGR, LAX, JFK, "
        "MCO, LAS, CDG, FCO, LHR, AMS, LIS, ATH, IST, DXB, NRT y más."
    ),
)
def search_flights(
    origin: str = Query(
        default="BUE",
        description="Código IATA o nombre del aeropuerto de origen",
        examples=["BUE", "EZE", "COR"],
    ),
    destination: str = Query(
        default="MIA",
        description="Código IATA o nombre del aeropuerto de destino",
        examples=["MIA", "CUN", "MAD"],
    ),
    date: str = Query(
        default="2026-07-15",
        description="Fecha de salida en formato YYYY-MM-DD",
        examples=["2026-07-15", "2026-12-01"],
    ),
    passengers: int = Query(
        default=2,
        ge=1,
        le=9,
        description="Cantidad de pasajeros (1-9)",
        examples=[1, 2, 4],
    ),
) -> ResultadoVuelos:
    """Genera resultados de búsqueda de vuelos aleatoriamente."""
    return generar_vuelos(origin, destination, date, passengers)


@router.get(
    "/hotels",
    response_model=ResultadoHoteles,
    summary="Buscar hoteles disponibles",
    description=(
        "Retorna entre 6 y 10 opciones de hotel para el destino y fechas indicadas. "
        "Incluye nombre, estrellas, calificación de usuarios, precio por noche y total, "
        "amenities (piscina, spa, kids club, playa privada, etc.), distancia a playa "
        "y centro. Resultados ordenados por precio. "
        "\n\n**Destinos de playa detectados automáticamente:** CUN, PUJ, FLN, PDP, "
        "MDQ, GIG, MIA, BCN (activan distancia a playa y playa privada)."
    ),
)
def search_hotels(
    destination: str = Query(
        default="CUN",
        description="Ciudad o código IATA del destino",
        examples=["CUN", "BCN", "MIA"],
    ),
    checkin: str = Query(
        default="2026-07-15",
        description="Fecha de check-in en formato YYYY-MM-DD",
        examples=["2026-07-15", "2026-08-01"],
    ),
    nights: int = Query(
        default=7,
        ge=1,
        le=30,
        description="Cantidad de noches de estadía",
        examples=[3, 7, 14],
    ),
    guests: int = Query(
        default=2,
        ge=1,
        le=8,
        description="Cantidad de huéspedes",
        examples=[1, 2, 4],
    ),
) -> ResultadoHoteles:
    """Genera resultados de búsqueda de hoteles aleatoriamente."""
    return generar_hoteles(destination, checkin, nights, guests)


@router.post(
    "/search",
    response_model=ResultadoBusqueda,
    summary="Búsqueda inteligente de paquetes",
    description=(
        "Endpoint inteligente del MCP que combina las preferencias del usuario "
        "y retorna entre 3 y 5 paquetes sugeridos (vuelo + hotel) ordenados por "
        "score de compatibilidad. Cada paquete incluye razones de recomendación, "
        "ahorro vs. compra separada y tags de clasificación. "
        "\n\n**Ideal para:** agentes IA que quieren obtener opciones personalizadas "
        "en una sola llamada."
    ),
)
def smart_search(body: BusquedaRequest) -> ResultadoBusqueda:
    """Motor de búsqueda inteligente basado en preferencias del usuario."""
    return generar_busqueda_inteligente(body)


@router.get(
    "/tools",
    response_model=MCPToolsResponse,
    summary="Herramientas disponibles del MCP server",
    description=(
        "Retorna la descripción de todas las herramientas (tools) que expone "
        "el servidor MCP de Turismo, siguiendo el formato del protocolo MCP. "
        "Incluye nombre, descripción, parámetros, tipo de retorno y ejemplos. "
        "\n\n**Equivalente al endpoint `tools/list` del protocolo MCP estándar.**"
    ),
)
def get_tools() -> MCPToolsResponse:
    """Retorna el listado de herramientas MCP disponibles con su documentación."""
    return generar_tools()
