import pytest, pytest_asyncio, asyncio

from agentstr.core import add, AgentStr, create_keys
from phi.model.openai import OpenAIChat
from nostr_sdk import Keys, Client, SendEventOutput
from dotenv import load_dotenv

load_dotenv()

def test_create_keys():
    keys = create_keys()
    assert isinstance(keys, Keys), "The result should be a Key"

def test_get_keys():
    keys = create_keys()
    agent = AgentStr(keys, company="Synvya AI", role="Seller", relay="wss://relay.damus.io")
    test_keys = agent.get_keys()
    print(f"Keys: {test_keys}")
    #assert isinstance(test_keys, Keys), "The result should be a set of Keys"
    assert keys == test_keys

def test_get_client():
    keys = create_keys()
    agent = AgentStr(keys, company="Synvya AI", role="Seller", relay="wss://relay.damus.io")
    client = agent.get_client()
    print(f"Client: {client}")
    assert isinstance(client, Client), "The result should be a set of Keys"


@pytest.mark.asyncio
async def test_connect_to_relay():
    keys = create_keys()
    agent = AgentStr(keys, company="Synvya AI", role="Seller", relay="wss://relay.damus.io")
    connected = await agent.connect_to_relay()
    assert connected is True, "Agent should connect to the relay successfully"

@pytest.mark.asyncio
async def test_publish_note():
    keys = create_keys()
    agent = AgentStr(keys, company="Synvya AI", role="Seller", relay="wss://relay.damus.io")
    connected = await agent.connect_to_relay()
    if connected:
        output = await agent.publish_note("Testing AgentStr")
        print(f"Note published with public key: {keys.public_key().to_bech32()}")
        assert output.success, "The success field should not be empty"
    else:
        assert connected is True, "should fail"

     
def test_add():
    assert add(2, 3) == 5

