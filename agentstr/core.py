from phi.agent import Agent
from phi.model.openai import OpenAIChat
from pydantic import Field
from typing import Optional


class AgentStr(Agent):

    # -*- Agent settings  
    # Company operating the agent.
    # Used as seed for public / private key identifier together with the agent role
    company: str = None
    
    # -*- Agent public / private key identifiers
    # The public / private key should be deterministic for a given 'company' and 'role' combination
    # Public key for the agent
    npub: str = None
    # Private key for the agent
    nsec: str = None

    # Call the parent class (Agent) constructor
    def __init__(self, company: str, role: str):
        super().__init__(role = role, model=OpenAIChat(id="gpt-4o"))
        self.company = company
        self.npub = f"npub - {self.company} - {self.role}" 
        self.nsec = f"nsec - {self.company} - {self.role}"

    def get_public_key(self) -> str:
        return self.npub
    
    def get_private_key(self) -> str:
        return self.nsec
    
    def get_company(self) -> str:
        return self.company
    
    def get_role(self) -> str:
        return self.role

def add(a, b):
    """Add two numbers."""
    return a + b
