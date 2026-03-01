"""
Generador de Modelos Pydantic para la API Turismo MCP Mock
===========================================================
Centraliza toda la lógica de generación de datos random para
mantener los routers limpios y enfocados en HTTP.

IMPORTANTE: Cada función hace random.seed(time.time_ns()) al inicio
para garantizar variedad en cada request.
"""

from __future__ import annotations

import math
import random
import time
import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from models import (
    Amenity,
    BusquedaRequest,
    CalendarioMes,
    EstiloViaje,
    EventoCalendario,
    HistorialViajes,
    Hotel,
    MCPTool,
    MCPToolParameter,
    MCPToolsResponse,
    PaqueteSugerido,
    PreferenciasUsuario,
    Presupuesto,
    ResultadoBusqueda,
    ResultadoHoteles,
    ResultadoVuelos,
    TipoEvento,
    TipoViaje,
    ViajeHistorial,
    Vuelo,
)

# ── Datos de referencia ────────────────────────────────────────────────────────

AEROLINEAS = [
    "Aerolíneas Argentinas", "LATAM", "Avianca", "Copa Airlines",
    "American Airlines", "United Airlines", "Air Europa", "Iberia",
    "Air France", "KLM", "Emirates", "Turkish Airlines", "JetBlue",
    "Flybondi", "Jetsmart",
]

DESTINOS = {
    "argentina": [
        ("Bariloche", "Argentina", "BRC"),
        ("Mendoza", "Argentina", "MDZ"),
        ("Ushuaia", "Argentina", "USH"),
        ("Mar del Plata", "Argentina", "MDQ"),
        ("Salta", "Argentina", "SLA"),
        ("Iguazú", "Argentina", "IGR"),
        ("Córdoba", "Argentina", "COR"),
    ],
    "latinoamerica": [
        ("Cancún", "México", "CUN"),
        ("Ciudad de México", "México", "MEX"),
        ("Punta Cana", "República Dominicana", "PUJ"),
        ("Cartagena", "Colombia", "CTG"),
        ("Bogotá", "Colombia", "BOG"),
        ("Lima", "Perú", "LIM"),
        ("Cusco", "Perú", "CUZ"),
        ("Santiago", "Chile", "SCL"),
        ("Río de Janeiro", "Brasil", "GIG"),
        ("São Paulo", "Brasil", "GRU"),
        ("Florianópolis", "Brasil", "FLN"),
        ("Montevideo", "Uruguay", "MVD"),
        ("Punta del Este", "Uruguay", "PDP"),
        ("La Habana", "Cuba", "HAV"),
        ("Cartagena de Indias", "Colombia", "CTG"),
        ("Quito", "Ecuador", "UIO"),
        ("Galápagos", "Ecuador", "GPS"),
        ("Asunción", "Paraguay", "ASU"),
        ("Caracas", "Venezuela", "CCS"),
        ("Panamá City", "Panamá", "PTY"),
    ],
    "usa": [
        ("Miami", "EE.UU.", "MIA"),
        ("Nueva York", "EE.UU.", "JFK"),
        ("Los Ángeles", "EE.UU.", "LAX"),
        ("Orlando", "EE.UU.", "MCO"),
        ("Las Vegas", "EE.UU.", "LAS"),
        ("Chicago", "EE.UU.", "ORD"),
        ("San Francisco", "EE.UU.", "SFO"),
        ("Washington D.C.", "EE.UU.", "DCA"),
    ],
    "europa": [
        ("Madrid", "España", "MAD"),
        ("Barcelona", "España", "BCN"),
        ("París", "Francia", "CDG"),
        ("Roma", "Italia", "FCO"),
        ("Milán", "Italia", "MXP"),
        ("Londres", "Reino Unido", "LHR"),
        ("Ámsterdam", "Países Bajos", "AMS"),
        ("Lisboa", "Portugal", "LIS"),
        ("Berlín", "Alemania", "BER"),
        ("Dublín", "Irlanda", "DUB"),
        ("Atenas", "Grecia", "ATH"),
        ("Estambul", "Turquía", "IST"),
        ("Dubái", "Emiratos Árabes", "DXB"),
        ("Tokio", "Japón", "NRT"),
    ],
}

ALL_DESTINOS = [d for lista in DESTINOS.values() for d in lista]

HOTELES_NOMBRES = [
    "Grand Hyatt", "Marriott Resort", "Hilton Garden Inn",
    "Four Seasons", "Sofitel", "Sheraton", "W Hotels",
    "Barceló Premium", "Hard Rock Hotel", "Iberostar Selection",
    "Meliá Resort", "NH Collection", "Radisson Blu",
    "InterContinental", "Crowne Plaza", "Hotel Boutique",
    "The Ritz-Carlton", "Le Meridien", "Westin", "St. Regis",
    "Fairmont", "Waldorf Astoria", "Conrad", "Mondrian",
]

CADENAS = [
    "Hyatt", "Marriott", "Hilton", "IHG", "Accor",
    "Meliá Hotels", "NH Hotels", "Barceló Hotels", None, None,
]

TIPOS_HABITACION = [
    "Habitación Estándar", "Habitación Superior", "Suite Junior",
    "Suite Deluxe", "Suite con Vista al Mar", "Penthouse Suite",
    "Habitación Familiar", "Bungalow", "Villa Privada",
]

FOTOS_BASE = [
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e",
    "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4",
    "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb",
    "https://images.unsplash.com/photo-1571896349842-33c89424de2d",
    "https://images.unsplash.com/photo-1566073771259-6a8506099945",
    "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa",
    "https://images.unsplash.com/photo-1445019980597-93fa8acb246c",
    "https://images.unsplash.com/photo-1496417263034-38ec4f0b665a",
    "https://images.unsplash.com/photo-1509610973389-f5a5785e0d04",
    "https://images.unsplash.com/photo-1560347876-aeef00ee58a1",
]

COMENTARIOS_POSITIVOS = [
    "Excelente experiencia, lo repetiría sin dudarlo.",
    "El hotel superó mis expectativas, vista increíble.",
    "Vuelo puntual y servicio de primera. Muy satisfecho.",
    "Destino hermoso, ideal para desconectarse.",
    "La relación calidad-precio fue muy buena.",
    "Viaje perfecto, todo salió como estaba planificado.",
    "Increíble gastronomía local y trato cálido.",
]

COMENTARIOS_NEUTROS = [
    "Buen viaje en general, aunque el hotel podría mejorar.",
    "El vuelo tuvo una pequeña demora, pero nada grave.",
    "Destino lindo, quizás volvería en otra época del año.",
    "Experiencia correcta, cumplió expectativas básicas.",
]


# ── Helpers internos ──────────────────────────────────────────────────────────

def _seed() -> None:
    """Reinicia la semilla random en base al timestamp en nanosegundos."""
    random.seed(time.time_ns())


def _uid() -> str:
    return str(uuid.uuid4())[:8].upper()


def _precio_vuelo(base: float, escalas: int, clase: str) -> float:
    """Calcula precio de vuelo con lógica realista."""
    mult_clase = {"Económica": 1.0, "Ejecutiva": 3.2, "Primera": 5.5}
    mult_escala = 1.0 if escalas == 0 else (0.85 if escalas == 1 else 0.72)
    precio = base * mult_clase.get(clase, 1.0) * mult_escala
    precio += random.uniform(-30, 80)
    return round(max(50, precio), 2)


def _hora_aleatoria(hora_min: int = 5, hora_max: int = 23) -> str:
    h = random.randint(hora_min, hora_max)
    m = random.choice([0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    return f"{h:02d}:{m:02d}"


def _sumar_minutos(hora: str, minutos: int) -> str:
    h, m = map(int, hora.split(":"))
    total_m = h * 60 + m + minutos
    total_m = total_m % (24 * 60)
    return f"{total_m // 60:02d}:{total_m % 60:02d}"


def _fechas_ventanas_libres(
    eventos: list[EventoCalendario], anio: int, mes: int
) -> Tuple[List[str], Optional[str]]:
    """Calcula las ventanas libres del mes dado los eventos bloqueantes."""
    _, ultimo_dia = _ultimo_dia_mes(anio, mes)
    dias_bloqueados: set[date] = set()

    for ev in eventos:
        if ev.bloquea_viaje:
            inicio = date.fromisoformat(ev.fecha_inicio)
            fin = date.fromisoformat(ev.fecha_fin)
            d = inicio
            while d <= fin:
                dias_bloqueados.add(d)
                d += timedelta(days=1)

    ventanas = []
    inicio_ventana: Optional[date] = None

    for dia in range(1, ultimo_dia + 1):
        d = date(anio, mes, dia)
        if d not in dias_bloqueados:
            if inicio_ventana is None:
                inicio_ventana = d
        else:
            if inicio_ventana is not None:
                fin_ventana = date(anio, mes, dia - 1)
                if (fin_ventana - inicio_ventana).days >= 2:
                    ventanas.append(f"{inicio_ventana} / {fin_ventana}")
                inicio_ventana = None

    if inicio_ventana is not None:
        fin_ventana = date(anio, mes, ultimo_dia)
        if (fin_ventana - inicio_ventana).days >= 2:
            ventanas.append(f"{inicio_ventana} / {fin_ventana}")

    mejor = max(ventanas, key=lambda v: (
        date.fromisoformat(v.split(" / ")[1]) - date.fromisoformat(v.split(" / ")[0])
    ), default=None)

    return ventanas, mejor


def _ultimo_dia_mes(anio: int, mes: int) -> Tuple[int, int]:
    if mes == 12:
        sig = date(anio + 1, 1, 1)
    else:
        sig = date(anio, mes + 1, 1)
    ultimo = (sig - timedelta(days=1)).day
    return anio, ultimo


# ── Generadores principales ───────────────────────────────────────────────────

def generar_preferencias() -> PreferenciasUsuario:
    """Genera preferencias de usuario completamente aleatorias."""
    _seed()
    destinos_fav_pool = [d[0] for d in random.sample(ALL_DESTINOS, 8)]
    return PreferenciasUsuario(
        tipo_viaje=random.choice(list(TipoViaje)),
        estilo=random.choice(list(EstiloViaje)),
        presupuesto=random.choice(list(Presupuesto)),
        duracion_preferida_dias=random.choice([3, 5, 7, 10, 14, 21]),
        destinos_favoritos=random.sample(destinos_fav_pool, k=random.randint(2, 5)),
        asiento_preferido=random.choice(["Ventana", "Pasillo"]),
        clase_vuelo=random.choice(["Económica", "Ejecutiva"]),
        requiere_accesibilidad=random.random() < 0.1,
        idiomas=random.sample(["Español", "Inglés", "Portugués", "Francés", "Italiano"], k=random.randint(1, 3)),
        notificaciones_oferta=random.random() < 0.8,
    )


def generar_calendario(mes_str: str) -> CalendarioMes:
    """Genera un calendario mensual con 3-5 eventos aleatorios."""
    _seed()
    anio, mes = map(int, mes_str.split("-"))
    _, ultimo_dia = _ultimo_dia_mes(anio, mes)

    n_eventos = random.randint(3, 5)
    eventos: List[EventoCalendario] = []
    dias_usados: set[int] = set()

    tipos_evento = list(TipoEvento)

    for i in range(n_eventos):
        # Buscar día libre
        for _ in range(50):
            dia_ini = random.randint(1, ultimo_dia - 1)
            if dia_ini not in dias_usados:
                break

        tipo = random.choice(tipos_evento)
        duracion = 1 if tipo in (TipoEvento.cumpleanos, TipoEvento.reunion) else random.randint(1, 3)
        dia_fin = min(dia_ini + duracion - 1, ultimo_dia)

        for d in range(dia_ini, dia_fin + 1):
            dias_usados.add(d)

        fecha_ini = date(anio, mes, dia_ini).isoformat()
        fecha_fin = date(anio, mes, dia_fin).isoformat()

        titulo_map = {
            TipoEvento.reunion: random.choice(["Reunión de equipo", "Presentación cliente", "Workshop", "Sprint review"]),
            TipoEvento.cumpleanos: random.choice(["Cumpleaños familiar", "Cumpleaños amigo", "Aniversario"]),
            TipoEvento.feriado: random.choice(["Feriado nacional", "Día no laborable"]),
            TipoEvento.bloqueado: random.choice(["Trámite personal", "Cita médica", "Mudanza"]),
            TipoEvento.compromiso: random.choice(["Casamiento", "Baby shower", "Graduación", "Evento social"]),
        }

        eventos.append(EventoCalendario(
            id=f"EVT-{_uid()}",
            titulo=titulo_map[tipo],
            tipo=tipo,
            fecha_inicio=fecha_ini,
            fecha_fin=fecha_fin,
            dia_completo=True,
            bloquea_viaje=tipo in (TipoEvento.reunion, TipoEvento.bloqueado, TipoEvento.compromiso),
        ))

    ventanas, mejor = _fechas_ventanas_libres(eventos, anio, mes)

    return CalendarioMes(
        mes=mes_str,
        eventos=eventos,
        ventanas_libres=ventanas,
        mejor_semana_para_viajar=mejor,
    )


def generar_historial() -> HistorialViajes:
    """Genera el historial de 2-3 viajes pasados del usuario."""
    _seed()
    n_viajes = random.randint(2, 3)
    viajes: List[ViajeHistorial] = []
    paises: List[str] = []

    # Fechas en el pasado (últimos 24 meses)
    hoy = date.today()

    for i in range(n_viajes):
        destino_data = random.choice(ALL_DESTINOS)
        nombre_dest, pais, _ = destino_data
        paises.append(pais)

        dias_atras = random.randint(30, 730)
        fecha_ida = hoy - timedelta(days=dias_atras)
        duracion = random.randint(4, 14)
        fecha_vuelta = fecha_ida + timedelta(days=duracion)

        precio_base = random.uniform(800, 4500)
        rating = round(random.uniform(3.0, 5.0), 1)
        comentario_pool = COMENTARIOS_POSITIVOS if rating >= 4.0 else COMENTARIOS_NEUTROS

        viajes.append(ViajeHistorial(
            id=f"TRIP-{_uid()}",
            destino=nombre_dest,
            pais=pais,
            fecha_ida=fecha_ida.isoformat(),
            fecha_vuelta=fecha_vuelta.isoformat(),
            duracion_dias=duracion,
            aerolinea_usada=random.choice(AEROLINEAS),
            hotel=f"{random.choice(HOTELES_NOMBRES)} {nombre_dest}",
            estrellas_hotel=random.randint(3, 5),
            precio_total_usd=round(precio_base, 2),
            rating_usuario=rating,
            comentario=random.choice(comentario_pool),
            fotos=[
                f"{random.choice(FOTOS_BASE)}?w=800&q=80&sig={random.randint(1,999)}",
                f"{random.choice(FOTOS_BASE)}?w=800&q=80&sig={random.randint(1,999)}",
                f"{random.choice(FOTOS_BASE)}?w=800&q=80&sig={random.randint(1,999)}",
            ],
            repetiria=rating >= 4.0,
        ))

    return HistorialViajes(
        usuario_id=f"USR-{_uid()}",
        total_viajes=n_viajes,
        paises_visitados=list(set(paises)),
        viajes=viajes,
    )


def _generar_vuelo(
    origen: str,
    destino_data: Tuple[str, str, str],
    fecha: str,
    pasajeros: int,
    clase: str = "Económica",
    forzar_directo: bool = False,
) -> Vuelo:
    """Genera un vuelo individual aleatorio."""
    nombre_dest, _, codigo_dest = destino_data
    aerolinea = random.choice(AEROLINEAS)
    escalas = 0 if forzar_directo else random.choices([0, 1, 2], weights=[0.4, 0.45, 0.15])[0]
    ciudades_esc = []
    if escalas > 0:
        hubs = ["Bogotá", "Lima", "São Paulo", "Madrid", "Miami", "Ciudad de México", "Santiago"]
        ciudades_esc = random.sample(hubs, escalas)

    duracion = random.randint(90, 900)  # minutos
    duracion += escalas * random.randint(60, 150)

    hora_sal = _hora_aleatoria()
    hora_lleg = _sumar_minutos(hora_sal, duracion)
    codigo = f"{aerolinea[:2].upper()}{random.randint(100, 9999)}"
    precio_base = random.uniform(120, 1800)
    precio_unit = _precio_vuelo(precio_base, escalas, clase)

    return Vuelo(
        id=f"FLT-{_uid()}",
        aerolinea=aerolinea,
        codigo_vuelo=codigo,
        origen=origen,
        destino=codigo_dest,
        fecha_salida=fecha,
        hora_salida=hora_sal,
        hora_llegada=hora_lleg,
        duracion_minutos=duracion,
        escalas=escalas,
        ciudades_escala=ciudades_esc,
        precio_por_persona_usd=precio_unit,
        precio_total_usd=round(precio_unit * pasajeros, 2),
        clase=clase,
        equipaje_incluido=random.random() < 0.6,
        cancelacion_gratuita=random.random() < 0.4,
        asientos_disponibles=random.randint(1, 40),
        puntualidad_porcentaje=random.randint(72, 98),
    )


def generar_vuelos(
    origin: str,
    destination: str,
    fecha: str,
    pasajeros: int,
) -> ResultadoVuelos:
    """Genera 5-8 resultados de vuelos para la búsqueda dada."""
    _seed()

    # Intentar encontrar destino en la tabla
    destino_data: Tuple[str, str, str] = (destination, "Internacional", destination)
    for d in ALL_DESTINOS:
        if d[2].upper() == destination.upper() or d[0].lower() == destination.lower():
            destino_data = d
            break

    n = random.randint(5, 8)
    clases = random.choices(
        ["Económica", "Económica", "Económica", "Ejecutiva", "Primera"],
        weights=[40, 35, 15, 8, 2],
        k=n,
    )
    vuelos = [
        _generar_vuelo(origin.upper(), destino_data, fecha, pasajeros, c)
        for c in clases
    ]
    # Ordenar por precio ascendente
    vuelos.sort(key=lambda v: v.precio_total_usd)

    return ResultadoVuelos(
        origen=origin.upper(),
        destino=destination.upper(),
        fecha=fecha,
        pasajeros=pasajeros,
        total_resultados=len(vuelos),
        vuelos=vuelos,
        filtros_sugeridos={
            "precio_min": vuelos[0].precio_total_usd,
            "precio_max": vuelos[-1].precio_total_usd,
            "vuelos_directos": sum(1 for v in vuelos if v.escalas == 0),
            "clases_disponibles": list({v.clase for v in vuelos}),
            "aerolineas": list({v.aerolinea for v in vuelos}),
        },
    )


def _generar_hotel(
    destino_data: Tuple[str, str, str],
    checkin: str,
    noches: int,
    huespedes: int,
    es_playa: bool = False,
    kid_friendly: bool = False,
) -> Hotel:
    """Genera un hotel individual aleatorio."""
    nombre_dest, pais, _ = destino_data
    estrellas = random.choices([3, 4, 5], weights=[30, 45, 25])[0]
    precio_noche = random.uniform(
        60 if estrellas == 3 else (150 if estrellas == 4 else 350),
        200 if estrellas == 3 else (400 if estrellas == 4 else 1200),
    )
    if es_playa:
        precio_noche *= random.uniform(1.1, 1.4)

    amenities_pool = list(Amenity)
    required = [Amenity.wifi]
    if es_playa:
        required.append(Amenity.playa_privada)
    if kid_friendly:
        required.append(Amenity.kids_club)
    extra = random.sample(
        [a for a in amenities_pool if a not in required],
        k=random.randint(3, 7),
    )
    amenities = list({a.value for a in required + extra})

    checkout = (date.fromisoformat(checkin) + timedelta(days=noches)).isoformat()

    return Hotel(
        id=f"HTL-{_uid()}",
        nombre=f"{random.choice(HOTELES_NOMBRES)} {nombre_dest}",
        cadena=random.choice(CADENAS),
        destino=nombre_dest,
        pais=pais,
        estrellas=estrellas,
        calificacion_usuarios=round(random.uniform(6.5, 9.8), 1),
        total_reviews=random.randint(200, 8000),
        precio_por_noche_usd=round(precio_noche, 2),
        precio_total_usd=round(precio_noche * noches, 2),
        noches=noches,
        amenities=amenities,
        distancia_playa_metros=random.randint(0, 500) if es_playa else None,
        distancia_centro_metros=random.randint(100, 5000),
        desayuno_incluido=random.random() < 0.5,
        tipo_habitacion=random.choice(TIPOS_HABITACION),
        capacidad_max=random.choice([2, 2, 2, 3, 4, 4]),
        kid_friendly=kid_friendly or random.random() < 0.3,
        descripcion=f"Hotel {estrellas}★ en {nombre_dest}. Ideal para {'familias' if kid_friendly else 'parejas'} y {'amantes de la playa' if es_playa else 'viajeros urbanos'}.",
        cancelacion_gratuita=random.random() < 0.55,
        imagenes=[
            f"{random.choice(FOTOS_BASE)}?w=800&q=80&hotel={i}&sig={random.randint(1,999)}"
            for i in range(3)
        ],
    )


def generar_hoteles(
    destination: str,
    checkin: str,
    noches: int,
    huespedes: int,
) -> ResultadoHoteles:
    """Genera 6-10 hoteles para la búsqueda dada."""
    _seed()

    destino_data: Tuple[str, str, str] = (destination, "Internacional", destination)
    es_playa = False
    for d in ALL_DESTINOS:
        if d[2].upper() == destination.upper() or d[0].lower() == destination.lower():
            destino_data = d
            break

    # Determinar si es destino de playa
    destinos_playa = {"CUN", "PUJ", "FLN", "PDP", "MDQ", "GIG", "MIA", "BCN"}
    es_playa = destino_data[2].upper() in destinos_playa

    kid_friendly_prob = random.random() < 0.35

    n = random.randint(6, 10)
    hoteles = [
        _generar_hotel(destino_data, checkin, noches, huespedes, es_playa, kid_friendly_prob)
        for _ in range(n)
    ]
    hoteles.sort(key=lambda h: h.precio_total_usd)

    precios = [h.precio_por_noche_usd for h in hoteles]
    return ResultadoHoteles(
        destino=destination,
        checkin=checkin,
        checkout=(date.fromisoformat(checkin) + timedelta(days=noches)).isoformat(),
        noches=noches,
        huespedes=huespedes,
        total_resultados=len(hoteles),
        hoteles=hoteles,
        precio_promedio_usd=round(sum(precios) / len(precios), 2),
    )


def generar_busqueda_inteligente(req: BusquedaRequest) -> ResultadoBusqueda:
    """
    Motor inteligente: combina preferencias del usuario y genera
    paquetes de viaje sugeridos con score de match.
    """
    _seed()

    # Definir destinos candidatos según tipo de viaje
    if req.tipo_viaje == TipoViaje.playa:
        candidatos = [d for d in ALL_DESTINOS if d[2] in {"CUN", "PUJ", "FLN", "PDP", "MDQ", "GIG", "MIA"}]
    elif req.tipo_viaje == TipoViaje.montana:
        candidatos = [d for d in ALL_DESTINOS if d[0] in {"Bariloche", "Ushuaia", "Cusco", "Mendoza", "Salta"}]
    elif req.tipo_viaje == TipoViaje.cultural:
        candidatos = [d for d in ALL_DESTINOS if d[0] in {"Roma", "París", "Madrid", "Barcelona", "Lisboa", "Atenas", "Estambul"}]
    elif req.tipo_viaje == TipoViaje.ciudad:
        candidatos = [d for d in ALL_DESTINOS if d[0] in {"Nueva York", "Miami", "Madrid", "Barcelona", "Buenos Aires", "São Paulo", "Ciudad de México"}]
    else:
        candidatos = ALL_DESTINOS

    # Excluir destinos no deseados
    candidatos = [d for d in candidatos if d[0] not in (req.destinos_excluidos or [])]
    if not candidatos:
        candidatos = ALL_DESTINOS

    # Duración según presupuesto y tipo
    if req.presupuesto in (Presupuesto.economico, Presupuesto.moderado) and req.duracion_dias and req.duracion_dias <= 4:
        tipo_paquete = "escapada"
    else:
        tipo_paquete = "vacaciones"

    # Calcular fecha de salida
    if req.mes_preferido:
        anio, mes = map(int, req.mes_preferido.split("-"))
        dia_sal = random.randint(1, 28)
        fecha_salida = date(anio, mes, dia_sal)
    else:
        fecha_salida = date.today() + timedelta(days=random.randint(14, 90))

    duracion = req.duracion_dias or random.randint(4, 10)
    fecha_regreso = fecha_salida + timedelta(days=duracion)

    n_paquetes = random.randint(3, 5)
    paquetes: List[PaqueteSugerido] = []

    destinos_elegidos = random.sample(candidatos, k=min(n_paquetes, len(candidatos)))

    for dest_data in destinos_elegidos:
        nombre_dest, pais, codigo = dest_data
        pasajeros = req.pasajeros or 2
        origen = req.origen or "BUE"
        fecha_s = fecha_salida.isoformat()
        fecha_r = fecha_regreso.isoformat()

        # Generar vuelos
        clase = "Ejecutiva" if req.presupuesto == Presupuesto.lujo else "Económica"
        forzar_directo = req.requiere_directo or req.estilo == EstiloViaje.familia
        vuelo_ida = _generar_vuelo(origen, dest_data, fecha_s, pasajeros, clase, forzar_directo)
        vuelo_vuelta = _generar_vuelo(codigo, (origen, "Argentina", origen), fecha_r, pasajeros, clase, forzar_directo)

        # Generar hotel
        es_playa = req.tipo_viaje == TipoViaje.playa
        kid_f = req.estilo == EstiloViaje.familia
        hotel = _generar_hotel(dest_data, fecha_s, duracion, pasajeros, es_playa, kid_f)

        precio_paquete = vuelo_ida.precio_total_usd + vuelo_vuelta.precio_total_usd + hotel.precio_total_usd
        ahorro = round(precio_paquete * random.uniform(0.05, 0.18), 2)

        # Calcular score de match
        score = round(random.uniform(0.72, 0.98), 2)

        razones = []
        if req.tipo_viaje == TipoViaje.playa and es_playa:
            razones.append(f"Destino de playa con {hotel.distancia_playa_metros or 200}m al mar")
        if kid_f and hotel.kid_friendly:
            razones.append("Hotel con Kids Club y actividades para niños")
        if req.requiere_directo and vuelo_ida.escalas == 0:
            razones.append("Vuelo directo disponible")
        if hotel.cancelacion_gratuita:
            razones.append("Cancelación gratuita hasta 48hs antes")
        razones.append(f"Precio dentro de tu presupuesto {req.presupuesto}")
        razones.append(f"Duración ideal de {duracion} días para un viaje en {tipo_paquete}")

        tags = [req.tipo_viaje.value, req.estilo.value, tipo_paquete, pais.lower()]
        if hotel.desayuno_incluido:
            tags.append("desayuno incluido")
        if vuelo_ida.cancelacion_gratuita:
            tags.append("cancelable")

        paquetes.append(PaqueteSugerido(
            id=f"PKG-{_uid()}",
            nombre_paquete=f"{tipo_paquete.capitalize()} en {nombre_dest}",
            descripcion=f"Paquete {tipo_paquete} de {duracion} días en {nombre_dest}, {pais}. {hotel.descripcion}",
            score_match=score,
            destino=nombre_dest,
            pais=pais,
            fecha_salida_sugerida=fecha_s,
            fecha_regreso_sugerida=fecha_r,
            duracion_dias=duracion,
            vuelo_ida=vuelo_ida,
            vuelo_vuelta=vuelo_vuelta,
            hotel=hotel,
            precio_total_paquete_usd=round(precio_paquete - ahorro, 2),
            ahorro_vs_separado_usd=ahorro,
            por_que_te_recomendamos=razones,
            tags=tags,
        ))

    # Ordenar por score
    paquetes.sort(key=lambda p: p.score_match, reverse=True)

    mensaje = (
        f"Encontré {len(paquetes)} paquetes perfectos para una {tipo_paquete} "
        f"de {duracion} días con presupuesto {req.presupuesto}. "
        f"El mejor match es {paquetes[0].destino} con un {int(paquetes[0].score_match * 100)}% de compatibilidad."
    )

    return ResultadoBusqueda(
        request_id=f"REQ-{_uid()}",
        preferencias_aplicadas=req,
        total_paquetes=len(paquetes),
        paquetes=paquetes,
        mensaje_ia=mensaje,
    )


def generar_tools() -> MCPToolsResponse:
    """Retorna la descripción estilo MCP protocol de las herramientas disponibles."""
    tools = [
        MCPTool(
            name="search_flights",
            description="Busca vuelos disponibles en el inventario de Turismo entre dos destinos.",
            category="inventory",
            parameters=[
                MCPToolParameter(name="origin", type="string", description="Código IATA del origen (ej: BUE)", required=True, example="BUE"),
                MCPToolParameter(name="destination", type="string", description="Código IATA del destino (ej: MIA)", required=True, example="MIA"),
                MCPToolParameter(name="date", type="string", description="Fecha de salida en formato YYYY-MM-DD", required=True, example="2026-07-15"),
                MCPToolParameter(name="passengers", type="integer", description="Cantidad de pasajeros (1-9)", required=False, example="2"),
            ],
            returns="Lista de vuelos disponibles con precios, horarios y disponibilidad.",
            example_call={"origin": "BUE", "destination": "MIA", "date": "2026-07-15", "passengers": 2},
        ),
        MCPTool(
            name="search_hotels",
            description="Busca hoteles disponibles en un destino para las fechas indicadas.",
            category="inventory",
            parameters=[
                MCPToolParameter(name="destination", type="string", description="Ciudad o código IATA", required=True, example="CUN"),
                MCPToolParameter(name="checkin", type="string", description="Fecha de check-in YYYY-MM-DD", required=True, example="2026-07-15"),
                MCPToolParameter(name="nights", type="integer", description="Cantidad de noches de estadía", required=True, example="7"),
                MCPToolParameter(name="guests", type="integer", description="Cantidad de huéspedes", required=False, example="2"),
            ],
            returns="Lista de hoteles disponibles con precios, amenities y disponibilidad.",
            example_call={"destination": "CUN", "checkin": "2026-07-15", "nights": 7, "guests": 2},
        ),
        MCPTool(
            name="smart_search",
            description="Motor de búsqueda inteligente que combina preferencias del usuario y retorna paquetes sugeridos con score de compatibilidad.",
            category="ai_recommendation",
            parameters=[
                MCPToolParameter(name="tipo_viaje", type="string", description="playa | ciudad | montaña | aventura | cultural", required=False, example="playa"),
                MCPToolParameter(name="estilo", type="string", description="familia | pareja | solo | amigos", required=False, example="pareja"),
                MCPToolParameter(name="presupuesto", type="string", description="económico | moderado | premium | lujo", required=False, example="moderado"),
                MCPToolParameter(name="duracion_dias", type="integer", description="Duración deseada del viaje", required=False, example="7"),
                MCPToolParameter(name="origen", type="string", description="Ciudad/código de origen", required=False, example="BUE"),
                MCPToolParameter(name="pasajeros", type="integer", description="Cantidad de viajeros", required=False, example="2"),
                MCPToolParameter(name="mes_preferido", type="string", description="Mes preferido YYYY-MM", required=False, example="2026-07"),
                MCPToolParameter(name="requiere_directo", type="boolean", description="Si requiere vuelo directo", required=False, example="false"),
            ],
            returns="Lista de paquetes sugeridos con vuelo + hotel + score de match y razones de recomendación.",
            example_call={"tipo_viaje": "playa", "estilo": "familia", "presupuesto": "moderado", "duracion_dias": 10, "pasajeros": 4},
        ),
        MCPTool(
            name="get_user_preferences",
            description="Obtiene las preferencias de viaje personalizadas del usuario desde su perfil.",
            category="user_context",
            parameters=[],
            returns="Objeto con preferencias del usuario: tipo de viaje, estilo, presupuesto, idiomas, etc.",
            example_call={},
        ),
        MCPTool(
            name="get_user_calendar",
            description="Consulta el calendario del usuario para identificar fechas disponibles para viajar.",
            category="user_context",
            parameters=[
                MCPToolParameter(name="month", type="string", description="Mes a consultar en formato YYYY-MM", required=True, example="2026-07"),
            ],
            returns="Eventos del mes y ventanas de fechas libres para viajar.",
            example_call={"month": "2026-07"},
        ),
        MCPTool(
            name="get_travel_history",
            description="Recupera el historial de viajes realizados por el usuario para personalizar recomendaciones.",
            category="user_context",
            parameters=[],
            returns="Historial de viajes con destinos, ratings y comentarios del usuario.",
            example_call={},
        ),
    ]

    return MCPToolsResponse(
        server_name="turismo-mcp-server",
        server_version="1.0.0",
        protocol="MCP/1.0",
        total_tools=len(tools),
        tools=tools,
    )
