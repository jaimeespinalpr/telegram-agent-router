import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from telethon import TelegramClient, events
from telethon.tl.custom import Message

from app.agents import Agent, AgentsConfig, normalize_username
from app.router_protocol import parse_dispatches
from app.settings import Settings

logger = logging.getLogger(__name__)


class CommunicationMode(StrEnum):
    ACTIVE = "ACTIVE_MODE"
    RECEIVE_ONLY = "RECEIVE_ONLY_MODE"
    PAUSED = "PAUSED_MODE"
    ERROR = "ERROR_MODE"


@dataclass
class RouterEvent:
    timestamp: str
    direction: str
    actor: str
    text: str


@dataclass
class RuntimeState:
    started: bool = False
    mode: CommunicationMode = CommunicationMode.ACTIVE
    last_error: str | None = None
    active_threads: dict[str, str] = field(default_factory=dict)
    agent_status: dict[str, str] = field(default_factory=dict)
    events: list[RouterEvent] = field(default_factory=list)


class TelegramRouterService:
    def __init__(self, settings: Settings, agents_config: AgentsConfig):
        self.settings = settings
        self.agents_config = agents_config
        self.state = RuntimeState()
        self.state.agent_status = {agent.id: "idle" for agent in agents_config.agents}
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

    def set_mode(self, mode: CommunicationMode) -> None:
        self.state.mode = mode
        status = "paused" if mode in {CommunicationMode.RECEIVE_ONLY, CommunicationMode.PAUSED} else "idle"
        for agent in self.agents_config.agents:
            self.state.agent_status[agent.id] = status
        self._record_event("system", mode.value, f"System mode changed to {mode.value}")

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
                await self._handle_agent_reply(agent, text)
                return

            if sender_username in {normalize_username(u) for u in self.agents_config.owner_usernames}:
                await self._route_owner_message(text)
                return

            await self._route_external_message(sender_username or "unknown", text)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to route Telegram message")
            self.state.last_error = str(exc)
            self.set_mode(CommunicationMode.ERROR)

    async def _handle_router_reply(self, text: str) -> None:
        self._set_agent_status(self.router_agent.id, "responding")
        dispatches = parse_dispatches(text)
        if not dispatches:
            logger.info("Router reply did not contain dispatch instructions")
            self._set_agent_status(self.router_agent.id, "done")
            return

        agents = self.agents_config.by_id
        for dispatch in dispatches:
            target = agents.get(dispatch.to)
            if not target:
                logger.warning("Unknown target agent: %s", dispatch.to)
                continue
            await self._send_to_agent(target, dispatch.message)
            self.state.active_threads[target.id] = dispatch.message[:200]
        self._set_agent_status(self.router_agent.id, "done")

    async def _handle_agent_reply(self, agent: Agent, text: str) -> None:
        self._set_agent_status(agent.id, "responding")
        dispatch_target = self.detect_target_agent(text, exclude_agent_id=agent.id)
        if dispatch_target and dispatch_target.id != self.router_agent.id:
            internal = f"[internal:{agent.id}->{dispatch_target.id}]\n{text}"
            self._record_event("internal", dispatch_target.id, internal)
            await self._send_to_agent(dispatch_target, text)
            return

        forwarded = f"[from:{agent.id}]\n{text}"
        await self._send_to_agent(self.router_agent, forwarded)

    async def send_owner_order(self, text: str) -> None:
        await self._route_owner_message(text)

    async def _route_owner_message(self, text: str) -> None:
        target = self.detect_target_agent(text) or self.router_agent
        await self._send_to_agent(target, text)

    async def _route_external_message(self, sender_username: str, text: str) -> None:
        target = self.detect_target_agent(text)
        if not target:
            logger.info("External message did not mention a configured agent")
            return

        forwarded = f"[from:{sender_username} -> {target.id}]\n{text}"
        await self._send_to_agent(target, forwarded)

    def detect_target_agent(self, text: str, exclude_agent_id: str | None = None) -> Agent | None:
        normalized_text = normalize_for_match(text)
        agents = [agent for agent in self.agents_config.agents if agent.id != exclude_agent_id]

        for agent in agents:
            tokens = [agent.telegram, agent.id, agent.name, *agent.aliases]
            if any(normalize_for_match(token) in normalized_text for token in tokens if token):
                return agent

        scored: list[tuple[int, Agent]] = []
        for agent in agents:
            score = sum(
                1 for keyword in agent.keywords if normalize_for_match(keyword) in normalized_text
            )
            if score:
                scored.append((score, agent))

        if not scored:
            return None
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    async def _send_to_agent(self, agent: Agent, text: str) -> None:
        if not self.client:
            raise RuntimeError("Telegram client is not started.")
        if self.state.mode != CommunicationMode.ACTIVE:
            self._set_agent_status(agent.id, "waiting")
            self._record_event("pending", agent.id, text)
            return
        self._set_agent_status(agent.id, "message_received")
        await self.client.send_message(agent.telegram, text)
        self._record_event("outgoing", agent.id, text)
        self._set_agent_status(agent.id, "working")

    def _set_agent_status(self, agent_id: str, status: str) -> None:
        self.state.agent_status[agent_id] = status

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


def normalize_for_match(value: str) -> str:
    return normalize_username(value).replace("@", "").replace("_", "").replace("-", "")
