from config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT


def test_agent_config():
    assert AGENT_NAME == "Warlock Local Agent"
    assert AGENT_VERSION == "0.2.0"
    assert PROJECT_ROOT.exists()


if __name__ == "__main__":
    test_agent_config()
    print("Agent configuration test: PASS")
