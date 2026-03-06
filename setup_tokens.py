"""Guia interactiva para configurar todos los tokens — CJ_Dev4.20 AutoPost."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("Instala dependencias primero: pip install -r requirements.txt")
    sys.exit(1)

console = Console()
ENV_PATH = Path(__file__).parent / ".env"

STEPS = [
    {
        "id": "google_sa",
        "title": "PASO 1: Google Cloud — Service Account",
        "vars": [],
        "instructions": [
            "1. Ve a https://console.cloud.google.com/",
            "2. Crea un proyecto nuevo (ej: 'cj-autopost')",
            "3. Ve a 'APIs & Services' > 'Library'",
            "4. Habilita estas 3 APIs:",
            "   - Google Sheets API",
            "   - Google Drive API",
            "   - YouTube Data API v3",
            "5. Ve a 'APIs & Services' > 'Credentials'",
            "6. Click 'Create Credentials' > 'Service Account'",
            "7. Nombre: 'cj-autopost-sa', click 'Create and Continue'",
            "8. Rol: 'Editor', click 'Done'",
            "9. Click en el Service Account creado",
            "10. Tab 'Keys' > 'Add Key' > 'Create new key' > JSON",
            "11. Descarga el archivo y copialo a: credentials/google_service_account.json",
            "",
            "IMPORTANTE: Copia el email del Service Account (ej: cj-autopost-sa@proyecto.iam.gserviceaccount.com)",
            "Lo necesitaras para compartir el Google Sheet.",
        ],
    },
    {
        "id": "google_sheet",
        "title": "PASO 2: Google Sheet",
        "vars": ["GOOGLE_SHEET_ID"],
        "instructions": [
            "1. Ve a https://docs.google.com/spreadsheets/",
            "2. Crea una nueva hoja de calculo",
            "3. En la fila 1, agrega estos encabezados (A-P):",
            "   A: ID | B: Fecha_Programada | C: Titulo | D: Descripcion",
            "   E: Codigo | F: Lenguaje | G: Color_Hex | H: Icono",
            "   I: Hashtags_Extra | J: Estado | K: URL_TikTok | L: URL_Instagram",
            "   M: URL_YouTube | N: URL_Facebook | O: Error_Log | P: Fecha_Publicacion",
            "",
            "4. Agrega una fila de prueba:",
            "   A: VAR001 | B: (vacio) | C: Variables en Python",
            "   D: Aprende que son las variables | E: nombre = 'CJ'",
            "   F: python | G: #6C63FF | H: (emoji) | I: (vacio) | J: pendiente",
            "",
            "5. Click 'Share' > pega el email del Service Account > Editor > Send",
            "",
            "6. Copia el SHEET ID de la URL:",
            "   https://docs.google.com/spreadsheets/d/[ESTE_ES_EL_ID]/edit",
        ],
    },
    {
        "id": "google_drive",
        "title": "PASO 3: Google Drive — Carpeta de salida",
        "vars": ["GOOGLE_DRIVE_FOLDER_ID"],
        "instructions": [
            "1. Ve a https://drive.google.com/",
            "2. Crea una carpeta llamada 'CJ_Dev4.20_Output'",
            "3. Click derecho > 'Share' > pega el email del Service Account > Editor",
            "4. Abre la carpeta y copia el FOLDER ID de la URL:",
            "   https://drive.google.com/drive/folders/[ESTE_ES_EL_ID]",
        ],
    },
    {
        "id": "telegram",
        "title": "PASO 4: Telegram Bot (notificaciones)",
        "vars": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
        "instructions": [
            "1. Abre Telegram y busca @BotFather",
            "2. Envia /newbot",
            "3. Nombre: CJ AutoPost Bot",
            "4. Username: cj_autopost_bot (o cualquier nombre disponible)",
            "5. BotFather te dara el TOKEN — copialo",
            "",
            "Para obtener tu CHAT_ID:",
            "6. Envia un mensaje cualquiera a tu bot",
            "7. Abre en el navegador:",
            "   https://api.telegram.org/bot<TU_TOKEN>/getUpdates",
            "8. Busca 'chat':{'id': NUMERO} — ese NUMERO es tu CHAT_ID",
        ],
    },
    {
        "id": "tiktok",
        "title": "PASO 5: TikTok for Developers",
        "vars": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN"],
        "instructions": [
            "1. Ve a https://developers.tiktok.com/",
            "2. Inicia sesion con tu cuenta de TikTok",
            "3. 'Manage apps' > 'Create app'",
            "4. Nombre: CJ AutoPost, Categoria: Entertainment",
            "5. En 'Products', agrega 'Content Posting API'",
            "6. Configura el 'Redirect URI' (ej: https://localhost/callback)",
            "7. Copia el Client Key y Client Secret",
            "",
            "Para obtener el Access Token:",
            "8. Usa el OAuth flow de TikTok:",
            "   https://www.tiktok.com/v2/auth/authorize/?client_key=TU_KEY&response_type=code&scope=video.upload,video.publish&redirect_uri=TU_REDIRECT",
            "9. Intercambia el 'code' por un access_token via API",
            "",
            "NOTA: La app necesita aprobacion de TikTok para Content Posting API.",
            "Esto puede tomar varios dias.",
        ],
    },
    {
        "id": "facebook",
        "title": "PASO 6: Facebook / Instagram (Meta for Developers)",
        "vars": [
            "FACEBOOK_PAGE_ID",
            "FACEBOOK_ACCESS_TOKEN",
            "INSTAGRAM_ACCESS_TOKEN",
            "INSTAGRAM_BUSINESS_ACCOUNT_ID",
        ],
        "instructions": [
            "1. Ve a https://developers.facebook.com/",
            "2. 'My Apps' > 'Create App' > tipo 'Business'",
            "3. Agrega el producto 'Instagram Graph API'",
            "",
            "Para Facebook Page:",
            "4. Ve a tu Facebook Page > Settings > Page ID (copialo)",
            "5. En la app de Meta: Tools > Graph API Explorer",
            "6. Selecciona tu app y solicita permisos:",
            "   pages_manage_posts, pages_read_engagement, publish_video",
            "7. Genera un Page Access Token de larga duracion",
            "",
            "Para Instagram:",
            "8. Vincula tu Instagram Business Account a la Facebook Page",
            "9. En Graph API Explorer, solicita permisos:",
            "   instagram_basic, instagram_content_publish",
            "10. Haz un GET /{page_id}?fields=instagram_business_account",
            "11. El 'id' dentro de instagram_business_account es tu BUSINESS_ACCOUNT_ID",
            "12. El access token de Instagram es el mismo Page Access Token",
            "",
            "NOTA: Instagram requiere cuenta Business/Creator vinculada a Facebook Page.",
        ],
    },
    {
        "id": "youtube",
        "title": "PASO 7: YouTube (OAuth 2.0)",
        "vars": ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"],
        "instructions": [
            "1. Ve a https://console.cloud.google.com/apis/credentials",
            "2. (Usa el mismo proyecto de Google Cloud del paso 1)",
            "3. 'Create Credentials' > 'OAuth client ID'",
            "4. Tipo: 'Web application'",
            "5. Redirect URI: http://localhost:8080/callback",
            "6. Copia el Client ID y Client Secret",
            "",
            "Para obtener el Refresh Token:",
            "7. Abre en el navegador (reemplaza TU_CLIENT_ID):",
            "   https://accounts.google.com/o/oauth2/v2/auth?client_id=TU_CLIENT_ID&redirect_uri=http://localhost:8080/callback&response_type=code&scope=https://www.googleapis.com/auth/youtube.upload&access_type=offline&prompt=consent",
            "8. Autoriza con tu cuenta de YouTube",
            "9. Copia el 'code' de la URL de redireccion",
            "10. Intercambia el code por tokens con curl:",
            '    curl -X POST https://oauth2.googleapis.com/token \\',
            '      -d "code=TU_CODE" \\',
            '      -d "client_id=TU_CLIENT_ID" \\',
            '      -d "client_secret=TU_CLIENT_SECRET" \\',
            '      -d "redirect_uri=http://localhost:8080/callback" \\',
            '      -d "grant_type=authorization_code"',
            "11. De la respuesta JSON, copia el 'refresh_token'",
        ],
    },
]


def read_env() -> dict[str, str]:
    """Lee el archivo .env y retorna un dict."""
    env: dict[str, str] = {}
    if not ENV_PATH.exists():
        return env
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def write_env(env: dict[str, str]) -> None:
    """Escribe el archivo .env preservando comentarios y estructura."""
    lines = []
    if ENV_PATH.exists():
        existing_lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    else:
        existing_lines = []

    written_keys: set[str] = set()
    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in env:
                lines.append(f"{key}={env[key]}")
                written_keys.add(key)
            else:
                lines.append(line)
        else:
            lines.append(line)

    for key, value in env.items():
        if key not in written_keys:
            lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_service_account() -> bool:
    """Verifica si existe el archivo de Service Account."""
    sa_path = Path(__file__).parent / "credentials" / "google_service_account.json"
    if sa_path.exists():
        try:
            data = json.loads(sa_path.read_text())
            email = data.get("client_email", "")
            console.print(f"[green]Service Account encontrado: {email}[/green]")
            return True
        except Exception:
            console.print("[yellow]Archivo existe pero no es un JSON valido[/yellow]")
            return False
    console.print("[red]No encontrado: credentials/google_service_account.json[/red]")
    return False


def show_status(env: dict[str, str]) -> None:
    """Muestra el estado actual de configuracion."""
    table = Table(title="Estado de Configuracion")
    table.add_column("Plataforma", style="bold")
    table.add_column("Variable", style="cyan")
    table.add_column("Estado")

    checks = {
        "Google": ["GOOGLE_SHEET_ID", "GOOGLE_DRIVE_FOLDER_ID"],
        "TikTok": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN"],
        "Instagram": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"],
        "Facebook": ["FACEBOOK_PAGE_ID", "FACEBOOK_ACCESS_TOKEN"],
        "YouTube": ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"],
        "Telegram": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
    }

    for platform, vars_list in checks.items():
        for var in vars_list:
            value = env.get(var, "")
            if value and not value.startswith("TU_"):
                status = "[green]Configurado[/green]"
            else:
                status = "[red]Pendiente[/red]"
            table.add_row(platform, var, status)

    console.print(table)

    sa_path = Path(__file__).parent / "credentials" / "google_service_account.json"
    if sa_path.exists():
        console.print("[green]Service Account JSON: Encontrado[/green]")
    else:
        console.print("[red]Service Account JSON: NO encontrado[/red]")


def run_step(step: dict, env: dict[str, str]) -> dict[str, str]:
    """Ejecuta un paso de la guia."""
    console.print(Panel("\n".join(step["instructions"]), title=step["title"], border_style="cyan"))

    if step["id"] == "google_sa":
        check_service_account()
        console.print()
        input("Presiona Enter cuando hayas completado este paso...")
        return env

    for var in step["vars"]:
        current = env.get(var, "")
        if current and not current.startswith("TU_"):
            console.print(f"[green]{var} ya configurado: {current[:20]}...[/green]")
            if not Confirm.ask(f"Quieres cambiar {var}?", default=False):
                continue
        value = Prompt.ask(f"Ingresa {var}").strip()
        if value:
            env[var] = value
            console.print(f"[green]{var} guardado[/green]")

    return env


def main() -> None:
    """Punto de entrada del setup interactivo."""
    console.print(Panel(
        "Esta guia te ayudara paso a paso a configurar\n"
        "todos los tokens y credenciales necesarios.\n\n"
        "Puedes salir en cualquier momento con Ctrl+C\n"
        "y continuar despues — el progreso se guarda automaticamente.",
        title="CJ_Dev4.20 AutoPost — Setup de Tokens",
        border_style="magenta",
    ))
    console.print()

    env = read_env()
    show_status(env)
    console.print()

    for i, step in enumerate(STEPS):
        console.print(f"\n[bold]{'=' * 60}[/bold]")
        console.print(f"[bold magenta]{step['title']}[/bold magenta]")
        console.print(f"[bold]{'=' * 60}[/bold]\n")

        skip = True
        if step["id"] == "google_sa":
            skip = check_service_account()
        else:
            for var in step["vars"]:
                val = env.get(var, "")
                if not val or val.startswith("TU_"):
                    skip = False
                    break

        if skip:
            console.print("[green]Ya completado. Saltando...[/green]")
            if not Confirm.ask("Quieres reconfigurar este paso?", default=False):
                continue

        try:
            env = run_step(step, env)
            write_env(env)
            console.print("[green]Progreso guardado en .env[/green]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrumpido. El progreso se guardo.[/yellow]")
            write_env(env)
            sys.exit(0)

    console.print(f"\n[bold]{'=' * 60}[/bold]")
    console.print("[bold green]SETUP COMPLETADO[/bold green]")
    console.print(f"[bold]{'=' * 60}[/bold]\n")
    show_status(env)

    console.print("\n[bold]Siguiente paso:[/bold]")
    console.print("  python main.py --validate")
    console.print("  python main.py --dry-run\n")


if __name__ == "__main__":
    main()
