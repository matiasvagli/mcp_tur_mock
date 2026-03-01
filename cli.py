#!/usr/bin/env python3
"""
CLI del Asistente Personal de Viajes 🧳
=======================================
Interfaz de terminal para interactuar con el agente IA de viajes.
Soporta consultas únicas y modo chat multi-turno.

Uso:
    python cli.py                    # modo chat interactivo
    python cli.py -q "tu consulta"   # consulta directa
    python cli.py --url http://...   # apuntar a otro servidor
"""

import json
import sys

import click
import httpx
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

console = Console()

BASE_URL = "http://localhost:8001"
CONVERSATION_ID: str | None = None


# ── Helpers de display ─────────────────────────────────────────────────────────

def _header():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🧳 Asistente Personal de Viajes[/bold cyan]\n"
        "[dim]Powered by Google Gemini · Turismo MCP Demo[/dim]",
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print()


def _print_analysis(analysis: dict):
    """Muestra el bloque de análisis del agente."""
    table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 1),
        title="[bold yellow]🔍 Análisis del agente[/bold yellow]",
        title_style="yellow",
    )
    table.add_column("Campo", style="dim", width=22)
    table.add_column("Valor", style="white")

    icons = {
        "calendar_check": "📅",
        "travel_style": "✈️ ",
        "transport_decision": "🚗",
        "duration": "⏱️ ",
        "companions": "👥",
        "budget": "💰",
    }
    labels = {
        "calendar_check": "Calendario",
        "travel_style": "Estilo de viaje",
        "transport_decision": "Transporte",
        "duration": "Duración",
        "companions": "Compañía",
        "budget": "Presupuesto",
    }

    for key, label in labels.items():
        if value := analysis.get(key):
            icon = icons.get(key, "•")
            table.add_row(f"{icon} {label}", str(value))

    console.print(Panel(table, border_style="yellow", padding=(0, 1)))


def _print_proposal(proposal: dict):
    """Muestra la propuesta principal de viaje."""
    dest = proposal.get("destination", "—")
    reason = proposal.get("reason", "")
    dates = proposal.get("dates", {})
    transport = proposal.get("transport", {})
    hotel = proposal.get("hotel", {})
    total = proposal.get("total_estimate_usd", 0)
    alternatives = proposal.get("alternatives", [])

    # ── Destino principal ──────────────────────────────────────────────────
    console.print(Panel(
        f"[bold green]📍 {dest}[/bold green]\n\n[white]{reason}[/white]",
        border_style="green",
        title="[bold green]✅ Propuesta Principal[/bold green]",
        padding=(1, 2),
    ))

    # ── Detalles grid ──────────────────────────────────────────────────────
    details = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    details.add_column("", style="dim")
    details.add_column("", style="white")
    details.add_column("", style="dim")
    details.add_column("", style="white")

    departure = dates.get("departure", "—")
    ret = dates.get("return", "—")
    mode = transport.get("mode", "—").upper()
    transport_reason = transport.get("reason", "")

    details.add_row("📅 Salida", departure, "🏁 Regreso", ret)
    details.add_row(
        f"{'🚗' if mode == 'AUTO' else '✈️'} Transporte",
        f"[bold]{mode}[/bold]",
        "💵 Total estimado",
        f"[bold green]USD {total:.0f}[/bold green]",
    )
    if transport_reason:
        details.add_row("   Motivo", f"[dim]{transport_reason}[/dim]", "", "")

    console.print(details)

    # ── Hotel ──────────────────────────────────────────────────────────────
    if hotel:
        stars = "⭐" * int(hotel.get("stars", 0))
        hotel_name = hotel.get("name", "—")
        price_night = hotel.get("price_per_night", 0)
        price_total = hotel.get("price_total", 0)
        amenities = ", ".join(hotel.get("amenities", [])[:4])
        why = hotel.get("why", "")

        hotel_text = (
            f"[bold]{hotel_name}[/bold]  {stars}\n"
            f"[dim]USD {price_night:.0f}/noche · Total: [bold]USD {price_total:.0f}[/bold][/dim]\n"
        )
        if amenities:
            hotel_text += f"[dim]🛎️  {amenities}[/dim]\n"
        if why:
            hotel_text += f"\n[italic cyan]{why}[/italic cyan]"

        console.print(Panel(
            hotel_text,
            title="[bold magenta]🏨 Hotel Sugerido[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        ))

    # ── Alternativas ───────────────────────────────────────────────────────
    if alternatives:
        alt_table = Table(
            title="[bold blue]🗺️  Alternativas[/bold blue]",
            box=box.SIMPLE_HEAVY,
            title_style="blue",
            show_header=True,
            header_style="bold blue",
        )
        alt_table.add_column("Destino", style="cyan", width=28)
        alt_table.add_column("Razón", style="white")
        alt_table.add_column("Distancia", style="dim", width=12, justify="right")

        for alt in alternatives:
            km = alt.get("distance_km", "")
            km_str = f"{km} km" if km else "—"
            alt_table.add_row(
                alt.get("destination", "—"),
                alt.get("reason", ""),
                km_str,
            )

        console.print(Panel(alt_table, border_style="blue", padding=(0, 1)))

    # ── Vuelo (si aplica) ──────────────────────────────────────────────────
    flight = transport.get("flight_option")
    if flight and isinstance(flight, dict):
        flight_text = (
            f"[bold]{flight.get('aerolinea', '—')}[/bold] · "
            f"{flight.get('codigo_vuelo', '')} · "
            f"Salida: {flight.get('hora_salida', '—')} → "
            f"Llegada: {flight.get('hora_llegada', '—')}\n"
            f"Escalas: {flight.get('escalas', 0)} · "
            f"[bold green]USD {flight.get('precio_total_usd', 0):.0f}[/bold green]"
        )
        console.print(Panel(
            flight_text,
            title="[bold yellow]✈️  Vuelo Sugerido[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))


def _print_agent_note(note: str):
    if note:
        console.print()
        console.print(Panel(
            f"[italic]{note}[/italic]",
            title="[bold cyan]💬 El agente dice[/bold cyan]",
            border_style="cyan",
            padding=(0, 2),
        ))


def _print_response(data: dict):
    """Renderiza la respuesta completa del agente."""
    console.print()
    console.print(Rule("[bold]Respuesta del Agente[/bold]", style="dim"))
    console.print()

    analysis = data.get("analysis", {})
    proposal = data.get("proposal", {})
    note = data.get("agent_note", "")

    # Caso de error o raw_response
    if "raw_response" in proposal:
        console.print(Panel(
            Markdown(proposal["raw_response"]),
            title="Respuesta",
            border_style="yellow",
        ))
        return

    if analysis:
        _print_analysis(analysis)

    if proposal:
        _print_proposal(proposal)

    _print_agent_note(note)
    console.print()


def _call_plan_trip(query: str, base_url: str) -> dict:
    """Llama al endpoint /ai/plan-trip."""
    with console.status("[cyan]Consultando calendario, preferencias e inventario...[/cyan]", spinner="dots"):
        try:
            r = httpx.post(
                f"{base_url}/ai/plan-trip",
                json={"query": query},
                timeout=90,
            )
            r.raise_for_status()
            return r.json()
        except httpx.ConnectError:
            console.print(f"\n[red]❌ No se pudo conectar al servidor en {base_url}[/red]")
            console.print("[dim]Verificá que el servidor esté corriendo: uvicorn main:app --port 8001 --reload[/dim]")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", str(e))
            console.print(f"\n[red]❌ Error del servidor ({e.response.status_code}): {detail}[/red]")
            if "GEMINI_API_KEY" in detail:
                console.print("[yellow]💡 Exportá tu API key: export GEMINI_API_KEY='tu-clave'[/yellow]")
                console.print("[dim]Obtené la clave gratis en: https://aistudio.google.com/app/apikey[/dim]")
            sys.exit(1)


def _call_chat(message: str, conv_id: str | None, base_url: str) -> tuple[dict, str]:
    """Llama al endpoint /ai/chat."""
    with console.status("[cyan]Pensando...[/cyan]", spinner="dots"):
        try:
            r = httpx.post(
                f"{base_url}/ai/chat",
                json={"message": message, "conversation_id": conv_id},
                timeout=90,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("response", data), data.get("conversation_id", "")
        except httpx.ConnectError:
            console.print(f"\n[red]❌ No se pudo conectar al servidor en {base_url}[/red]")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", str(e))
            console.print(f"\n[red]❌ Error ({e.response.status_code}): {detail}[/red]")
            if "GEMINI_API_KEY" in detail:
                console.print("[yellow]💡 Exportá tu API key: export GEMINI_API_KEY='tu-clave'[/yellow]")
            sys.exit(1)


def _check_status(base_url: str):
    """Verifica el estado del servidor antes de comenzar."""
    try:
        r = httpx.get(f"{base_url}/ai/status", timeout=5)
        data = r.json()
        if not data.get("api_key_configured"):
            console.print(Panel(
                "[yellow]⚠️  El servidor no tiene GEMINI_API_KEY configurada.[/yellow]\n\n"
                "Reiniciá el servidor exportando la variable primero:\n"
                "[bold]export GEMINI_API_KEY='tu-clave'[/bold]\n"
                "[bold]uvicorn main:app --port 8001 --reload[/bold]\n\n"
                "[dim]Obtené la clave gratis en: https://aistudio.google.com/app/apikey[/dim]",
                border_style="yellow",
                title="API Key no configurada",
            ))
            sys.exit(1)
    except httpx.ConnectError:
        console.print(Panel(
            f"[red]❌ No hay servidor corriendo en {base_url}[/red]\n\n"
            "Inicialo con:\n"
            "[bold]uvicorn main:app --port 8001 --reload[/bold]",
            border_style="red",
            title="Servidor no disponible",
        ))
        sys.exit(1)


# ── Comandos CLI ───────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--url", default=BASE_URL, help="URL base del servidor", show_default=True)
@click.option("-q", "--query", default=None, help="Consulta directa (sin modo chat)")
@click.pass_context
def cli(ctx, url, query):
    """
    🧳 Asistente Personal de Viajes

    Sin argumentos → entra en modo chat interactivo.\n
    Con -q → ejecuta una consulta y muestra el resultado.
    """
    ctx.ensure_object(dict)
    ctx.obj["url"] = url

    if ctx.invoked_subcommand is None:
        if query:
            # Modo consulta directa
            _header()
            _check_status(url)
            console.print(f"[dim]Consulta:[/dim] [italic]{query}[/italic]\n")
            data = _call_plan_trip(query, url)
            _print_response(data)
        else:
            # Modo chat interactivo por defecto
            ctx.invoke(chat, url=url)


@cli.command()
@click.option("--url", default=BASE_URL, help="URL base del servidor", show_default=True)
def chat(url):
    """
    💬 Chat interactivo multi-turno con el agente.

    Podés ir refinando la propuesta turno a turno:
    "buscame algo para este finde" → "dale pero más barato" → "y si voy el sábado?"
    """
    global CONVERSATION_ID

    _header()
    _check_status(url)

    console.print("[dim]Modo chat interactivo. Escribí [bold]salir[/bold] para terminar, [bold]reset[/bold] para nueva conversación.[/dim]")
    console.print("[dim]Tip: podés pedir cosas como:[/dim]")
    console.print("[dim]  → 'che fijate si tengo libre este finde'[/dim]")
    console.print("[dim]  → 'mi aniversario es en 2 meses, algo romántico'[/dim]")
    console.print("[dim]  → 'quiero ir a la playa con los chicos en julio'[/dim]")
    console.print()

    while True:
        try:
            query = Prompt.ask("[bold cyan]Vos[/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[dim]¡Hasta luego! 👋[/dim]")
            break

        if not query:
            continue

        if query.lower() in ("salir", "exit", "quit", "chau", "bye"):
            console.print("\n[dim]¡Hasta luego! 👋[/dim]")
            break

        if query.lower() in ("reset", "nueva", "nuevo", "reiniciar"):
            CONVERSATION_ID = None
            console.print("[dim]✨ Conversación reiniciada.[/dim]\n")
            continue

        response, new_id = _call_chat(query, CONVERSATION_ID, url)
        CONVERSATION_ID = new_id

        if CONVERSATION_ID:
            console.print(f"[dim]conversation_id: {CONVERSATION_ID}[/dim]")

        _print_response(response)


@cli.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--url", default=BASE_URL, help="URL base del servidor", show_default=True)
@click.option("--json-output", is_flag=True, help="Mostrar respuesta JSON cruda")
def plan(query, url, json_output):
    """
    🗺️  Planificar un viaje en una sola consulta.

    Ejemplo:\n
        python cli.py plan "escapada finde con mi mujer"\n
        python cli.py plan "quiero ir a la playa en familia en julio"
    """
    query_str = " ".join(query)
    _header()
    _check_status(url)
    console.print(f"[dim]Consulta:[/dim] [italic cyan]{query_str}[/italic cyan]\n")

    data = _call_plan_trip(query_str, url)

    if json_output:
        console.print_json(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        _print_response(data)


@cli.command()
@click.option("--url", default=BASE_URL, help="URL base del servidor", show_default=True)
def status(url):
    """🔍 Ver el estado del servidor y del agente IA."""
    try:
        r = httpx.get(f"{url}/ai/status", timeout=5)
        data = r.json()

        ok = data.get("api_key_configured", False)
        color = "green" if ok else "yellow"
        icon = "✅" if ok else "⚠️"

        console.print(Panel(
            f"[bold]Agente:[/bold] {data.get('agent', '—')}\n"
            f"[bold]Modelo:[/bold] {data.get('model', '—')}\n"
            f"[bold]API Key:[/bold] [{color}]{icon} {'Configurada' if ok else 'Falta configurar'}[/{color}]\n"
            f"[bold]Estado:[/bold] {data.get('status', '—')}\n"
            f"[bold]Conversaciones activas:[/bold] {data.get('active_conversations', 0)}",
            title="[bold]Estado del Servidor[/bold]",
            border_style=color,
            padding=(1, 2),
        ))
    except httpx.ConnectError:
        console.print(f"[red]❌ No hay servidor en {url}[/red]")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
