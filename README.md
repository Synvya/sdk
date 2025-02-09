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
│       ├── marketplace.py
│       └── nostr.py
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

See our [examples directory](https://github.com/Synvya/agentstr/tree/main/examples/) for complete working implementations:

- [Basic CLI Agent](https://github.com/Synvya/agentstr/tree/main/examples/basic_cli/main.py) - A complete example showing:
  - Setting up merchant profiles
  - Creating stalls with shipping methods
  - Defining products with shipping costs
  - Configuring the agent with the merchant toolkit
  - Running an interactive CLI application


## Documentation

For more detailed documentation and examples, see [Docs](https://github.com/Synvya/agentstr/tree/main/docs/docs.md) 

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Testing instructions
- Contribution guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Phidata](https://www.phidata.com) - For their AI agent framework
- [Rust-Nostr](https://rust-nostr.org) - For their Python Nostr SDK
- [Nostr Protocol](https://github.com/nostr-protocol/nips) - For the protocol specification

