import unittest
import agentstr

from agentstr.core import add, AgentStr
from phi.model.openai import OpenAIChat
from dotenv import load_dotenv

load_dotenv()

def test_get_public_key():
    agent = AgentStr(company="Synvya AI", role="Seller")
    public_key = agent.get_public_key()
    assert public_key == "npub - Synvya AI - Seller"

def test_add():
    assert add(2, 3) == 5

