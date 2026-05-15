from contextlib import asynccontextmanager
from html import escape
import json
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import auth
from app.agents import load_agents_config
from app.settings import Settings, get_settings
from app.telegram_service import TelegramRouterService


def create_service(settings: Settings) -> TelegramRouterService:
    agents_config = load_agents_config(settings.agents_config_path)
    return TelegramRouterService(settings=settings, agents_config=agents_config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    service = create_service(settings)
    app.state.router_service = service
    try:
        await service.start()
    except Exception as exc:  # noqa: BLE001
        service.state.last_error = str(exc)
    yield
    await service.stop()


app = FastAPI(title="Telegram Agent Router", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=get_settings().app_secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
unity_build_path = Path("web/unity-build")
unity_build_path.mkdir(parents=True, exist_ok=True)
app.mount("/unity-build", StaticFiles(directory=unity_build_path), name="unity-build")


def get_service(request: Request) -> TelegramRouterService:
    return request.app.state.router_service


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, service: TelegramRouterService = Depends(get_service)):
    if not auth.is_authenticated(request):
        return RedirectResponse("/login", status_code=303)

    agents = service.agents_config.agents
    room_classes = {
        "router": "top-left green",
        "multi": "top-right blue",
        "ardida": "bottom-left pink",
        "prpagyda": "bottom-right teal",
        "prjimenezda": "bottom-center amber",
    }
    rooms = "\n".join(
        f"""
        <section class="room {room_classes.get(agent.id, "extra-room blue")}">
          <div class="back-wall"></div>
          <div class="rug"></div>
          <div class="wall-light"></div>
          <div class="pixel-window"><i></i></div>
          <div class="poster poster-one"></div>
          <div class="poster poster-two"></div>
          <div class="shelf"><span></span><span></span><span></span><b></b></div>
          <div class="plant"><i></i><i></i><i></i><b></b></div>
          <div class="cabinet"><span></span><span></span></div>
          <div class="desk">
            <div class="coffee"></div>
            <div class="monitor"><span></span></div>
            <div class="side-monitor"><span></span></div>
            <div class="keyboard"></div>
          </div>
          <div class="chair"></div>
          <div class="avatar avatar-{escape(agent.id)}">
            <div class="hair"></div>
            <div class="head"><span class="eye-left"></span><span class="eye-right"></span><span class="mouth"></span></div>
            <div class="neck"></div>
            <div class="torso"></div>
            <div class="arm arm-left"></div>
            <div class="arm arm-right"></div>
            <div class="leg leg-left"></div>
            <div class="leg leg-right"></div>
          </div>
          <div class="agent-label">
            <strong>{escape(agent.name)}</strong>
            <small>{escape(agent.telegram)} / {escape(agent.id)}</small>
          </div>
        </section>
        """
        for agent in agents
    )
    rows = "\n".join(
        f"<tr><td>{escape(agent.id)}</td><td>{escape(agent.telegram)}</td><td>{escape(agent.role)}</td></tr>"
        for agent in agents
    )
    status = "running" if service.state.started else "stopped"
    error = (
        f"<p class=\"error\"><strong>Last error:</strong> {escape(service.state.last_error)}</p>"
        if service.state.last_error
        else ""
    )
    events = "\n".join(
        f"<article class=\"event\"><div><strong>{escape(event.direction)}</strong> "
        f"<code>{escape(event.actor)}</code> <small>{escape(event.timestamp)}</small></div>"
        f"<pre>{escape(event.text)}</pre></article>"
        for event in service.state.events
    )
    if not events:
        events = "<p class=\"muted\">No messages yet. Send an order or write to the director in Telegram.</p>"
    latest_event = service.state.events[0] if service.state.events else None
    route_target = latest_event.actor if latest_event and latest_event.direction == "outgoing" else ""
    if route_target not in service.agents_config.by_id:
        route_target = ""
    scene_route = f"route-to-{escape(route_target)}" if route_target else "idle"
    scene_agents = [
        {"id": agent.id, "name": agent.name, "telegram": agent.telegram, "kind": agent.kind}
        for agent in agents
    ]
    scene_state = {
        "agents": scene_agents,
        "routeTarget": route_target,
        "latestText": latest_event.text if latest_event else "",
    }
    scene_state_json = json.dumps(scene_state)
    return HTMLResponse(
        f"""
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Telegram Agent Router</title>
          <style>
            :root {{
              --ink: #f7ead5;
              --panel: #1c1830;
              --wood: #9a5b2e;
              --wood-dark: #5d3426;
              --line: #3a2b38;
              --cyan: #52e6f2;
              --mint: #78f09b;
              --pink: #ff74d4;
              --amber: #ffd15a;
              --blue: #68a8ff;
            }}
            * {{ box-sizing: border-box; }}
            body {{
              margin: 0;
              min-height: 100vh;
              color: var(--ink);
              font-family: "Trebuchet MS", Verdana, sans-serif;
              background:
                radial-gradient(circle at 50% 42%, rgba(46, 59, 102, .7), transparent 34rem),
                linear-gradient(140deg, #08091d, #11132b 45%, #050614);
              overflow-x: hidden;
            }}
            body::before {{
              content: "";
              position: fixed;
              inset: 0;
              pointer-events: none;
              background: repeating-linear-gradient(
                0deg,
                rgba(255,255,255,.04) 0,
                rgba(255,255,255,.04) 1px,
                transparent 1px,
                transparent 4px
              );
              mix-blend-mode: soft-light;
              opacity: .28;
            }}
            .shell {{
              width: min(1440px, 100%);
              margin: 0 auto;
              padding: 18px;
              overflow-x: auto;
            }}
            .topbar {{
              display: flex;
              align-items: center;
              justify-content: space-between;
              gap: 14px;
              margin-bottom: 14px;
            }}
            h1, h2, p {{ margin: 0; }}
            h1 {{
              font-size: clamp(22px, 3vw, 38px);
              text-shadow: 0 3px 0 #2c1d2b;
            }}
            .status {{
              display: inline-flex;
              align-items: center;
              gap: 8px;
              padding: 8px 12px;
              background: #162f2a;
              border: 3px solid #315e4f;
              box-shadow: inset 0 -4px 0 rgba(0,0,0,.25);
            }}
            .status::before {{
              content: "";
              width: 9px;
              height: 9px;
              background: var(--mint);
              box-shadow: 0 0 12px var(--mint);
            }}
            .error {{
              margin: 10px 0;
              color: #ffd0d0;
              background: #61202b;
              padding: 10px;
              border: 2px solid #b44;
            }}
            .stage {{
              position: relative;
              display: grid;
              grid-template-columns: minmax(330px, 1fr) 390px minmax(330px, 1fr);
              grid-template-rows: 300px 230px 300px;
              gap: 18px;
              min-width: 1120px;
              min-height: 850px;
              image-rendering: pixelated;
            }}
            .floor {{
              position: absolute;
              inset: 242px 17% 190px 17%;
              border: 10px solid #4d3440;
              background:
                radial-gradient(circle at 52% 47%, rgba(255,220,120,.16), transparent 145px),
                repeating-linear-gradient(0deg, transparent 0 31px, rgba(64,37,26,.55) 31px 35px),
                repeating-linear-gradient(90deg, #ad6735 0 74px, #8f502a 74px 79px);
              box-shadow:
                inset 0 0 0 7px rgba(255,255,255,.08),
                inset 0 0 45px rgba(39,18,18,.35),
                0 16px 0 #2a1a24;
            }}
            .floor::before {{
              content: "";
              position: absolute;
              left: 50%;
              top: 50%;
              width: 210px;
              height: 126px;
              transform: translate(-50%, -50%);
              border-radius: 50%;
              background:
                radial-gradient(ellipse at center, rgba(84, 232, 190, .26), transparent 58%),
                repeating-radial-gradient(ellipse at center, rgba(255,255,255,.12) 0 4px, transparent 4px 14px);
              border: 7px solid rgba(60,35,43,.82);
              box-shadow: inset 0 0 0 6px rgba(255,209,90,.1);
            }}
            .floor::after {{
              content: "";
              position: absolute;
              inset: 14px;
              background:
                linear-gradient(45deg, transparent 49%, rgba(255,255,255,.08) 50%, transparent 51%),
                linear-gradient(-45deg, transparent 49%, rgba(255,255,255,.06) 50%, transparent 51%);
              background-size: 74px 74px;
              opacity: .42;
            }}
            .lobby-plant {{
              position: absolute;
              z-index: 4;
              left: calc(50% - 44px);
              top: calc(50% - 58px);
              width: 88px;
              height: 116px;
              filter: drop-shadow(0 12px 0 rgba(0,0,0,.22));
            }}
            .lobby-plant i {{
              position: absolute;
              bottom: 34px;
              width: 34px;
              height: 72px;
              background: #47d96c;
              border: 4px solid #183a22;
              border-radius: 34px 34px 8px 34px;
              transform-origin: bottom center;
              animation: leaf-sway 2.8s steps(3) infinite;
            }}
            .lobby-plant i:nth-child(1) {{ left: 8px; transform: rotate(-42deg); }}
            .lobby-plant i:nth-child(2) {{ left: 24px; transform: rotate(-14deg); background: #68ef7d; animation-delay: .2s; }}
            .lobby-plant i:nth-child(3) {{ right: 24px; transform: rotate(14deg); background: #3bc35d; animation-delay: .4s; }}
            .lobby-plant i:nth-child(4) {{ right: 8px; transform: rotate(42deg); animation-delay: .6s; }}
            .lobby-plant b {{
              position: absolute;
              left: 22px;
              bottom: 0;
              width: 46px;
              height: 44px;
              background: linear-gradient(#a36135, #713823);
              border: 6px solid #2f2028;
              box-shadow: inset 0 -8px 0 rgba(0,0,0,.2);
            }}
            .sofa {{
              position: absolute;
              z-index: 3;
              width: 102px;
              height: 54px;
              top: calc(50% + 110px);
              background: #244c8e;
              border: 6px solid #2f2028;
              border-radius: 18px 18px 8px 8px;
              box-shadow: inset 0 -12px 0 rgba(0,0,0,.2), 0 9px 0 rgba(0,0,0,.18);
            }}
            .sofa::before, .sofa::after {{
              content: "";
              position: absolute;
              top: 14px;
              width: 38px;
              height: 28px;
              border: 4px solid #2f2028;
              background: rgba(255,255,255,.07);
            }}
            .sofa::before {{ left: 10px; }}
            .sofa::after {{ right: 10px; }}
            .sofa-left {{ left: calc(50% - 180px); }}
            .sofa-right {{ right: calc(50% - 180px); transform: scaleX(-1); }}
            .wayfinder {{
              position: absolute;
              z-index: 4;
              width: 34px;
              height: 34px;
              display: grid;
              place-items: center;
              color: #201520;
              font-weight: 800;
              background: #ffd15a;
              border: 5px solid #2f2028;
              box-shadow: 0 0 16px rgba(255,209,90,.55);
              animation: sign-blink 2s steps(2) infinite;
            }}
            .sign-router {{ left: 33%; top: 34%; }}
            .sign-multi {{ right: 33%; top: 34%; animation-delay: .2s; }}
            .sign-ardida {{ left: 32%; bottom: 30%; animation-delay: .4s; }}
            .sign-prpagyda {{ right: 32%; bottom: 30%; animation-delay: .6s; }}
            .sign-prjimenezda {{ left: calc(50% - 17px); bottom: 20%; animation-delay: .8s; }}
            .hub {{
              grid-column: 2;
              grid-row: 2;
              z-index: 3;
              align-self: center;
              justify-self: center;
              width: 100%;
              padding: 18px;
              border: 6px solid #4b3340;
              background: linear-gradient(#c0793e, #7c4429);
              box-shadow: inset 0 0 0 4px rgba(255,255,255,.12), 0 12px 0 #2b1b23;
            }}
            .hub::before {{
              content: "";
              position: absolute;
              right: 18px;
              top: 16px;
              width: 54px;
              height: 42px;
              background:
                radial-gradient(circle at 18px 18px, #78f09b 0 7px, transparent 8px),
                radial-gradient(circle at 36px 18px, #ff74d4 0 7px, transparent 8px),
                #201520;
              border: 5px solid #2f2028;
              box-shadow: 0 0 18px rgba(255,209,90,.35);
            }}
            .hub::after {{
              content: "";
              position: absolute;
              left: 18px;
              top: 58px;
              width: 78px;
              height: 44px;
              background:
                linear-gradient(90deg, transparent 0 20%, rgba(255,255,255,.18) 20% 24%, transparent 24%),
                repeating-linear-gradient(0deg, #52e6f2 0 3px, transparent 3px 9px),
                #11182a;
              border: 5px solid #2f2028;
              opacity: .86;
            }}
            .hub h2 {{
              font-size: 18px;
              margin-bottom: 10px;
              color: #fff4d8;
            }}
            .hub form {{
              position: relative;
              z-index: 1;
              padding-left: 94px;
            }}
            textarea {{
              width: 100%;
              min-height: 104px;
              resize: vertical;
              border: 4px solid #3a2932;
              background: #f8e6c4;
              color: #25171c;
              padding: 12px;
              font: inherit;
              outline: none;
              box-shadow: inset 0 4px 0 rgba(0,0,0,.12);
            }}
            button {{
              width: 100%;
              margin-top: 10px;
              padding: 12px 14px;
              border: 4px solid #2d2230;
              color: #25171c;
              background: linear-gradient(#ffe07a, #e69b36);
              font: inherit;
              font-weight: 700;
              cursor: pointer;
              box-shadow: 0 5px 0 #563521;
            }}
            button:active {{ transform: translateY(3px); box-shadow: 0 2px 0 #563521; }}
            .room {{
              position: relative;
              z-index: 2;
              overflow: hidden;
              min-height: 280px;
              border: 10px solid #4b3340;
              background:
                linear-gradient(transparent 63%, rgba(57,28,24,.4) 63%),
                repeating-linear-gradient(90deg, rgba(0,0,0,.1) 0 4px, transparent 4px 12px),
                var(--room-bg, #263d46);
              box-shadow:
                inset 0 0 0 5px rgba(255,255,255,.08),
                inset 0 -68px 0 rgba(83,45,29,.38),
                inset 0 0 54px rgba(0,0,0,.25),
                0 14px 0 #261823;
            }}
            .room::before {{
              content: "";
              position: absolute;
              inset: 10px;
              border: 3px solid rgba(255,255,255,.08);
              pointer-events: none;
            }}
            .back-wall {{
              position: absolute;
              left: 0;
              right: 0;
              bottom: 76px;
              height: 16px;
              background: rgba(34,23,27,.36);
              border-top: 4px solid rgba(255,255,255,.08);
            }}
            .top-left {{ grid-column: 1; grid-row: 1; }}
            .top-right {{ grid-column: 3; grid-row: 1; }}
            .bottom-left {{ grid-column: 1; grid-row: 3; }}
            .bottom-right {{ grid-column: 3; grid-row: 3; }}
            .bottom-center {{ grid-column: 2; grid-row: 3; }}
            .green {{ --room-bg: #3c5f34; --accent: var(--mint); --shirt: #49d069; --hair: #6b351d; }}
            .blue {{ --room-bg: #263e6f; --accent: var(--blue); --shirt: #3f8cff; --hair: #1687ff; }}
            .pink {{ --room-bg: #66345f; --accent: var(--pink); --shirt: #ff65c8; --hair: #ff5fdc; }}
            .teal {{ --room-bg: #245f5d; --accent: var(--cyan); --shirt: #22d1a5; --hair: #14b9a8; }}
            .amber {{ --room-bg: #76582a; --accent: var(--amber); --shirt: #ffc52f; --hair: #2b191b; }}
            .rug {{
              position: absolute;
              left: 13%;
              right: 12%;
              bottom: 12px;
              height: 72px;
              background:
                radial-gradient(ellipse at center, rgba(255,255,255,.14), transparent 52%),
                var(--accent);
              opacity: .45;
              border: 5px solid rgba(41,26,32,.75);
              border-radius: 50%;
              filter: saturate(1.2);
            }}
            .wall-light {{
              position: absolute;
              right: 24px;
              top: 28px;
              width: 68px;
              height: 52px;
              border: 5px solid var(--accent);
              border-radius: 18px;
              opacity: .85;
              box-shadow: 0 0 24px var(--accent);
            }}
            .wall-light::before, .wall-light::after {{
              content: "";
              position: absolute;
              background: var(--accent);
              box-shadow: 0 0 18px var(--accent);
            }}
            .wall-light::before {{ left: 14px; right: 14px; top: 20px; height: 5px; }}
            .wall-light::after {{ left: 29px; top: 9px; width: 5px; height: 26px; }}
            .pixel-window {{
              position: absolute;
              right: 112px;
              top: 30px;
              width: 72px;
              height: 50px;
              background: #10182a;
              border: 5px solid #2f2028;
              box-shadow: inset 0 0 0 5px rgba(104,168,255,.16);
            }}
            .pixel-window i {{
              display: block;
              width: 45px;
              height: 18px;
              margin: 14px auto;
              border-top: 5px solid var(--accent);
              border-left: 5px solid var(--accent);
              border-right: 5px solid var(--accent);
              border-radius: 28px 28px 0 0;
              filter: drop-shadow(0 0 10px var(--accent));
            }}
            .poster-one, .poster-two {{
              position: absolute;
              top: 34px;
              width: 48px;
              height: 42px;
              border: 4px solid #2f2028;
              background:
                linear-gradient(135deg, transparent 48%, rgba(255,255,255,.22) 49% 52%, transparent 53%),
                linear-gradient(90deg, #f5c34b 0 33%, #e85b75 33% 66%, #5bb7f0 66%);
            }}
            .poster-one {{ left: 174px; }}
            .poster-two {{ left: 232px; transform: translateY(10px); }}
            .top-left .poster-one::before {{
              content: "";
              position: absolute;
              left: 10px;
              top: 8px;
              width: 26px;
              height: 20px;
              background: #ffd15a;
              clip-path: polygon(0 100%, 10% 25%, 34% 66%, 50% 0, 68% 66%, 90% 25%, 100% 100%);
            }}
            .top-left .poster-two {{
              background:
                linear-gradient(#f1e2bd 0 100%);
            }}
            .top-left .poster-two::before {{
              content: "";
              position: absolute;
              left: 8px;
              right: 8px;
              top: 9px;
              height: 4px;
              background: #4a6ea8;
              box-shadow: 0 10px 0 #4a6ea8, 12px 20px 0 #e86b6b, -8px 20px 0 #60b86b;
            }}
            .top-right .wall-light {{
              width: 82px;
              border-radius: 28px;
            }}
            .top-right .wall-light::before {{
              left: 18px;
              right: 18px;
              top: 22px;
            }}
            .top-right .wall-light::after {{
              left: 36px;
              top: 11px;
              height: 30px;
            }}
            .top-right .poster-one {{
              background:
                repeating-linear-gradient(0deg, #59f0a8 0 4px, transparent 4px 10px),
                #111b2e;
            }}
            .bottom-left .wall-light {{
              border-radius: 50%;
              transform: rotate(45deg);
            }}
            .bottom-left .wall-light::before {{
              left: 19px;
              right: 19px;
              top: 20px;
            }}
            .bottom-left .wall-light::after {{
              left: 29px;
              top: 26px;
              height: 18px;
            }}
            .bottom-left .poster-one {{
              background:
                linear-gradient(135deg, #f07ed8 0 35%, #ffd15a 35% 50%, #61bfff 50% 100%);
            }}
            .bottom-left .poster-two {{
              background:
                linear-gradient(90deg, #ff74d4 0 20%, #ffd15a 20% 40%, #78f09b 40% 60%, #68a8ff 60% 80%, #f7ead5 80%);
            }}
            .bottom-right .poster-one {{
              background:
                linear-gradient(90deg, transparent 0 18%, #ff6f6f 18% 30%, transparent 30% 42%, #ffd15a 42% 58%, transparent 58% 70%, #78f09b 70% 86%, transparent 86%),
                #e8f5df;
            }}
            .bottom-right .poster-two {{
              background:
                linear-gradient(20deg, transparent 0 20%, #68a8ff 20% 27%, transparent 27% 43%, #ff74d4 43% 50%, transparent 50%),
                #f0dfbd;
            }}
            .bottom-center .wall-light {{
              width: 52px;
              height: 62px;
              border-radius: 12px;
            }}
            .bottom-center .wall-light::before {{
              content: "?";
              left: 0;
              right: 0;
              top: -5px;
              height: auto;
              color: var(--accent);
              background: transparent;
              font-size: 44px;
              line-height: 58px;
              text-align: center;
              text-shadow: 0 0 15px var(--accent);
            }}
            .bottom-center .wall-light::after {{ display: none; }}
            .shelf {{
              position: absolute;
              left: 24px;
              top: 36px;
              width: 136px;
              height: 62px;
              border-bottom: 9px solid #5b3222;
              box-shadow: 0 6px 0 rgba(0,0,0,.16);
            }}
            .shelf span {{
              display: inline-block;
              width: 24px;
              height: 38px;
              margin: 14px 4px 0;
              background: linear-gradient(#e2b65d, #a96d36);
              border: 3px solid #2f2028;
            }}
            .shelf b {{
              display: inline-block;
              width: 34px;
              height: 25px;
              margin-left: 4px;
              background: var(--accent);
              border: 3px solid #2f2028;
              box-shadow: inset 0 -6px 0 rgba(0,0,0,.18);
            }}
            .plant {{
              position: absolute;
              left: 22px;
              bottom: 48px;
              width: 52px;
              height: 72px;
            }}
            .plant i {{
              position: absolute;
              bottom: 22px;
              width: 24px;
              height: 42px;
              background: #43ce61;
              border: 3px solid #1b3922;
              border-radius: 24px 24px 4px 24px;
              transform-origin: bottom center;
            }}
            .plant i:nth-child(1) {{ left: 7px; transform: rotate(-34deg); }}
            .plant i:nth-child(2) {{ left: 17px; transform: rotate(4deg); background: #62e978; }}
            .plant i:nth-child(3) {{ left: 27px; transform: rotate(31deg); }}
            .plant b {{
              position: absolute;
              left: 12px;
              bottom: 0;
              width: 30px;
              height: 28px;
              background: #91502b;
              border: 4px solid #2f2028;
              box-shadow: inset 0 -7px 0 rgba(0,0,0,.18);
            }}
            .cabinet {{
              position: absolute;
              right: 28px;
              bottom: 28px;
              width: 62px;
              height: 88px;
              background: #7a4328;
              border: 5px solid #2f2028;
              box-shadow: inset 0 -8px 0 rgba(0,0,0,.2);
            }}
            .cabinet span {{
              display: block;
              height: 36px;
              border-bottom: 4px solid #2f2028;
            }}
            .cabinet span::after {{
              content: "";
              display: block;
              width: 10px;
              height: 5px;
              margin: 16px auto 0;
              background: #f2c15c;
            }}
            .desk {{
              position: absolute;
              left: 21%;
              bottom: 35px;
              width: 53%;
              height: 78px;
              background: linear-gradient(#9b5c31, #6c3925);
              border: 6px solid #2f2028;
              box-shadow:
                inset 0 -12px 0 rgba(0,0,0,.2),
                0 8px 0 rgba(0,0,0,.16);
            }}
            .desk::before, .desk::after {{
              content: "";
              position: absolute;
              bottom: -40px;
              width: 15px;
              height: 38px;
              background: #4a2a22;
              border: 4px solid #2f2028;
            }}
            .desk::before {{ left: 18px; }}
            .desk::after {{ right: 18px; }}
            .coffee {{
              position: absolute;
              right: 18px;
              bottom: 28px;
              width: 18px;
              height: 22px;
              background: #f3e0b3;
              border: 3px solid #2f2028;
            }}
            .coffee::after {{
              content: "";
              position: absolute;
              right: -9px;
              top: 5px;
              width: 8px;
              height: 8px;
              border: 3px solid #2f2028;
              border-left: 0;
            }}
            .monitor {{
              position: absolute;
              left: 42%;
              bottom: 54px;
              width: 78px;
              height: 54px;
              background: #101827;
              border: 6px solid #2f2028;
              box-shadow: 0 6px 0 rgba(0,0,0,.22);
            }}
            .side-monitor {{
              position: absolute;
              left: 72%;
              bottom: 58px;
              width: 54px;
              height: 44px;
              background: #101827;
              border: 5px solid #2f2028;
              transform: rotate(4deg);
            }}
            .monitor span, .side-monitor span {{
              display: block;
              width: 100%;
              height: 100%;
              background:
                linear-gradient(90deg, transparent 0 22%, rgba(255,255,255,.12) 22% 25%, transparent 25%),
                repeating-linear-gradient(0deg, var(--accent) 0 3px, transparent 3px 9px);
              opacity: .85;
            }}
            .keyboard {{
              position: absolute;
              left: 43%;
              bottom: 13px;
              width: 94px;
              height: 16px;
              background: #1a2130;
              border: 3px solid #2f2028;
            }}
            .chair {{
              position: absolute;
              left: 34%;
              bottom: 50px;
              width: 58px;
              height: 74px;
              background: #1b2235;
              border: 5px solid #2f2028;
              border-radius: 16px 16px 8px 8px;
              box-shadow: inset 0 -12px 0 rgba(255,255,255,.05);
            }}
            .avatar {{
              position: absolute;
              left: 34%;
              bottom: 92px;
              width: 82px;
              height: 124px;
              animation: idle-bob 1.6s steps(2) infinite;
              filter: drop-shadow(0 10px 0 rgba(0,0,0,.22));
            }}
            .hair {{
              position: absolute;
              left: 16px;
              top: 1px;
              width: 50px;
              height: 34px;
              background: var(--hair);
              border: 4px solid #2a1b22;
              border-radius: 18px 18px 9px 9px;
              z-index: 3;
              box-shadow:
                -9px 8px 0 var(--hair),
                8px 7px 0 var(--hair),
                inset 0 -7px 0 rgba(0,0,0,.16);
            }}
            .head {{
              position: absolute;
              left: 18px;
              top: 18px;
              width: 47px;
              height: 43px;
              background: #f0b17a;
              border: 4px solid #2a1b22;
              border-radius: 14px 14px 10px 10px;
              z-index: 2;
              box-shadow: inset -5px -5px 0 rgba(136,72,52,.16);
            }}
            .eye-left, .eye-right {{
              position: absolute;
              top: 17px;
              width: 5px;
              height: 5px;
              background: #24171d;
            }}
            .eye-left {{ left: 12px; }}
            .eye-right {{ right: 12px; }}
            .mouth {{
              position: absolute;
              left: 20px;
              bottom: 9px;
              width: 10px;
              height: 4px;
              background: #9b443c;
            }}
            .neck {{
              position: absolute;
              left: 34px;
              top: 55px;
              width: 16px;
              height: 14px;
              background: #d98d65;
              border-left: 4px solid #2a1b22;
              border-right: 4px solid #2a1b22;
              z-index: 1;
            }}
            .torso {{
              position: absolute;
              left: 17px;
              top: 66px;
              width: 50px;
              height: 45px;
              background:
                linear-gradient(90deg, rgba(255,255,255,.18) 0 12px, transparent 12px),
                var(--shirt);
              border: 4px solid #2a1b22;
              border-radius: 13px 13px 6px 6px;
              box-shadow: inset 0 -9px 0 rgba(0,0,0,.18);
            }}
            .torso::before {{
              content: "";
              position: absolute;
              left: 20px;
              top: 4px;
              height: 34px;
              border-left: 4px solid rgba(42,27,34,.28);
            }}
            .arm {{
              position: absolute;
              top: 72px;
              width: 18px;
              height: 42px;
              background: var(--shirt);
              border: 4px solid #2a1b22;
              border-radius: 10px;
              transform-origin: top center;
            }}
            .arm-left {{ left: 5px; transform: rotate(16deg); }}
            .arm-right {{ right: 5px; transform: rotate(-18deg); animation: type-arm 1s steps(2) infinite; }}
            .leg {{
              position: absolute;
              top: 105px;
              width: 19px;
              height: 25px;
              background: #23324f;
              border: 4px solid #2a1b22;
              border-radius: 5px 5px 9px 9px;
            }}
            .leg-left {{ left: 23px; transform: rotate(8deg); }}
            .leg-right {{ right: 22px; transform: rotate(-7deg); }}
            .avatar-router .hair {{
              border-radius: 14px 18px 8px 12px;
              box-shadow: -8px 6px 0 var(--hair), 12px 10px 0 #3e1d14, inset 0 -7px 0 rgba(0,0,0,.2);
            }}
            .avatar-router::before {{
              content: "";
              position: absolute;
              left: 27px;
              top: -15px;
              width: 28px;
              height: 20px;
              background: #ffd15a;
              border: 4px solid #2a1b22;
              clip-path: polygon(0 100%, 12% 28%, 35% 70%, 50% 0, 67% 70%, 88% 28%, 100% 100%);
              z-index: 5;
            }}
            .avatar-multi .head::after {{
              content: "";
              position: absolute;
              left: 8px;
              right: 8px;
              top: 14px;
              height: 12px;
              border: 3px solid #123459;
              border-left-width: 4px;
              border-right-width: 4px;
              border-radius: 8px;
            }}
            .avatar-ardida .hair {{
              width: 58px;
              left: 11px;
              height: 42px;
              border-radius: 22px 22px 12px 12px;
              box-shadow: -12px 18px 0 var(--hair), 12px 18px 0 var(--hair), inset 0 -8px 0 rgba(0,0,0,.16);
            }}
            .avatar-prpagyda .hair {{
              border-radius: 18px 18px 18px 9px;
              box-shadow: -10px 12px 0 #0d756c, 11px 9px 0 var(--hair), inset 0 -7px 0 rgba(0,0,0,.16);
            }}
            .avatar-prjimenezda .hair {{
              background: #2d1c1c;
              box-shadow: -9px 7px 0 #2d1c1c, 8px 8px 0 #2d1c1c, inset 0 -7px 0 rgba(0,0,0,.2);
            }}
            .avatar-prjimenezda .head::after {{
              content: "";
              position: absolute;
              left: 0;
              right: 0;
              top: -12px;
              height: 12px;
              border: 4px solid #2a1b22;
              border-bottom: 0;
              background: #2f3648;
              border-radius: 18px 18px 0 0;
            }}
            .agent-label {{
              position: absolute;
              left: 16px;
              right: 16px;
              bottom: 12px;
              display: grid;
              gap: 2px;
              padding: 8px 10px;
              background: rgba(20,17,29,.82);
              border: 3px solid rgba(255,255,255,.14);
            }}
            .agent-label strong {{ font-size: 14px; }}
            .agent-label small {{ color: #d9c7ad; }}
            .packet {{
              position: absolute;
              z-index: 5;
              left: 50%;
              top: 50%;
              width: 34px;
              height: 25px;
              border: 4px solid #231823;
              background: #fff4d8;
              box-shadow: 0 0 24px var(--cyan);
              opacity: 0;
            }}
            .packet::before {{
              content: "";
              position: absolute;
              left: -22px;
              top: 5px;
              width: 14px;
              height: 8px;
              background: var(--beam, var(--cyan));
              box-shadow: -18px 0 0 var(--beam, var(--cyan)), -34px 0 0 rgba(255,255,255,.65);
            }}
            .packet::after {{
              content: "";
              position: absolute;
              left: 8px;
              bottom: -10px;
              border: 6px solid transparent;
              border-top-color: #231823;
            }}
            .route-to-router {{ --target-x: 18%; --target-y: 18%; --beam: var(--mint); }}
            .route-to-multi {{ --target-x: 82%; --target-y: 18%; --beam: var(--blue); }}
            .route-to-ardida {{ --target-x: 18%; --target-y: 76%; --beam: var(--pink); }}
            .route-to-prpagyda {{ --target-x: 82%; --target-y: 76%; --beam: var(--cyan); }}
            .route-to-prjimenezda {{ --target-x: 50%; --target-y: 82%; --beam: var(--amber); }}
            .scene:not(.idle) .packet {{
              animation: fly-message 2.4s ease-in-out infinite;
            }}
            .beam {{
              position: absolute;
              z-index: 1;
              inset: 0;
              pointer-events: none;
            }}
            .beam::before {{
              content: "";
              position: absolute;
              left: 50%;
              top: 50%;
              width: 240px;
              height: 0;
              border-top: 6px dashed var(--beam, var(--cyan));
              transform-origin: left center;
              opacity: .8;
              animation: beam-pulse 1.1s linear infinite;
              display: none;
            }}
            .route-to-router .beam::before {{ display: block; width: 430px; transform: rotate(214deg); }}
            .route-to-multi .beam::before {{ display: block; width: 430px; transform: rotate(-34deg); }}
            .route-to-ardida .beam::before {{ display: block; width: 440px; transform: rotate(146deg); }}
            .route-to-prpagyda .beam::before {{ display: block; width: 440px; transform: rotate(34deg); }}
            .route-to-prjimenezda .beam::before {{ display: block; width: 245px; transform: rotate(90deg); }}
            .route-to-router .avatar-router,
            .route-to-multi .avatar-multi,
            .route-to-ardida .avatar-ardida,
            .route-to-prpagyda .avatar-prpagyda,
            .route-to-prjimenezda .avatar-prjimenezda {{
              animation: receive-message 1.1s steps(2) infinite;
            }}
            .route-to-router .top-left,
            .route-to-multi .top-right,
            .route-to-ardida .bottom-left,
            .route-to-prpagyda .bottom-right,
            .route-to-prjimenezda .bottom-center {{
              box-shadow:
                inset 0 0 0 5px rgba(255,255,255,.12),
                inset 0 -68px 0 rgba(83,45,29,.38),
                inset 0 0 64px rgba(255,255,255,.08),
                0 14px 0 #261823,
                0 0 34px var(--beam);
            }}
            @keyframes fly-message {{
              0% {{ left: 50%; top: 50%; opacity: 0; transform: translate(-50%, -50%) scale(.7); }}
              15% {{ opacity: 1; }}
              75% {{ left: var(--target-x); top: var(--target-y); opacity: 1; transform: translate(-50%, -50%) scale(1.05); }}
              100% {{ left: var(--target-x); top: var(--target-y); opacity: 0; transform: translate(-50%, -50%) scale(.8); }}
            }}
            @keyframes beam-pulse {{
              from {{ filter: drop-shadow(0 0 2px var(--beam)); opacity: .35; }}
              50% {{ filter: drop-shadow(0 0 10px var(--beam)); opacity: 1; }}
              to {{ filter: drop-shadow(0 0 2px var(--beam)); opacity: .35; }}
            }}
            .monitor span, .side-monitor span {{
              animation: screen-flicker 1.8s steps(3) infinite;
            }}
            @keyframes idle-bob {{
              0%, 100% {{ transform: translateY(0); }}
              50% {{ transform: translateY(-4px); }}
            }}
            @keyframes type-arm {{
              0%, 100% {{ transform: rotate(-18deg) translateY(0); }}
              50% {{ transform: rotate(-8deg) translateY(4px); }}
            }}
            @keyframes receive-message {{
              0%, 100% {{ transform: translateY(0) scale(1); filter: drop-shadow(0 10px 0 rgba(0,0,0,.22)); }}
              50% {{ transform: translateY(-8px) scale(1.05); filter: drop-shadow(0 10px 0 rgba(0,0,0,.22)) drop-shadow(0 0 14px var(--accent)); }}
            }}
            @keyframes screen-flicker {{
              0%, 100% {{ opacity: .72; transform: translateY(0); }}
              50% {{ opacity: 1; transform: translateY(1px); }}
            }}
            @keyframes leaf-sway {{
              0%, 100% {{ filter: brightness(1); }}
              50% {{ filter: brightness(1.2); }}
            }}
            @keyframes sign-blink {{
              0%, 100% {{ filter: brightness(.95); transform: translateY(0); }}
              50% {{ filter: brightness(1.35); transform: translateY(-2px); }}
            }}
            .side-panel {{
              display: grid;
              grid-template-columns: 1.2fr .8fr;
              gap: 14px;
              margin-top: 16px;
            }}
            .panel {{
              background: rgba(22,19,34,.92);
              border: 5px solid #4b3340;
              padding: 14px;
              box-shadow: 0 8px 0 #201620;
            }}
            .panel h2 {{ font-size: 18px; margin-bottom: 12px; }}
            .event {{
              border: 3px solid rgba(255,255,255,.13);
              background: rgba(255,255,255,.06);
              padding: 10px;
              margin: 8px 0;
            }}
            .event pre {{
              white-space: pre-wrap;
              margin: 8px 0 0;
              color: #ffe8b8;
              font-family: "Courier New", monospace;
              font-size: 13px;
            }}
            code {{
              color: #120d14;
              background: #f4d27d;
              padding: 2px 5px;
            }}
            .muted {{ color: #c4b69f; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
            th, td {{ padding: 8px; border-bottom: 2px solid rgba(255,255,255,.12); text-align: left; }}
            @media (max-width: 980px) {{
              .shell {{ padding: 12px; }}
              .topbar {{ align-items: flex-start; flex-direction: column; }}
              .side-panel {{ grid-template-columns: 1fr; }}
            }}
            .stage {{
              display: block;
              height: 900px;
              min-height: 900px;
              background: #07091b;
              border: 10px solid #4b3340;
              box-shadow: inset 0 0 0 6px rgba(255,255,255,.06), 0 14px 0 #201620;
              overflow: hidden;
            }}
            .office-canvas {{
              position: absolute;
              inset: 0;
              width: 100%;
              height: 100%;
              image-rendering: pixelated;
            }}
            .floor,
            .lobby-plant,
            .sofa,
            .wayfinder,
            .beam,
            .packet,
            .room {{
              display: none;
            }}
            .hub {{
              position: absolute;
              left: 50%;
              bottom: 24px;
              transform: translateX(-50%);
              width: 430px;
              z-index: 8;
              grid-column: auto;
              grid-row: auto;
              opacity: .96;
            }}
          </style>
        </head>
        <body>
          <main class="shell">
            <header class="topbar">
              <div>
                <h1>Telegram Agent Router</h1>
                <p>Director bot: <code>{escape(service.router_agent.telegram)}</code></p>
              </div>
              <p class="status">{status}</p>
            </header>
            {error}
            <section class="stage scene {scene_route}">
              <canvas id="office-canvas" class="office-canvas" width="1120" height="900"></canvas>
              <div class="floor"></div>
              <div class="lobby-plant"><i></i><i></i><i></i><i></i><b></b></div>
              <div class="sofa sofa-left"></div>
              <div class="sofa sofa-right"></div>
              <div class="wayfinder sign-router">A</div>
              <div class="wayfinder sign-multi">B</div>
              <div class="wayfinder sign-ardida">C</div>
              <div class="wayfinder sign-prpagyda">D</div>
              <div class="wayfinder sign-prjimenezda">E</div>
              <div class="beam"></div>
              <div class="packet"></div>
              {rooms}
              <section class="hub">
                <h2>Consola central</h2>
                <form action="/send" method="post">
                  <textarea name="message" placeholder="Escribe una orden para el bot director"></textarea>
                  <button type="submit">Enviar al director</button>
                </form>
              </section>
            </section>
            <script>
              window.__SCENE_STATE__ = {scene_state_json};
              (() => {{
                const canvas = document.getElementById("office-canvas");
                const ctx = canvas.getContext("2d");
                ctx.imageSmoothingEnabled = false;
                const W = 1120;
                const H = 900;
                const state = window.__SCENE_STATE__;
                const rooms = {{
                  router: {{ x: 35, y: 35, w: 350, h: 250, color: "#3c5f34", accent: "#78f09b", hair: "#6b351d", shirt: "#49d069", skin: "#f0b17a", name: "Director", emoji: "A" }},
                  multi: {{ x: 735, y: 35, w: 350, h: 250, color: "#263e6f", accent: "#68a8ff", hair: "#1687ff", shirt: "#3f8cff", skin: "#f0b17a", name: "Codigo", emoji: "B" }},
                  ardida: {{ x: 35, y: 590, w: 350, h: 250, color: "#66345f", accent: "#ff74d4", hair: "#ff5fdc", shirt: "#ff65c8", skin: "#f0b17a", name: "Creativo", emoji: "C" }},
                  prpagyda: {{ x: 735, y: 590, w: 350, h: 250, color: "#245f5d", accent: "#52e6f2", hair: "#14b9a8", shirt: "#22d1a5", skin: "#f0b17a", name: "Analitica", emoji: "D" }},
                  prjimenezda: {{ x: 385, y: 632, w: 350, h: 220, color: "#76582a", accent: "#ffd15a", hair: "#2b191b", shirt: "#ffc52f", skin: "#b9764f", name: "Soporte", emoji: "E" }},
                }};
                const agentNames = Object.fromEntries(state.agents.map((agent) => [agent.id, agent.telegram]));
                let lastRoute = state.routeTarget || "";
                let routeStarted = performance.now();

                function px(x, y, w, h, fill, stroke = "#2a1b22", sw = 0) {{
                  ctx.fillStyle = fill;
                  ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
                  if (sw) {{
                    ctx.strokeStyle = stroke;
                    ctx.lineWidth = sw;
                    ctx.strokeRect(Math.round(x) + sw / 2, Math.round(y) + sw / 2, Math.round(w) - sw, Math.round(h) - sw);
                  }}
                }}

                function text(label, x, y, size = 14, color = "#f7ead5", align = "left") {{
                  ctx.fillStyle = color;
                  ctx.font = `bold ${{size}}px Trebuchet MS, Verdana, sans-serif`;
                  ctx.textAlign = align;
                  ctx.textBaseline = "top";
                  ctx.fillText(label, x, y);
                }}

                function noise(x, y, seed = 1) {{
                  const value = Math.sin(x * 12.9898 + y * 78.233 + seed * 37.719) * 43758.5453;
                  return value - Math.floor(value);
                }}

                function materialRect(x, y, w, h, base, seed = 1, density = 10) {{
                  px(x, y, w, h, base);
                  for (let yy = y; yy < y + h; yy += density) {{
                    for (let xx = x; xx < x + w; xx += density) {{
                      const n = noise(Math.floor(xx / density), Math.floor(yy / density), seed);
                      if (n > .54) px(xx, yy, density, density, "rgba(255,255,255,.045)");
                      if (n < .18) px(xx, yy, density, density, "rgba(0,0,0,.075)");
                    }}
                  }}
                }}

                function softShadow(x, y, w, h, alpha = .22) {{
                  const shadow = ctx.createRadialGradient(x, y, 4, x, y, Math.max(w, h));
                  shadow.addColorStop(0, `rgba(0,0,0,${{alpha}})`);
                  shadow.addColorStop(1, "rgba(0,0,0,0)");
                  ctx.fillStyle = shadow;
                  ctx.beginPath();
                  ctx.ellipse(x, y, w, h, 0, 0, Math.PI * 2);
                  ctx.fill();
                }}

                function radialLight(x, y, r, color, alpha = .22) {{
                  const light = ctx.createRadialGradient(x, y, 0, x, y, r);
                  light.addColorStop(0, color.replace(")", `, ${{alpha}})`).replace("rgb", "rgba"));
                  light.addColorStop(1, "rgba(0,0,0,0)");
                  ctx.fillStyle = light;
                  ctx.fillRect(x - r, y - r, r * 2, r * 2);
                }}

                function drawVignette() {{
                  const vignette = ctx.createRadialGradient(W / 2, H / 2, 240, W / 2, H / 2, 720);
                  vignette.addColorStop(0, "rgba(0,0,0,0)");
                  vignette.addColorStop(1, "rgba(0,0,0,.62)");
                  ctx.fillStyle = vignette;
                  ctx.fillRect(0, 0, W, H);
                }}

                function drawBackground() {{
                  const bg = ctx.createLinearGradient(0, 0, W, H);
                  bg.addColorStop(0, "#07091b");
                  bg.addColorStop(.5, "#11142f");
                  bg.addColorStop(1, "#040514");
                  px(0, 0, W, H, bg);
                  radialLight(W / 2, 410, 420, "rgb(82, 230, 242)", .09);
                  radialLight(170, 140, 240, "rgb(120, 240, 155)", .08);
                  radialLight(950, 160, 260, "rgb(104, 168, 255)", .09);
                  radialLight(175, 735, 240, "rgb(255, 116, 212)", .08);
                  radialLight(890, 720, 260, "rgb(82, 230, 242)", .08);
                  for (let i = 0; i < 190; i += 1) {{
                    const x = (i * 97) % W;
                    const y = (i * 53) % H;
                    const size = i % 7 === 0 ? 3 : 2;
                    px(x, y, size, size, i % 5 === 0 ? "rgba(82,230,242,.2)" : "rgba(255,255,255,.14)");
                  }}
                  for (let y = 0; y < H; y += 6) {{
                    px(0, y, W, 1, "rgba(255,255,255,.025)");
                  }}
                }}

                function drawFloor() {{
                  softShadow(W / 2, 624, 390, 70, .24);
                  px(305, 248, 510, 360, "#4d3440", "#2a1b22", 8);
                  for (let y = 260; y < 594; y += 28) {{
                    for (let x = 318; x < 805; x += 64) {{
                      const base = (x + y) % 3 ? "#a76031" : "#92502b";
                      materialRect(x, y, 62, 26, base, x + y, 8);
                      px(x, y, 62, 2, "rgba(255,230,170,.08)");
                      px(x, y + 24, 62, 2, "rgba(0,0,0,.13)");
                    }}
                  }}
                  for (let i = 0; i < 6; i += 1) {{
                    ctx.strokeStyle = i % 2 ? "rgba(82,230,242,.22)" : "rgba(255,209,90,.18)";
                    ctx.lineWidth = 4;
                    ctx.beginPath();
                    ctx.ellipse(W / 2, 414, 118 + i * 13, 68 + i * 8, 0, 0, Math.PI * 2);
                    ctx.stroke();
                  }}
                  px(455, 360, 210, 112, "rgba(255,209,90,.18)", "#4d3440", 7);
                  materialRect(505, 384, 110, 65, "rgba(82,230,242,.14)", 19, 7);
                  px(505, 384, 110, 65, "rgba(82,230,242,.06)", "#5f3f4a", 5);
                }}

                function drawRoom(id, room, now) {{
                  const glow = lastRoute === id;
                  softShadow(room.x + room.w / 2, room.y + room.h + 10, room.w / 1.8, 32, .28);
                  px(room.x, room.y, room.w, room.h, "#4b3340", "#211722", 7);
                  const wallGradient = ctx.createLinearGradient(room.x, room.y, room.x, room.y + room.h);
                  wallGradient.addColorStop(0, shade(room.color, 16));
                  wallGradient.addColorStop(.62, room.color);
                  wallGradient.addColorStop(1, shade(room.color, -30));
                  materialRect(room.x + 10, room.y + 10, room.w - 20, room.h - 20, wallGradient, room.x + room.y, 12);
                  px(room.x + 14, room.y + 14, room.w - 28, 4, "rgba(255,255,255,.12)");
                  px(room.x + 16, room.y + room.h - 76, room.w - 32, 60, "rgba(122,67,40,.72)");
                  for (let x = room.x + 22; x < room.x + room.w - 30; x += 44) {{
                    materialRect(x, room.y + room.h - 70, 41, 56, x % 2 ? "#7d4529" : "#8f512d", x, 9);
                    px(x, room.y + room.h - 70, 41, 2, "rgba(255,220,160,.09)");
                  }}
                  radialLight(room.x + room.w - 56, room.y + 54, 130, room.accent, .18);
                  if (glow) {{
                    ctx.shadowColor = room.accent;
                    ctx.shadowBlur = 24;
                    px(room.x + 14, room.y + 14, room.w - 28, room.h - 28, "rgba(255,255,255,.05)", room.accent, 4);
                    ctx.shadowBlur = 0;
                  }}
                  drawProps(room, id, now);
                  drawSprite(room.x + room.w * .46, room.y + room.h - 126, room, id, now, glow);
                  px(room.x + 18, room.y + room.h - 42, room.w - 36, 28, "rgba(15,12,23,.82)", "rgba(255,255,255,.16)", 3);
                  text(agentNames[id] || id, room.x + 28, room.y + room.h - 36, 13, "#f7ead5");
                  text(id, room.x + room.w - 28, room.y + room.h - 36, 13, room.accent, "right");
                }}

                function drawProps(room, id, now) {{
                  const flicker = Math.floor(now / 220) % 2;
                  px(room.x + 26, room.y + 45, 112, 12, "#5b3222", "#2a1b22", 3);
                  px(room.x + 34, room.y + 18, 24, 34, "#d59b42", "#2a1b22", 3);
                  px(room.x + 66, room.y + 18, 24, 34, "#68a8ff", "#2a1b22", 3);
                  px(room.x + 100, room.y + 24, 28, 26, room.accent, "#2a1b22", 3);
                  px(room.x + room.w - 82, room.y + 32, 50, 44, "#10182a", "#2a1b22", 4);
                  px(room.x + room.w - 70, room.y + 48, 26, 8, room.accent);
                  px(room.x + 168, room.y + 28, 52, 42, "#f0dfbd", "#2a1b22", 4);
                  px(room.x + 180, room.y + 40, 28, 5, room.accent);
                  px(room.x + 180, room.y + 52, 18, 5, "#e85b75");
                  px(room.x + 30, room.y + room.h - 108, 36, 42, "#91502b", "#2a1b22", 4);
                  px(room.x + 22, room.y + room.h - 142, 20, 42, "#43ce61", "#1b3922", 3);
                  px(room.x + 42, room.y + room.h - 150, 20, 50, "#62e978", "#1b3922", 3);
                  px(room.x + room.w - 74, room.y + room.h - 112, 48, 74, "#7a4328", "#2a1b22", 4);
                  px(room.x + 86, room.y + room.h - 86, 184, 58, "#8c4d2d", "#2a1b22", 5);
                  px(room.x + 190, room.y + room.h - 140, 72, 48, "#101827", "#2a1b22", 5);
                  px(room.x + 200, room.y + room.h - 130, 52, 28, flicker ? room.accent : "#20304d");
                  px(room.x + 266, room.y + room.h - 132, 48, 38, "#101827", "#2a1b22", 4);
                  px(room.x + 274, room.y + room.h - 124, 30, 20, flicker ? "#f7ead5" : room.accent);
                  px(room.x + 196, room.y + room.h - 62, 92, 14, "#1a2130", "#2a1b22", 3);
                  if (id === "router") drawCrown(room.x + 194, room.y + 80);
                  if (id === "multi") drawCodeBars(room.x + 172, room.y + 82, room.accent);
                  if (id === "ardida") drawPalette(room.x + 180, room.y + 82);
                  if (id === "prpagyda") drawChart(room.x + 176, room.y + 82);
                  if (id === "prjimenezda") drawQuestion(room.x + 184, room.y + 76, room.accent);
                }}

                function drawCrown(x, y) {{
                  px(x, y + 18, 44, 12, "#ffd15a", "#2a1b22", 3);
                  px(x + 4, y + 4, 8, 20, "#ffd15a", "#2a1b22", 3);
                  px(x + 18, y, 8, 24, "#ffd15a", "#2a1b22", 3);
                  px(x + 32, y + 4, 8, 20, "#ffd15a", "#2a1b22", 3);
                }}
                function drawCodeBars(x, y, color) {{
                  for (let i = 0; i < 5; i += 1) px(x, y + i * 9, 70 - i * 8, 4, i % 2 ? "#f7ead5" : color);
                }}
                function drawPalette(x, y) {{
                  px(x, y, 58, 38, "#f7ead5", "#2a1b22", 4);
                  px(x + 10, y + 8, 10, 10, "#ff74d4");
                  px(x + 26, y + 8, 10, 10, "#ffd15a");
                  px(x + 40, y + 18, 10, 10, "#68a8ff");
                }}
                function drawChart(x, y) {{
                  px(x, y, 64, 42, "#e8f5df", "#2a1b22", 4);
                  px(x + 10, y + 26, 8, 10, "#ff6f6f");
                  px(x + 26, y + 16, 8, 20, "#ffd15a");
                  px(x + 42, y + 8, 8, 28, "#78f09b");
                }}
                function drawQuestion(x, y, color) {{
                  text("?", x + 16, y - 8, 44, color);
                  px(x, y + 40, 62, 18, "#7a4328", "#2a1b22", 4);
                }}

                function drawSprite(x, y, p, id, now, active) {{
                  const bob = Math.floor(now / 260) % 2 ? -3 : 0;
                  if (active) ctx.shadowBlur = 16, ctx.shadowColor = p.accent;
                  const pants = id === "router" || id === "multi" ? "#2d2a37" : "#263148";
                  const shoe = id === "router" || id === "multi" ? "#2268bd" : p.accent;

                  px(x - 38, y + 112 + bob, 27, 12, "rgba(0,0,0,.24)");
                  px(x + 4, y + 112 + bob, 40, 12, "rgba(0,0,0,.24)");

                  px(x - 30, y + 76 + bob, 22, 42, pants, "#1a1420", 5);
                  px(x + 7, y + 76 + bob, 24, 42, pants, "#1a1420", 5);
                  px(x - 34, y + 112 + bob, 31, 14, shoe, "#1a1420", 4);
                  px(x + 9, y + 112 + bob, 39, 14, shoe, "#1a1420", 4);
                  px(x - 26, y + 116 + bob, 20, 4, "#f7ead5");
                  px(x + 20, y + 116 + bob, 22, 4, "#f7ead5");

                  px(x - 38, y + 50 + bob, 20, 48, p.shirt, "#1a1420", 5);
                  px(x + 32, y + 50 + bob, 19, 42, p.shirt, "#1a1420", 5);
                  px(x - 31, y + 42 + bob, 72, 56, p.shirt, "#1a1420", 5);
                  px(x - 23, y + 89 + bob, 56, 12, shade(p.shirt, -24), "#1a1420", 3);
                  px(x - 19, y + 52 + bob, 10, 28, "rgba(255,255,255,.16)");
                  px(x + 7, y + 49 + bob, 4, 44, p.accent);
                  px(x - 7, y + 58 + bob, 10, 12, p.accent);
                  px(x + 11, y + 58 + bob, 10, 12, p.accent);

                  px(x - 12, y + 31 + bob, 20, 17, "#d98d65", "#1a1420", 3);
                  px(x - 34, y + 4 + bob, 66, 47, p.skin, "#1a1420", 5);
                  drawHair(x, y + bob, p, id);
                  drawFace(x, y + bob, p, id);
                  drawHeadphones(x, y + bob, p, id);
                  drawLaptop(x + 38, y + 48 + bob, p, id);
                  ctx.shadowBlur = 0;
                }}

                function drawHair(x, y, p, id) {{
                  const hair = p.hair;
                  px(x - 40, y - 3, 25, 20, hair, "#1a1420", 4);
                  px(x - 31, y - 14, 25, 24, hair, "#1a1420", 4);
                  px(x - 12, y - 18, 31, 23, hair, "#1a1420", 4);
                  px(x + 12, y - 12, 28, 25, hair, "#1a1420", 4);
                  px(x - 36, y + 12, 16, 24, shade(hair, -28), "#1a1420", 3);
                  px(x + 24, y + 12, 12, 18, shade(hair, -18), "#1a1420", 3);
                  px(x - 20, y - 5, 38, 12, shade(hair, 22));
                  if (id === "ardida") px(x - 44, y + 18, 16, 44, hair, "#1a1420", 4);
                  if (id === "prjimenezda") px(x - 34, y - 20, 72, 12, "#2f3648", "#1a1420", 4);
                }}

                function drawFace(x, y, p, id) {{
                  px(x - 23, y + 23, 16, 15, "rgba(255,180,120,.22)");
                  px(x + 16, y + 23, 12, 14, "rgba(255,180,120,.18)");
                  px(x - 19, y + 25, 8, 8, "#f7ead5", "#1a1420", 2);
                  px(x + 7, y + 25, 8, 8, "#f7ead5", "#1a1420", 2);
                  px(x - 16, y + 27, 3, 4, "#24171d");
                  px(x + 10, y + 27, 3, 4, "#24171d");
                  px(x - 6, y + 38, 16, 4, "#9b443c");
                  if (id === "router" || id === "multi") {{
                    px(x - 23, y + 21, 22, 17, "rgba(120,190,255,.18)", "#111827", 3);
                    px(x + 3, y + 21, 22, 17, "rgba(120,190,255,.18)", "#111827", 3);
                    px(x - 1, y + 28, 5, 3, "#111827");
                  }}
                }}

                function drawHeadphones(x, y, p, id) {{
                  if (id === "prpagyda") return;
                  px(x - 44, y + 30, 18, 28, "#202432", "#111018", 4);
                  px(x + 28, y + 30, 18, 28, "#202432", "#111018", 4);
                  px(x - 39, y + 38, 8, 12, p.accent);
                  px(x + 33, y + 38, 8, 12, p.accent);
                  px(x - 29, y + 17, 60, 6, "#202432", "#111018", 3);
                }}

                function drawLaptop(x, y, p, id) {{
                  px(x, y, 48, 36, "#2d2a37", "#16121a", 4);
                  px(x + 7, y + 12, 12, 5, p.accent);
                  px(x + 24, y + 9, 5, 18, p.accent);
                  px(x - 26, y + 34, 55, 12, "#403b48", "#16121a", 3);
                  px(x - 19, y + 39, 20, 3, "#17131b");
                }}

                function shade(hex, amount) {{
                  const clean = hex.replace("#", "");
                  const n = parseInt(clean, 16);
                  const r = Math.max(0, Math.min(255, (n >> 16) + amount));
                  const g = Math.max(0, Math.min(255, ((n >> 8) & 255) + amount));
                  const b = Math.max(0, Math.min(255, (n & 255) + amount));
                  return `rgb(${{r}}, ${{g}}, ${{b}})`;
                }}

                function centerOf(id) {{
                  const r = rooms[id];
                  return r ? {{ x: r.x + r.w / 2, y: r.y + r.h / 2 }} : {{ x: W / 2, y: H / 2 }};
                }}

                function drawRoute(now) {{
                  if (!lastRoute || !rooms[lastRoute]) return;
                  const from = {{ x: W / 2, y: H / 2 }};
                  const to = centerOf(lastRoute);
                  const room = rooms[lastRoute];
                  const t = ((now - routeStarted) % 2200) / 2200;
                  const eased = t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
                  ctx.strokeStyle = room.accent;
                  ctx.lineWidth = 6;
                  ctx.setLineDash([18, 13]);
                  ctx.shadowColor = room.accent;
                  ctx.shadowBlur = 12;
                  ctx.beginPath();
                  ctx.moveTo(from.x, from.y);
                  ctx.lineTo(to.x, to.y);
                  ctx.stroke();
                  ctx.setLineDash([]);
                  const x = from.x + (to.x - from.x) * eased;
                  const y = from.y + (to.y - from.y) * eased;
                  px(x - 18, y - 12, 36, 24, "#fff4d8", "#2a1b22", 4);
                  px(x - 38, y - 3, 12, 6, room.accent);
                  px(x - 56, y - 3, 10, 6, "rgba(255,255,255,.7)");
                  ctx.shadowBlur = 0;
                }}

                function drawLoop(now) {{
                  drawBackground();
                  drawFloor();
                  Object.entries(rooms).forEach(([id, room]) => drawRoom(id, room, now));
                  drawRoute(now);
                  requestAnimationFrame(drawLoop);
                }}

                async function pollScene() {{
                  try {{
                    const response = await fetch("/scene-state");
                    const next = await response.json();
                    if ((next.routeTarget || "") !== lastRoute) {{
                      lastRoute = next.routeTarget || "";
                      routeStarted = performance.now();
                    }}
                  }} catch (error) {{
                    console.warn("scene poll failed", error);
                  }}
                }}

                requestAnimationFrame(drawLoop);
                window.setInterval(pollScene, 2500);
              }})();
            </script>
            <section class="side-panel">
              <div class="panel">
                <h2>Mensajes recientes</h2>
                {events}
              </div>
              <div class="panel">
                <h2>Agentes</h2>
                <table>
                  <thead><tr><th>ID</th><th>Telegram</th><th>Rol</th></tr></thead>
                  <tbody>{rows}</tbody>
                </table>
                <form action="/logout" method="post">
                  <button type="submit">Logout</button>
                </form>
              </div>
            </section>
          </main>
        </body>
        </html>
        """
    )


@app.post("/send")
async def send_order(
    request: Request,
    message: str = Form(...),
    service: TelegramRouterService = Depends(get_service),
):
    if not auth.is_authenticated(request):
        return RedirectResponse("/login", status_code=303)
    if message.strip():
        await service.send_owner_order(message.strip())
    return RedirectResponse("/", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(
        """
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8" />
          <title>Login</title>
          <style>
            body { font-family: ui-sans-serif, system-ui; margin: 40px; color: #161616; }
            form { max-width: 320px; display: grid; gap: 12px; }
            input, button { padding: 10px; font: inherit; }
          </style>
        </head>
        <body>
          <h1>Login</h1>
          <form action="/login" method="post">
            <input name="username" placeholder="Username" autocomplete="username" />
            <input name="password" placeholder="Password" type="password" autocomplete="current-password" />
            <button type="submit">Login</button>
          </form>
        </body>
        </html>
        """
    )


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    settings: Settings = Depends(get_settings),
):
    if auth.login(request, settings, username, password):
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/login", status_code=303)


@app.post("/logout")
async def logout_submit(request: Request):
    auth.logout(request)
    return RedirectResponse("/login", status_code=303)


@app.get("/health")
async def health(service: TelegramRouterService = Depends(get_service)):
    return {
        "telegram_started": service.state.started,
        "last_error": service.state.last_error,
        "agents": len(service.agents_config.agents),
    }


@app.get("/unity", response_class=HTMLResponse)
async def unity_page():
    if (unity_build_path / "index.html").exists():
        return HTMLResponse(
            """
            <!doctype html>
            <html>
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>Unity Lobby</title>
              <style>
                html, body { margin: 0; min-height: 100%; background: #050614; }
                iframe { width: 100vw; height: 100vh; border: 0; display: block; }
              </style>
            </head>
            <body>
              <iframe src="/unity-build/index.html"></iframe>
            </body>
            </html>
            """
        )

    return HTMLResponse(
        """
        <!doctype html>
        <html>
        <head><meta charset="utf-8" /><title>Unity Lobby</title></head>
        <body style="font-family: sans-serif; padding: 32px">
          <h1>Unity build not exported yet</h1>
          <p>Build WebGL from Unity into <code>web/unity-build</code>, then reload this page.</p>
        </body>
        </html>
        """
    )


@app.get("/scene-state")
async def scene_state(service: TelegramRouterService = Depends(get_service)):
    latest_event = service.state.events[0] if service.state.events else None
    route_target = latest_event.actor if latest_event and latest_event.direction == "outgoing" else ""
    if route_target not in service.agents_config.by_id:
        route_target = ""
    return {
        "routeTarget": route_target,
        "latestText": latest_event.text if latest_event else "",
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "telegram": agent.telegram,
                "kind": agent.kind,
                "role": agent.role,
            }
            for agent in service.agents_config.agents
        ],
        "events": [
            {
                "timestamp": event.timestamp,
                "direction": event.direction,
                "actor": event.actor,
                "text": event.text,
            }
            for event in service.state.events[:10]
        ],
    }
