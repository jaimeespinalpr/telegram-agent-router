# Telegram Agent Router

Plataforma para coordinar varios bots de Telegram desde una cuenta personal. El sistema usa tu cuenta como puente: tú envías una orden al bot director, el bot director decide a qué bot o usuario enviar cada tarea, y las respuestas vuelven al director para que la conversación continúe.

## Arquitectura

- `FastAPI`: panel web mínimo, estado del servicio y login.
- `Telethon`: conecta una cuenta personal de Telegram usando MTProto.
- `config/agents.yaml`: define bots, usuarios humanos y el bot director.
- Sin historial persistente: los mensajes viven en Telegram. La app solo mantiene estado de enrutamiento mientras está corriendo.

## Flujo de mensajes

1. Tú escribes al bot director en Telegram.
2. El director responde con una instrucción estructurada.
3. La app lee esa instrucción y envía mensajes individuales a los bots o usuarios indicados.
4. Cuando un bot responde, la app reenvía esa respuesta al director.
5. El director puede seguir coordinando nuevas tareas.

## Protocolo del bot director

El bot director debe responder usando uno de estos formatos.

Formato JSON:

```json
{"to":"research","message":"Busca información sobre X"}
```

Varios destinos:

```json
[
  {"to":"research","message":"Busca fuentes sobre X"},
  {"to":"writer","message":"Prepara un borrador con lo que ya sabemos"}
]
```

Formato simple:

```text
@research: Busca información sobre X
@writer: Prepara un borrador inicial
```

Los IDs como `research` y `writer` deben existir en `config/agents.yaml`.

## Configuración local

1. Crea una app en `https://my.telegram.org/apps` y toma `api_id` y `api_hash`.
2. Copia `.env.example` a `.env`.
3. Copia `config/agents.example.yaml` a `config/agents.yaml`.
4. Edita tus bots y usuarios.
5. Instala dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

6. Inicia sesión en Telegram:

```bash
python scripts/login_telegram.py
```

7. Arranca la app:

```bash
uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000`.

## GitHub y despliegue

GitHub guardará el código y GitHub Pages publica una página de entrada estática en:

```text
https://jaimeespinalpr.github.io/telegram-agent-router/
```

Importante: GitHub Pages no ejecuta Python, FastAPI ni Telethon. La página de Pages sirve como launcher público; el router real necesita estar corriendo en un servidor para escuchar Telegram. Para producción recomiendo Render, Railway, Fly.io o una VPS con disco persistente para guardar la sesión de Telethon.

Variables necesarias:

- `APP_SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_PATH`
- `AGENTS_CONFIG_PATH`
- `ROUTER_AGENT_ID`

Con Docker:

```bash
docker build -t telegram-agent-router .
docker run --env-file .env -p 8000:8000 telegram-agent-router
```

Cuando tengas el backend público, abre la página de Pages, pega la URL HTTPS del backend y usa el botón "Abrir panel".

## Limitaciones

- La app debe iniciar sesión como cuenta personal de Telegram.
- Los bots deben poder recibir mensajes privados de tu cuenta.
- El director necesita emitir instrucciones en el protocolo anterior para que el router sepa a quién enviar cada mensaje.
- Para audio e imágenes, Telethon ya soporta medios; esta primera versión deja preparada la estructura, pero enruta texto.
