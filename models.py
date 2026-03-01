"""
Modelos Pydantic para la API Turismo MCP Mock
=============================================
Contiene todos los esquemas de datos usados en los routers
de usuario y del servidor MCP.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Enumeraciones ─────────────────────────────────────────────────────────────

class TipoViaje(str, Enum):
    playa = "playa"
    ciudad = "ciudad"
    montana = "montaña"
    aventura = "aventura"
    cultural = "cultural"


class EstiloViaje(str, Enum):
    familia = "familia"
    pareja = "pareja"
    solo = "solo"
    amigos = "amigos"


class Presupuesto(str, Enum):
    economico = "económico"
    moderado = "moderado"
    premium = "premium"
    lujo = "lujo"


class TipoEvento(str, Enum):
    reunion = "reunión"
    cumpleanos = "cumpleaños"
    feriado = "feriado"
    bloqueado = "bloqueado"
    compromiso = "compromiso personal"


# ── Modelos de Usuario ────────────────────────────────────────────────────────

class PreferenciasUsuario(BaseModel):
    """Preferencias de viaje personalizadas del usuario."""

    tipo_viaje: TipoViaje = Field(..., description="Tipo de destino preferido")
    estilo: EstiloViaje = Field(..., description="Con quién suele viajar")
    presupuesto: Presupuesto = Field(..., description="Rango de presupuesto habitual")
    duracion_preferida_dias: int = Field(..., ge=1, le=30, description="Duración ideal del viaje en días")
    destinos_favoritos: List[str] = Field(..., description="Países o ciudades visitados con alta puntuación")
    asiento_preferido: str = Field(..., description="Ventana o pasillo")
    clase_vuelo: str = Field(..., description="Económica, executiva, primera")
    requiere_accesibilidad: bool = Field(False, description="Necesidades de accesibilidad")
    idiomas: List[str] = Field(..., description="Idiomas que habla el usuario")
    notificaciones_oferta: bool = Field(True, description="Desea recibir alertas de ofertas")


class EventoCalendario(BaseModel):
    """Evento en el calendario personal del usuario."""

    id: str
    titulo: str
    tipo: TipoEvento
    fecha_inicio: str = Field(..., description="YYYY-MM-DD")
    fecha_fin: str = Field(..., description="YYYY-MM-DD")
    dia_completo: bool = True
    bloquea_viaje: bool = Field(..., description="Si este evento impide viajar")
    descripcion: Optional[str] = None


class CalendarioMes(BaseModel):
    """Calendario del mes con eventos y ventanas libres."""

    mes: str = Field(..., description="YYYY-MM")
    eventos: List[EventoCalendario]
    ventanas_libres: List[str] = Field(..., description="Rangos de fechas libres para viajar (YYYY-MM-DD / YYYY-MM-DD)")
    mejor_semana_para_viajar: Optional[str] = None


class ViajeHistorial(BaseModel):
    """Registro de un viaje pasado del usuario."""

    id: str
    destino: str
    pais: str
    fecha_ida: str
    fecha_vuelta: str
    duracion_dias: int
    aerolinea_usada: str
    hotel: str
    estrellas_hotel: int
    precio_total_usd: float
    rating_usuario: float = Field(..., ge=1.0, le=5.0, description="Puntuación del 1 al 5")
    comentario: Optional[str] = None
    fotos: List[str] = Field(..., description="URLs de fotos (simuladas)")
    repetiria: bool


class HistorialViajes(BaseModel):
    """Historial completo de viajes del usuario."""

    usuario_id: str
    total_viajes: int
    paises_visitados: List[str]
    viajes: List[ViajeHistorial]


# ── Modelos MCP: Vuelos ───────────────────────────────────────────────────────

class Vuelo(BaseModel):
    """Vuelo disponible del inventario del MCP server."""

    id: str
    aerolinea: str
    codigo_vuelo: str
    origen: str
    destino: str
    fecha_salida: str = Field(..., description="YYYY-MM-DD")
    hora_salida: str = Field(..., description="HH:MM")
    hora_llegada: str = Field(..., description="HH:MM")
    duracion_minutos: int
    escalas: int
    ciudades_escala: List[str]
    precio_por_persona_usd: float
    precio_total_usd: float
    clase: str
    equipaje_incluido: bool
    cancelacion_gratuita: bool
    asientos_disponibles: int
    puntualidad_porcentaje: int = Field(..., ge=0, le=100)


class ResultadoVuelos(BaseModel):
    """Resultado de la búsqueda de vuelos en el MCP."""

    origen: str
    destino: str
    fecha: str
    pasajeros: int
    total_resultados: int
    vuelos: List[Vuelo]
    filtros_sugeridos: dict


# ── Modelos MCP: Hoteles ──────────────────────────────────────────────────────

class Amenity(str, Enum):
    piscina = "piscina"
    spa = "spa"
    gym = "gimnasio"
    restaurante = "restaurante"
    bar = "bar"
    wifi = "wifi gratuito"
    estacionamiento = "estacionamiento"
    kids_club = "kids club"
    playa_privada = "playa privada"
    transfers = "transfers incluidos"
    todo_incluido = "todo incluido"
    pet_friendly = "pet friendly"
    rooftop = "rooftop bar"
    casino = "casino"
    business_center = "business center"


class Hotel(BaseModel):
    """Hotel disponible en el inventario del MCP server."""

    id: str
    nombre: str
    cadena: Optional[str] = None
    destino: str
    pais: str
    estrellas: int = Field(..., ge=1, le=5)
    calificacion_usuarios: float = Field(..., ge=1.0, le=10.0)
    total_reviews: int
    precio_por_noche_usd: float
    precio_total_usd: float
    noches: int
    amenities: List[str]
    distancia_playa_metros: Optional[int] = None
    distancia_centro_metros: int
    desayuno_incluido: bool
    tipo_habitacion: str
    capacidad_max: int
    kid_friendly: bool
    descripcion: str
    cancelacion_gratuita: bool
    imagenes: List[str] = Field(..., description="URLs de imágenes (simuladas)")


class ResultadoHoteles(BaseModel):
    """Resultado de la búsqueda de hoteles en el MCP."""

    destino: str
    checkin: str
    checkout: str
    noches: int
    huespedes: int
    total_resultados: int
    hoteles: List[Hotel]
    precio_promedio_usd: float


# ── Modelos MCP: Búsqueda Inteligente ────────────────────────────────────────

class BusquedaRequest(BaseModel):
    """Cuerpo de la solicitud al endpoint inteligente /mcp/search."""

    tipo_viaje: Optional[TipoViaje] = TipoViaje.playa
    estilo: Optional[EstiloViaje] = EstiloViaje.pareja
    presupuesto: Optional[Presupuesto] = Presupuesto.moderado
    duracion_dias: Optional[int] = Field(7, ge=1, le=30)
    origen: Optional[str] = "BUE"
    pasajeros: Optional[int] = Field(2, ge=1, le=9)
    mes_preferido: Optional[str] = Field(None, description="YYYY-MM, si es None usa próximo mes")
    destinos_excluidos: Optional[List[str]] = []
    requiere_directo: Optional[bool] = False


class PaqueteSugerido(BaseModel):
    """Paquete de viaje completo sugerido por el motor inteligente del MCP."""

    id: str
    nombre_paquete: str
    descripcion: str
    score_match: float = Field(..., ge=0.0, le=1.0, description="Qué tan bien coincide con las preferencias")
    destino: str
    pais: str
    fecha_salida_sugerida: str
    fecha_regreso_sugerida: str
    duracion_dias: int
    vuelo_ida: Vuelo
    vuelo_vuelta: Vuelo
    hotel: Hotel
    precio_total_paquete_usd: float
    ahorro_vs_separado_usd: float
    por_que_te_recomendamos: List[str]
    tags: List[str]


class ResultadoBusqueda(BaseModel):
    """Respuesta completa del endpoint de búsqueda inteligente."""

    request_id: str
    preferencias_aplicadas: BusquedaRequest
    total_paquetes: int
    paquetes: List[PaqueteSugerido]
    mensaje_ia: str


# ── Modelos MCP: Tools ────────────────────────────────────────────────────────

class MCPToolParameter(BaseModel):
    """Parámetro de una herramienta MCP."""

    name: str
    type: str
    description: str
    required: bool
    example: Optional[str] = None


class MCPTool(BaseModel):
    """Descripción de una herramienta expuesta por el servidor MCP."""

    name: str
    description: str
    category: str
    parameters: List[MCPToolParameter]
    returns: str
    example_call: dict


class MCPToolsResponse(BaseModel):
    """Respuesta del endpoint /mcp/tools con todas las herramientas disponibles."""

    server_name: str
    server_version: str
    protocol: str
    total_tools: int
    tools: List[MCPTool]
