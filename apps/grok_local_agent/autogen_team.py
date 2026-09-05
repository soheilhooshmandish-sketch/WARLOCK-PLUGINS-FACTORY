"""AutoGen AgentChat-shaped team without installing autogen-agentchat.

Maps to current Microsoft AutoGen 0.4+ ideas:
  AssistantAgent -> role with tools
  RoundRobinGroupChat -> turn order
  MaxMessageTermination -> AUTOGEN_MAX_TURNS
  policy UserProxy -> never writes apps/local_agent

Real autogen-agentchat is not added to requirements (offline, no LLM client).
"""
from dataclasses import dataclass, field

from . import inspect_self as S
from . import stats as ST
from . import tools as T
from .config import AUTOGEN_MAX_TURNS
from .peers import fleet
from .policy import is_locked


@dataclass
class AgentMessage:
    source: str
    content: str


@dataclass
class Assistant:
    name: str
    run: object


@dataclass
class RoundRobinTeam:
    agents: list[Assistant]
    max_turns: int = AUTOGEN_MAX_TURNS
    transcript: list[AgentMessage] = field(default_factory=list)

    def run_task(self, task: str) -> str:
        self.transcript.append(AgentMessage("user", task))
        for agent in self.agents[: self.max_turns]:
            text = agent.run(task)
            self.transcript.append(AgentMessage(agent.name, text))
            if "APPROVE" in text or is_locked(task):
                break
        return "\n\n".join(f"[{m.source}] {m.content}" for m in self.transcript)


def _scout(task: str) -> str:
    q = task.split()[-1] if task.split() else "farnaz"
    return "scout: " + T.search_names(q, limit=6)


def _analyst(_: str) -> str:
    return "analyst: " + S.syntax() + " | " + S.inventory().splitlines()[0]


def _reviewer(_: str) -> str:
    lock = ST.lock_ok()
    return f"reviewer: {lock}\nAPPROVE original ChatGPT agent unchanged"


def _fleet(_: str) -> str:
    return "fleet:\n" + fleet()


def run_autogen(task: str) -> str:
    team = RoundRobinTeam(
        agents=[
            Assistant("scout", _scout),
            Assistant("analyst", _analyst),
            Assistant("fleet", _fleet),
            Assistant("reviewer", _reviewer),
        ]
    )
    header = (
        "AutoGen-style RoundRobinGroupChat (offline subset)\n"
        "Not Microsoft autogen-agentchat package. MaxMessageTermination="
        f"{AUTOGEN_MAX_TURNS}"
    )
    return header + "\n\n" + team.run_task(task)
