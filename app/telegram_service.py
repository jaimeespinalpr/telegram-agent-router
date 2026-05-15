import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from telethon import TelegramClient, events
from telethon.tl.custom import Message

from app.agents import Agent, AgentsConfig, normalize_username
from app.router_protocol import parse_dispatches
from app.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class RouterEvent:
    timestamp: str
    direction: str
    actor: str
    text: str


@dataclass
class RuntimeState:
    started: bool = False
    last_error: str | None = None
    active_threads: dict[str, str] = field(default_factory=dict)
    events: list[RouterEvent] = field(default_factory=list)


class TelegramRouterService:
    def __init__(self, settings: Settings, agents_config: AgentsConfig):
        self.settings = settings
        self.agents_config = agents_config
        self.state = RuntimeState()
        self.client: TelegramClient | None = None
        self._lock = asyncio.Lock()

    @property
    def router_agent(self) -> Agent:
        agents = self.agents_config.by_id
        if self.settings.router_agent_id not in agents:
            raise ValueError(f"Router agent '{self.settings.router_agent_id}' is not configured.")
        return agents[self.settings.router_agent_id]

    async def start(self) -> None:
        async with self._lock:
            if self.state.started:
                return
            if self.settings.telegram_api_id is None or not self.settings.telegram_api_hash:
                raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH are required.")

            self.client = TelegramClient(
                self.settings.telegram_session_path,
                self.settings.telegram_api_id,
                self.settings.telegram_api_hash,
            )
            await self.client.start()
            self.client.add_event_handler(self._handle_message, events.NewMessage(incoming=True))
            self.state.started = True
            self.state.last_error = None
            logger.info("Telegram router started")

    async def stop(self) -> None:
        async with self._lock:
            if self.client:
                await self.client.disconnect()
            self.client = None
            self.state.started = False

    async def _handle_message(self, event: events.NewMessage.Event) -> None:
        try:
            if not self.client:
                return
            message: Message = event.message
            sender = await event.get_sender()
            sender_username = normalize_username(getattr(sender, "username", None))
            text = message.raw_text or ""
            if not text.strip():
                return

            router = self.router_agent
            router_username = normalize_username(router.telegram)
            self._record_event("incoming", sender_username or "unknown", text)

            if sender_username == router_username:
                await self._handle_router_reply(text)
                return

            agent = self.agents_config.by_telegram.get(sender_username)
            if agent and agent.id != router.id:
                await self._forward_agent_reply_to_router(agent, text)
                return

            if sender_username in {normalize_username(u) for u in self.agents_config.owner_usernames}:
                await self._send_to_agent(router, text)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to route Telegram message")
            self.state.last_error = str(exc)

    async def _handle_router_reply(self, text: str) -> None:
        dispatches = parse_dispatches(text)
        if not dispatches:
            logger.info("Router reply did not contain dispatch instructions")
            return

        agents = self.agents_config.by_id
        for dispatch in dispatches:
            target = agents.get(dispatch.to)
            if not target:
                logger.warning("Unknown target agent: %s", dispatch.to)
                continue
            await self._send_to_agent(target, dispatch.message)
            self.state.active_threads[target.id] = dispatch.message[:200]

    async def _forward_agent_reply_to_router(self, agent: Agent, text: str) -> None:
        router = self.router_agent
        forwarded = f"[from:{agent.id}]\n{text}"
        await self._send_to_agent(router, forwarded)

    async def send_owner_order(self, text: str) -> None:
        await self._send_to_agent(self.router_agent, text)

    async def _send_to_agent(self, agent: Agent, text: str) -> None:
        if not self.client:
            raise RuntimeError("Telegram client is not started.")
        await self.client.send_message(agent.telegram, text)
        self._record_event("outgoing", agent.id, text)

    def _record_event(self, direction: str, actor: str, text: str) -> None:
        self.state.events.insert(
            0,
            RouterEvent(
                timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
                direction=direction,
                actor=actor,
                text=text[:1000],
            ),
        )
        del self.state.events[100:]
