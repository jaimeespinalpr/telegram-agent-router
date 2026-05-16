from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class Agent(BaseModel):
    id: str
    name: str
    telegram: str
    kind: Literal["bot", "human"] = "bot"
    role: str = ""
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class AgentsConfig(BaseModel):
    agents: list[Agent] = Field(default_factory=list)
    owner_usernames: list[str] = Field(default_factory=list)

    @property
    def by_id(self) -> dict[str, Agent]:
        return {agent.id: agent for agent in self.agents}

    @property
    def by_telegram(self) -> dict[str, Agent]:
        return {normalize_username(agent.telegram): agent for agent in self.agents}


def normalize_username(username: str | None) -> str:
    if not username:
        return ""
    username = username.strip()
    return username.lower() if username.startswith("@") else f"@{username.lower()}"


def load_agents_config(path: str) -> AgentsConfig:
    config_path = Path(path)
    if not config_path.exists():
        example_path = config_path.with_name("agents.example.yaml")
        raise FileNotFoundError(
            f"Missing {config_path}. Copy {example_path} to {config_path} and edit it."
        )

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return AgentsConfig.model_validate(raw)
