# Unity Visualizer

Unity front-end for the Telegram Agent Router. It renders an isometric office scene and polls the FastAPI backend at `http://127.0.0.1:8000/scene-state`.

## Open

1. Open Unity Hub.
2. Add this folder as a project: `UnityVisual`.
3. Open it with a 2022.3 LTS or newer editor.
4. In Unity, run `Tools > Telegram Office > Create Visualizer Scene`.
5. Open `Assets/Scenes/TelegramOffice.unity` if Unity does not open it automatically.
6. Press Play.

The scene is generated procedurally: tilemap-style floor, office rooms, pixel character sprites, and animated message packets.

## WebGL export target

When the lobby is ready, build WebGL into:

```text
/Users/jaimeespinalpr/Desktop/VM Machine/web/unity-build
```

FastAPI already serves that folder at:

```text
http://127.0.0.1:8000/unity-build/
```

## Backend

Keep the Python server running:

```bash
cd "/Users/jaimeespinalpr/Desktop/VM Machine"
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
