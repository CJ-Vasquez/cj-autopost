# CJ_Dev4.20 AutoPost

Sistema 100% automatizado que genera contenido educativo de programacion y lo publica diariamente en TikTok, Instagram, YouTube y Facebook.

```
                    +------------------+
                    |  Google Sheets   |
                    |  (contenido)     |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |   ContentReader   |
                    |  Lee tema del dia |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
        +-----------+  +-----------+  +-----------+
        |  Image    |  |  Voice    |  |  Video    |
        | Generator |  | Generator |  | Generator |
        +-----------+  +-----------+  +-----------+
              |              |              |
              +--------------+--------------+
                             |
                    +--------+---------+
                    |  Drive Uploader  |
                    +--------+---------+
                             |
              +---------+----+----+---------+
              |         |         |         |
              v         v         v         v
          +------+  +------+  +------+  +------+
          |TikTok|  |Insta |  |YouTube| |  FB  |
          +------+  +------+  +------+  +------+
                             |
                    +--------+---------+
                    | Telegram Notifier|
                    +------------------+
```

## Requisitos previos

- **Python 3.11+**
- **FFmpeg** instalado y en PATH
- **Cuenta Google Cloud** con Service Account
- **APIs habilitadas:** Google Sheets, Google Drive, YouTube Data API v3
- **Cuentas de desarrollador** en TikTok, Facebook/Instagram (Graph API)
- **Bot de Telegram** (opcional, para notificaciones)

## Instalacion

### 1. Clonar y crear entorno virtual

```bash
cd D:/cj_autopost
python -m venv venv
source venv/Scripts/activate   # Windows
pip install -r requirements.txt
```

### 2. Configurar credenciales

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Agregar Service Account de Google

Coloca el archivo JSON de tu Service Account en:
```
credentials/google_service_account.json
```

### 4. Crear Google Sheet

Crea una hoja con estas columnas en orden:

| A: ID | B: Fecha_Programada | C: Titulo | D: Descripcion | E: Codigo | F: Lenguaje | G: Color_Hex | H: Icono | I: Hashtags_Extra | J: Estado | K: URL_TikTok | L: URL_Instagram | M: URL_YouTube | N: URL_Facebook | O: Error_Log | P: Fecha_Publicacion |

**Estados posibles (columna J):**
- `pendiente` — sera procesado
- `publicado` — ya publicado
- `error` — fallo, revisar columna O
- `pausado` — skip temporal
- `borrador` — no publicar aun

### 5. Validar instalacion

```bash
python main.py --validate
```

## Configuracion de APIs

| Plataforma | Consola de desarrolladores |
|------------|---------------------------|
| Google Cloud | https://console.cloud.google.com/ |
| TikTok | https://developers.tiktok.com/ |
| Facebook/Instagram | https://developers.facebook.com/ |
| YouTube | https://console.cloud.google.com/apis/library/youtube.googleapis.com |
| Telegram Bot | https://t.me/BotFather |

## Comandos de uso

```bash
# Ver ayuda
python main.py --help

# Simular sin publicar (recomendado para probar)
python main.py --dry-run

# Solo validar credenciales
python main.py --validate

# Publicar en plataformas especificas
python main.py --platforms tiktok --platforms instagram

# Forzar un tema por ID
python main.py --topic-id 001

# Modo completo (publicacion real)
python main.py
```

## Automatizacion con n8n

### Opcion 1: Docker (recomendado)

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -v /ruta/cj_autopost:/data/cj_autopost \
  n8nio/n8n
```

### Opcion 2: npm

```bash
npm install n8n -g
n8n start
```

Importar workflow: `http://localhost:5678` -> Import from file -> `n8n/workflow_cj_autopost.json`

El workflow ejecuta `python main.py` todos los dias a las 9:00 AM (America/Lima).

## Troubleshooting

| # | Error | Solucion |
|---|-------|----------|
| 1 | `ModuleNotFoundError` | Ejecutar `pip install -r requirements.txt` |
| 2 | `FileNotFoundError: service_account.json` | Verificar ruta en `.env` GOOGLE_SERVICE_ACCOUNT_JSON |
| 3 | `gspread.exceptions.SpreadsheetNotFound` | Compartir el Sheet con el email del Service Account |
| 4 | `PIL.UnidentifiedImageError` | Verificar que las fuentes se descargaron en `assets/fonts/` |
| 5 | `moviepy - FFmpeg not found` | Instalar FFmpeg y agregar al PATH del sistema |
| 6 | `TikTok spam_risk_too_many_posts` | Esperar 1-2 horas, el sistema reintenta automaticamente |
| 7 | `Instagram: image_url must be public` | Las imagenes deben estar en URL publica (Drive con permisos) |
| 8 | `YouTube quota exceeded` | Limite de 10,000 unidades/dia, esperar 24h |
| 9 | `Facebook: Invalid OAuth token` | Regenerar token de pagina en Facebook Developer Console |
| 10 | `Telegram: chat not found` | Enviar /start al bot primero, verificar CHAT_ID |

## Como agregar nuevos temas

1. Abrir el Google Sheet
2. Agregar una nueva fila con:
   - **ID**: identificador unico (ej: `VAR001`)
   - **Fecha_Programada**: formato `YYYY-MM-DD` (opcional)
   - **Titulo**: nombre del tema
   - **Descripcion**: explicacion breve (1-2 oraciones)
   - **Codigo**: snippet de codigo (se renderiza con syntax highlighting)
   - **Lenguaje**: `python`, `javascript`, `java`, etc.
   - **Color_Hex**: color del tema (ej: `#6C63FF`)
   - **Icono**: emoji representativo
   - **Estado**: `pendiente`

## Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Test especifico
pytest tests/test_image_generator.py -v
```

## Estructura del proyecto

```
cj_autopost/
├── .env / .env.example      # Variables de entorno
├── config/                   # Configuracion (settings, platforms.yaml)
├── core/                     # Logica principal
│   ├── content_reader.py     # Lee Google Sheets
│   ├── image_generator.py    # Genera imagenes con Pillow
│   ├── video_generator.py    # Genera videos con MoviePy
│   ├── voice_generator.py    # Genera voz con gTTS
│   ├── drive_uploader.py     # Sube a Google Drive
│   └── notifier.py           # Notificaciones Telegram
├── publishers/               # Publicadores por plataforma
├── n8n/                      # Workflow de automatizacion
├── assets/                   # Fuentes y templates
├── output/                   # Archivos generados
├── logs/                     # Logs del sistema
├── tests/                    # Tests unitarios
└── main.py                   # Entry point
```

## Roadmap

- [ ] IA para generar temas automaticamente con Claude API
- [ ] A/B testing de hashtags
- [ ] Dashboard web con FastAPI
- [ ] Soporte multi-idioma (ES/EN)
- [ ] Thumbnails personalizados para YouTube
- [ ] Webhook de TikTok para metricas
- [ ] Soporte para Twitter/X

---

*CJ_Dev4.20 AutoPost | Stack: Python + n8n | 100% Gratuito*
