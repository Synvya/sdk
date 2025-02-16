# AgentStr

AgentStr is an extension of [Agno](https://www.agno.ai) AI agents that enables peer-to-peer agent communication using the Nostr protocol.

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
│       ├── buyer.py
│       ├── buyer.pyi
│       ├── merchant.py
│       ├── merchant.pyi
│       ├── models.py
│       ├── models.pyi
│       ├── nostr.py
│       ├── nostr.pyi
│       └── py.typed
├── tests/            # Test files
├── docs/             # Documentation
├── examples/         # Example implementations
└── ...
```

## Features

### Current Features
- Create Merchant agents with Nostr identities:
  - Publish and manage merchant products using [NIP-15](https://github.com/nostr-protocol/nips/blob/master/15.md) marketplace protocol
  - Create merchant stalls to organize products
  - Handle shipping zones and costs
  - Secure communication using Nostr keys
- Create Buyer agents:
  - Retrieve a list of sellers from the relay using [NIP-15](https://github.com/nostr-protocol/nips/blob/master/15.md) marketplace protocol
  - Find an specific seller by name or public key
  - Refresh the list of sellers from the relay

### Roadmap
- [ ] Create marketplace with stalls
- [ ] Expand buyer agent to include more features
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

To install the examples clone the repository and navigate to the examples directory:

```bash
git clone https://github.com/Synvya/agentstr.git
cd agentstr/examples/
```
Each example has its own README with instructions on how to run it.

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

- [Agno](https://www.agno.ai) - For their AI agent framework
- [Rust-Nostr](https://rust-nostr.org) - For their Python Nostr SDK
- [Nostr Protocol](https://github.com/nostr-protocol/nips) - For the protocol specification

This software includes the following software licensed under the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0):
- [DataStax Python Driver for Apache Cassandra](https://github.com/datastax/python-driver)
- [cassIO](https://github.com/CassioML/cassio). This library is not maintained anymore. We will need to replace it with a new library.

