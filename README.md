<div align="center" id="top">
  <a href="https://www.synvya.com">
    <picture>
      <img src="https://i.nostr.build/l1xRbUr5YpISK2dg.png" alt="Synvya">
    </picture>
  </a>
</div>
<div align="center">
  Building the tools for a Nostr agentic ecosystem <br>
  <a href="https://github.com/Synvya/sdk/tree/main/docs/docs.md">📚 Documentation</a> &nbsp;|&nbsp;
  <a href="https://github.com/Synvya/sdk/tree/main/examples">💡 Examples</a> &nbsp;|&nbsp;
  <a href="https://github.com/Synvya/sdk/stargazers">🌟 Star Us</a>
</div>

## Overview

The next step in AI evolution is enabling AI agents to communicate directly with one another. 

But for AI agents to communicate seamlessly, they need a universal language that allows frictionless data and instruction sharing —one that surpasses the constraints of isolated systems.

We believe that Nostr is the best suited open and standard communication protocol for AI agents: the “HTTP” for agent-to-agent communication. And we’re not alone. 

> "Agents on Nostr, combined with cashu, would be amazing"
>
> — Jack Dorsey, [Citadel Dispatch #150](https://fountain.fm/episode/OlQzTxXaGKkxfZr1pYLL), Jan 2025

Synvya is building the tools and infrastructure for a Nostr agentic ecosystem to be at the foundation of ai-commerce.

The Synvya SDK is a Python package that equips developers with the necessary tools for ai-commerce on Nostr, where buyers, sellers, or both can be autonomous AI agents. 

Communication happens over the open, permissionless [Nostr](https://github.com/nostr-protocol/nostr/blob/master/README.md) network using standard JSON data structures defined in [Nostr Implementation Possibilities](https://github.com/nostr-protocol/nips) or NIPs.


## Project Structure

The primary tools are within `src/synvya_sdk/`. 

The folder `src/synvya_sdk/agno/` contains [Agno](https://www.agno.com) Toolkits (`BuyerTools` and `SellerTools`) built using the Synvya SDK to enable Agno AI agents to engage in the Nostr agentic ecosystem. 

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

## Key Features
### Sellers
Publish to the Nostr network:
- Business background information
- Products and service for sale 

### Buyers
Find on the Nostr network:
- Business selling products or services
- Information about said products or services



## Installation

```shell
# Create a new python environment
python3 -m venv ~/.venvs/aienv
source ~/.venvs/aienv/bin/activate

# Install Synvya SDK
pip install -U synvya-sdk
```

## Examples

You can find example code in the [examples](https://github.com/Synvya/sdk/tree/main/examples/) directory.

To install the examples clone the repository and navigate to the examples directory:

```shell
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

This project is distributed under the [MIT License](https://github.com/Synvya/sdk/blob/main/LICENSE).

## Acknowledgments

- [Agno](https://www.agno.com) - For their AI agent framework
- [Rust-Nostr](https://rust-nostr.org) - For their Python Nostr SDK
- [Nostr Protocol](https://github.com/nostr-protocol/nips) - For the protocol specification

