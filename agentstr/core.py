import asyncio
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from nostr_sdk import Keys, Client, EventBuilder, NostrSigner, SendEventOutput

# Function to create Nostr keys
# The Function is external to the class 
# You create the keys and then always assign the same keys to your agent instance
# Keys should be stored in persistent memory to be reused every time the agent is initiated
def create_keys() -> Keys:
    return Keys.generate()


class AgentStr(Agent):

    # -*- Agent settings  
    # Company operating the agent.
    company: str = None
    
    # -*- Agent Nostr parameters 
    # The public / private keys
    keys: Keys = None
    # Nostr Signer
    nostr_signer: NostrSigner = None
    # Client
    client: Client = None
    # Relay
    relay: str = None
    # EventBuilder
    builder: EventBuilder = None
    # Output
    output: SendEventOutput = None

    # Call the class (Agent) constructor
    def __init__(self, keys: Keys, company: str, role: str, relay: str):
        super().__init__(role = role, model=OpenAIChat(id="gpt-4o"))
        self.keys = keys
        self.company = company
        self.nostr_signer = NostrSigner.keys(self.keys)
        self.client = Client(self.nostr_signer)
        self.relay = relay

    def get_company(self) -> str:
        return self.company
    
    def get_role(self) -> str:
        return self.role
    
    def get_keys(self) -> Keys:
        return self.keys
    
    def get_client(self) -> Client:
        return self.client
    
    async def connect_to_relay(self) -> bool:
        try:
            await self.client.add_relay(self.relay)
            await self.client.connect()
            return True
        except Exception as e:
            print(f"Failed to add relay {self.relay}: {e}")
            return False
    
    async def publish_note(self, text: str) -> SendEventOutput:
        self.builder = EventBuilder.text_note(text)
        self.output = await self.client.send_event_builder(self.builder)
        return self.output
                

def add(a, b):
    """Add two numbers."""
    return a + b



    