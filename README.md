# Synvya SDK

Synvya SDK is a python SDK that enables peer-to-peer agent communication using the Nostr protocol.

## Overview

Synvya SDK allows AI agents operated by different organizations to communicate and collaborate. For example:
- Agent A from Company A can coordinate with Agent B from Company B to execute a transaction
- Agents can discover and interact with each other through the decentralized Nostr network
- No central authority or intermediary required

The primary source code is under src/synvya_sdk. 

The folder src/synvya_sdk/agno contains an example implementation with two Nostr capable Toolkits for [Agno](https://www.agno.com) agents, one for buyer agents (BuyerTools) and one for seller agents (SellerTools).

## Project Structure

```
sdk/
├── src/              # Source code
│   └── synvya_sdk/
│       ├── models.py
│       ├── models.pyi
│       ├── nostr.py
│       ├── nostr.pyi
│       └── py.typed
|       └── agno/
|         ├── __init__.py
│         ├── buyer.py
│         ├── buyer.pyi
│         ├── seller.py
│         ├── seller.pyi
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

# Install Synvya SDK
pip install --upgrade pip
pip install synvya_sdk
```

## Examples

You can find example code in the [examples](https://github.com/Synvya/sdk/tree/main/examples/) directory.

To install the examples clone the repository and navigate to the examples directory:

```bash
git clone https://github.com/Synvya/sdk.git
cd sdk/examples/
```
Each example has its own README with instructions on how to run it.

## Documentation

For more detailed documentation and examples, see [Docs](https://github.com/Synvya/sdk/tree/main/docs/docs.md) 

## Development

See [CONTRIBUTING.md](https://github.com/Synvya/sdk/blob/main/CONTRIBUTING.md) for:
- Development setup
- Testing instructions
- Contribution guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Synvya/sdk/blob/main/LICENSE) file for details.

## Acknowledgments

- [Agno](https://www.agno.com) - For their AI agent framework
- [Rust-Nostr](https://rust-nostr.org) - For their Python Nostr SDK
- [Nostr Protocol](https://github.com/nostr-protocol/nips) - For the protocol specification

