"""Curated sources fetched for Farnaz. Not the entire internet."""

SOURCES = [
    {"topic": "autogen", "title": "AgentChat termination",
     "url": "https://microsoft.github.io/autogen/0.4.4/user-guide/agentchat-user-guide/tutorial/termination.html"},
    {"topic": "autogen", "title": "Selector Group Chat",
     "url": "https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/selector-group-chat.html"},
    {"topic": "autogen", "title": "Teams RoundRobin vs Selector vs Swarm",
     "url": "https://www.mintlify.com/microsoft/autogen/agentchat/teams"},
    {"topic": "autogen", "title": "v0.2 to v0.4 migration selector_func",
     "url": "https://microsoft.github.io/autogen/0.4.0/user-guide/agentchat-user-guide/migration-guide.html"},
    {"topic": "autogen", "title": "AutoGen GitHub README",
     "url": "https://github.com/microsoft/autogen"},
    {"topic": "crewai", "title": "HITL workflows",
     "url": "https://docs.crewai.com/en/learn/human-in-the-loop"},
    {"topic": "crewai", "title": "Human feedback in Flows",
     "url": "https://docs.crewai.com/en/learn/human-feedback-in-flows"},
    {"topic": "crewai", "title": "Resume API",
     "url": "https://docs.crewai.com/en/api-reference/resume.md"},
    {"topic": "crewai", "title": "Execution hooks PRE_TOOL_CALL",
     "url": "https://docs.crewai.com/v1.15.18/en/learn/execution-hooks"},
    {"topic": "crewai", "title": "Frontend HITL CopilotKit",
     "url": "https://docs.crewai.com/v1.15.16/en/guides/frontend/human-in-the-loop"},
    {"topic": "langgraph", "title": "Interrupts",
     "url": "https://docs.langchain.com/oss/python/langgraph/interrupts"},
    {"topic": "langgraph", "title": "interrupt() reference",
     "url": "https://reference.langchain.com/python/langgraph/types/interrupt"},
    {"topic": "langgraph", "title": "Checkpointers",
     "url": "https://docs.langchain.com/oss/javascript/langgraph/checkpointers"},
    {"topic": "langgraph", "title": "Graph API add_messages",
     "url": "https://docs.langchain.com/oss/python/langgraph/graph-api"},
    {"topic": "langgraph", "title": "add_messages source",
     "url": "https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/graph/message.py"},
    {"topic": "langgraph", "title": "checkpoint package",
     "url": "https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint"},
    {"topic": "langgraph", "title": "Human-in-the-loop JS",
     "url": "https://docs.langchain.com/oss/javascript/langchain/human-in-the-loop"},
    {"topic": "oversight", "title": "Oversight Has a Capacity (arXiv:2606.08919)",
     "url": "https://arxiv.org/abs/2606.08919"},
    {"topic": "xai", "title": "xAI docs llms.txt",
     "url": "https://x.ai/docs/llms.txt"},
    {"topic": "xai", "title": "xAI console API keys",
     "url": "https://console.x.ai/team/default/api-keys"},
    {"topic": "xai", "title": "Quickstart",
     "url": "https://x.ai/docs/developers/quickstart"},
]


def list_sources(topic: str | None = None) -> str:
    rows = SOURCES
    if topic:
        t = topic.lower().strip()
        rows = [s for s in SOURCES if t in s["topic"] or t in s["title"].lower()]
    if not rows:
        rows = SOURCES
    lines = [f"Farnaz sources ({len(rows)})"]
    for s in rows:
        lines.append(f"[{s['topic']}] {s['title']}\n{s['url']}")
    return "\n\n".join(lines)
