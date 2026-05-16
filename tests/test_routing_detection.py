from app.agents import Agent, AgentsConfig
from app.settings import Settings
from app.telegram_service import CommunicationMode, TelegramRouterService


def build_service() -> TelegramRouterService:
    agents = AgentsConfig(
        owner_usernames=["@jaimeespinalpr"],
        agents=[
            Agent(
                id="router",
                name="ChattyDA Bot",
                telegram="@Chattydabot",
                aliases=["chatty", "director"],
                keywords=["coordina", "resumen"],
            ),
            Agent(
                id="multi",
                name="MultiDA Bot",
                telegram="@Multida_bot",
                aliases=["multida", "marketing"],
                keywords=["promocionar", "cancion", "ep", "contenido"],
            ),
            Agent(id="prpagyda", name="PRPagyDA Bot", telegram="@prpagydabot"),
            Agent(id="prjimenezda", name="PRJimenezDA Bot", telegram="@prjimenezdabot"),
        ],
    )
    return TelegramRouterService(Settings(), agents)


def test_direct_mention_routes_to_agent():
    service = build_service()

    target = service.detect_target_agent("@Multida_bot dame ideas para promocionar mi EP")

    assert target is not None
    assert target.id == "multi"


def test_keyword_intent_routes_to_agent_without_mention():
    service = build_service()

    target = service.detect_target_agent("Necesito ideas para promocionar mi canción")

    assert target is not None
    assert target.id == "multi"


def test_unknown_intent_falls_back_to_router():
    service = build_service()

    target = service.detect_target_agent("Necesito ayuda con algo ambiguo")

    assert target is None


def test_stop_communication_sets_receive_only_mode():
    service = build_service()

    service.set_mode(CommunicationMode.RECEIVE_ONLY)

    assert service.state.mode == CommunicationMode.RECEIVE_ONLY
    assert set(service.state.agent_status.values()) == {"paused"}
