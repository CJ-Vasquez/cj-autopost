"""CJ_Dev4.20 AutoPost — Entry point principal."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import click
import structlog
from rich.console import Console

# Agregar el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import get_settings, get_enabled_platforms, load_platform_config, BASE_DIR
from core.models import TopicData, PublishContent, PublishResult

console = Console()


def setup_logging(level: str) -> None:
    """Configura logging estructurado."""
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level, logging.INFO),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_dir / "autopost.log"), encoding="utf-8"),
        ],
    )
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level, logging.INFO)
        ),
    )


def validate_system() -> bool:
    """Valida configuración y credenciales."""
    settings = get_settings()
    errors = settings.validate_all_tokens()

    if "google" in errors:
        console.print(f"[red]✗ Google: faltan {errors['google']}[/red]")
        return False

    console.print("[green]✓ Config válida[/green]")

    enabled = get_enabled_platforms()
    console.print(f"[green]✓ Plataformas habilitadas: {', '.join(enabled)}[/green]")

    for platform in enabled:
        if platform in errors:
            console.print(f"[yellow]⚠ {platform}: faltan {errors[platform]}[/yellow]")

    return True


def get_publisher(platform: str):
    """Retorna la instancia del publisher para una plataforma."""
    from publishers.tiktok_publisher import TikTokPublisher
    from publishers.instagram_publisher import InstagramPublisher
    from publishers.youtube_publisher import YouTubePublisher
    from publishers.facebook_publisher import FacebookPublisher

    publishers = {
        "tiktok": TikTokPublisher,
        "instagram": InstagramPublisher,
        "youtube": YouTubePublisher,
        "facebook": FacebookPublisher,
    }
    cls = publishers.get(platform)
    if cls is None:
        return None
    return cls()


def run_pipeline(
    topic: TopicData,
    platforms: list[str],
    dry_run: bool,
) -> dict[str, str]:
    """Ejecuta el pipeline completo para un tema."""
    from core.image_generator import ImageGenerator
    from core.voice_generator import VoiceGenerator
    from core.video_generator import VideoGenerator
    from core.drive_uploader import DriveUploader

    logger = structlog.get_logger("pipeline")
    urls: dict[str, str] = {}

    # 1. Generar imágenes
    console.print("[bold]Generando imágenes...[/bold]")
    img_gen = ImageGenerator()
    images = img_gen.generate_all_formats(topic)
    for platform, path in images.items():
        console.print(f"[green]✓ Imagen {platform} generada ({path.name})[/green]")

    # 2. Generar voz
    console.print("[bold]Generando narración...[/bold]")
    voice_gen = VoiceGenerator()
    audio_path = voice_gen.generate(topic)
    console.print(f"[green]✓ Audio generado ({audio_path.name})[/green]")

    # 3. Generar video
    console.print("[bold]Generando video...[/bold]")
    video_gen = VideoGenerator()
    videos: dict[str, Path] = {}
    for platform in platforms:
        if platform in images:
            video_path = video_gen.generate(
                images=[images[platform]],
                audio=audio_path,
                topic=topic,
                platform=platform,
            )
            videos[platform] = video_path
            console.print(f"[green]✓ Video {platform} generado ({video_path.name})[/green]")

    # 4. Subir a Google Drive
    drive_urls: dict[str, str] = {}
    if not dry_run:
        console.print("[bold]Subiendo a Google Drive...[/bold]")
        try:
            uploader = DriveUploader()
            all_files = {}
            for name, path in images.items():
                all_files[f"imagen_{name}.png"] = path
            for name, path in videos.items():
                all_files[f"video_{name}.mp4"] = path
            all_files["audio_narration.mp3"] = audio_path
            drive_urls = uploader.upload_batch(topic, all_files)
            console.print(f"[green]✓ {len(drive_urls)} archivos subidos a Drive[/green]")
        except Exception as e:
            logger.error("Error subiendo a Drive", error=str(e))
            console.print(f"[yellow]⚠ Drive upload falló: {e}[/yellow]")

    # 5. Publicar en cada plataforma
    config = load_platform_config()
    content_cfg = config.get("content", {})
    base_hashtags = content_cfg.get("hashtags_base", [])
    all_hashtags = base_hashtags + [f"#{h.lstrip('#')}" for h in topic.hashtags_extra]

    for platform in platforms:
        content = PublishContent(
            topic=topic,
            image_path=images.get(platform),
            video_path=videos.get(platform),
            image_url=drive_urls.get(f"imagen_{platform}.png"),
            video_url=drive_urls.get(f"video_{platform}.mp4"),
            caption=f"{topic.titulo} | {topic.descripcion}",
            hashtags=all_hashtags,
        )

        if dry_run:
            console.print(f"[cyan]✓ [DRY RUN] {platform}: NO publicado (modo prueba)[/cyan]")
            continue

        publisher = get_publisher(platform)
        if publisher is None:
            console.print(f"[yellow]⚠ Publisher no encontrado para {platform}[/yellow]")
            continue

        try:
            result = publisher.publish(content)
            if result.success:
                urls[platform] = result.url
                console.print(f"[green]✓ {platform}: publicado → {result.url}[/green]")
            else:
                console.print(f"[red]✗ {platform}: {result.error}[/red]")
        except Exception as e:
            logger.error("Error publicando", platform=platform, error=str(e))
            console.print(f"[red]✗ {platform}: {e}[/red]")

    return urls


@click.command()
@click.option("--dry-run", is_flag=True, help="Simula sin publicar")
@click.option("--topic-id", help="Fuerza un tema específico por ID")
@click.option("--platforms", multiple=True, help="Plataformas específicas")
@click.option("--validate", is_flag=True, help="Solo valida credenciales")
def main(dry_run: bool, topic_id: str | None, platforms: tuple, validate: bool) -> None:
    """CJ_Dev4.20 AutoPost — Sistema de publicación automática."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = structlog.get_logger("main")

    if dry_run or settings.dry_run:
        dry_run = True
        console.print("[cyan][MODO DRY RUN ACTIVADO][/cyan]\n")

    console.print("[bold magenta]═══ CJ_Dev4.20 AutoPost ═══[/bold magenta]\n")

    # 1. Validar sistema
    if not validate_system():
        console.print("[red]Sistema no válido. Revisa la configuración.[/red]")
        sys.exit(1)

    if validate:
        console.print("\n[green]Validación completada.[/green]")
        return

    # 2. Leer tema del día
    console.print("\n[bold]Conectando con Google Sheets...[/bold]")
    try:
        from core.content_reader import ContentReader
        reader = ContentReader()
        pending = reader.get_pending_count()
        console.print(f"[green]✓ Google Sheets conectado — {pending} temas pendientes[/green]")

        if topic_id:
            topic = reader.get_today_topic()  # TODO: buscar por ID específico
        else:
            topic = reader.get_today_topic()

        if topic is None:
            console.print("[yellow]No hay temas pendientes para hoy.[/yellow]")
            return
    except Exception as e:
        logger.error("Error conectando Google Sheets", error=str(e))
        console.print(f"[red]✗ Google Sheets: {e}[/red]")
        sys.exit(1)

    console.print(f"\n[bold]Tema: {topic.icono} {topic.titulo}[/bold]")

    # 3. Determinar plataformas
    target_platforms = list(platforms) if platforms else get_enabled_platforms()
    console.print(f"Plataformas: {', '.join(target_platforms)}\n")

    # 4. Ejecutar pipeline
    start_time = time.time()

    try:
        urls = run_pipeline(topic, target_platforms, dry_run)
        duration = time.time() - start_time

        # 5. Actualizar Google Sheets
        if not dry_run and urls:
            try:
                reader.mark_as_published(topic.id, urls)
                console.print("[green]✓ Google Sheets actualizado[/green]")
            except Exception as e:
                logger.error("Error actualizando Sheet", error=str(e))

        # 6. Notificar por Telegram
        if not dry_run:
            try:
                from core.notifier import TelegramNotifier
                notifier = TelegramNotifier()
                notifier.notify_success(topic, urls, duration)

                if pending <= 7:
                    notifier.notify_low_content(pending)
            except Exception as e:
                logger.warning("Error notificando Telegram", error=str(e))

        # 7. Resumen
        if dry_run:
            console.print(f"\n[bold cyan]🎉 DRY RUN completado exitosamente en {duration:.1f}s[/bold cyan]")
        else:
            console.print(f"\n[bold green]🎉 PUBLICACIÓN COMPLETADA en {duration:.1f}s[/bold green]")

    except Exception as e:
        duration = time.time() - start_time
        logger.error("Error fatal en pipeline", error=str(e))
        console.print(f"\n[bold red]✗ Error fatal: {e}[/bold red]")

        # Marcar error en Sheet
        try:
            reader.mark_as_error(topic.id, str(e))
        except Exception:
            pass

        # Notificar error
        if not dry_run:
            try:
                from core.notifier import TelegramNotifier
                TelegramNotifier().notify_error(topic, e, "pipeline")
            except Exception:
                pass

        sys.exit(1)


if __name__ == "__main__":
    main()
