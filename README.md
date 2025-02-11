# AgentStr

AgentStr is an extension of [Phidata](https://www.phidata.com) AI agents that enables peer-to-peer agent communication using the Nostr protocol.

## Overview

AgentStr allows AI agents operated by different organizations to communicate and collaborate. For example:
- Agent A from Company A can coordinate with Agent B from Company B to execute a transaction
- Agents can discover and interact with each other through the decentralized Nostr network
- No central authority or intermediary required

## Project Structure

```
agentstr/
├── src/              # Source code
│   └── agentstr/
│       ├── __init__.py
│       ├── merchant.py
│       ├── merchant.pyi
│       ├── nostr.py
│       └── nostr.pyi
├── tests/            # Test files
├── docs/             # Documentation
├── examples/         # Example implementations
└── ...
```

## Features

### Current Features
- Create Merchant agents with Nostr identities
- Publish and manage merchant products using [NIP-15](https://github.com/nostr-protocol/nips/blob/master/15.md) marketplace protocol
- Create merchant stalls to organize products
- Handle shipping zones and costs
- Secure communication using Nostr keys

### Roadmap
- [ ] Create marketplace with stalls
- [ ] Create Buyer agents
- [ ] Enable merchants to define products
- [ ] Add customer toolkit for buyers
- [ ] Support additional Nostr NIPs
- [ ] Add more agent interaction patterns

## Installation

```bash
# Create a new python environment
python3 -m venv ~/.venvs/aienv
source ~/.venvs/aienv/bin/activate

# Install agentstr
pip install --upgrade pip
pip install agentstr
```

## Examples

You can find example code in the [examples](https://github.com/Synvya/agentstr/tree/main/examples/) directory.

### Instaling the examples
1. **Clone the repository**
```bash
git clone https://github.com/Synvya/agentstr.git
```

### Basic CLI Example
A simple command-line interface demonstrating agentstr's merchant capabilities:


- [Basic CLI Agent](https://github.com/Synvya/agentstr/tree/main/src/agentstr/examples/basic_cli/main.py) - A complete example showing:
  - Setting up merchant profiles
  - Creating stalls with shipping methods
  - Defining products with shipping costs
  - Configuring the agent with the merchant toolkit
  - Running an interactive CLI application

1. ** Create a virtual environment**
```bash
cd agentstr/examples/basic_cli
python3 -m venv venv
source venv/bin/activate
```

2. ** Install dependencies**
```bash
pip install -r requirements.txt
```

3. ** Configure your environment**
```bash
cp .env.example .env
```
**Edit the .env file with your own API keys and Nostr credentials**

4. ** Run the example**
```bash
python main.py
```


## Documentation

For more detailed documentation and examples, see [Docs](https://github.com/Synvya/agentstr/tree/main/docs/docs.md) 

## Development

See [CONTRIBUTING.md](https://github.com/Synvya/agentstr/blob/main/CONTRIBUTING.md) for:
- Development setup
- Testing instructions
- Contribution guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Synvya/agentstr/blob/main/LICENSE) file for details.

## Acknowledgments

- [Phidata](https://www.phidata.com) - For their AI agent framework
- [Rust-Nostr](https://rust-nostr.org) - For their Python Nostr SDK
- [Nostr Protocol](https://github.com/nostr-protocol/nips) - For the protocol specification

