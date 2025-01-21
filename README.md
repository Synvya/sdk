AgentStr
========
AgentStr is an extension of [Phidata](https://www.phidata.com) AI agents that allows for agents to communicate with other agents in separate computers using the Nostr communication protocol.

The goal is for Agent A operated by Company A to be able to work with Agent B operated by Company B to achieve a common goal. For example: Company A wants to buy a product sold by Company B so Agent A and Agent B can coordinate and execute the transaction. 

The basic communication tools are implemented in `agentstr/nostr.py`. 

As a first example, AgentStr provides the tools to create and operate a marketplace using the [NIP-15](https://github.com/nostr-protocol/nips/blob/master/15.md) Nostr Marketplace as its foundation. The file `agentstr/marketplace.py` includes NIP-15 `merchant` and `customer` profiles implemented each as a Phidata Toolkit. 

# License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

# Current status
The library is in its infancy.

Done:
- Workflow to package and distribute the library
- Users can create a Merchant profile and create an agent with the `merchant` toolkit that acts on behalf of the Merchant profile


To be done:
- Create a `marketplace` with `stalls`
- Merchants to define `products`
- Create a `customer` Toolkit

# Installation
AgentStr is offered as a python library available at https://pypi.org/project/agentstr/. 

Here is an example on how to use the library:

1. Create a new python environment for your app
    ```
    cd ~/
    python3 -m venv ~/.venvs/aienv
    source ~/.venvs/aienv/bin/activate
    ```
2. Install the agentstr library
    ```
    pip install --upgrade pip
    pip install agentstr
    mkdir ~/mysampleapp
    cd ~/mysampleapp
    ```
3. Create a new python file
    ```
    touch main.py
    ```
4. Copy paste this code to the main.py file
    ```
    from dotenv import load_dotenv
    from os import getenv
    from phi.agent import Agent 
    from phi.model.openai import OpenAIChat
    from agentstr.marketplace import MerchantProfile, Merchant


    profile = MerchantProfile(
        "Synvya",
        "Testing stuff",
        "https://i.nostr.build/ocjZ5GlAKwrvgRhx.png",
        getenv("NSEC_KEY")
    )

    agent = Agent(
        name="Merchant Assistant",
        model=OpenAIChat(id="gpt-4o"),
        tools=[Merchant(merchant_profile=profile, relay="wss://relay.damus.io")],
        show_tool_calls=True,
        markdown=True,
        debug_mode=True
    )
    
    agent.print_response("Publish the merchant information and tell me full URL where I can find it")
    ```
5. Export your OpenAI key and optionally a Nostr private key before running the code
    ```
    export OPENAI_API_KEY="sk-***"
    export NSEC_KEY="nsec***"
    python main.py
    ```

This example will attempt to load a Nostr private key defined as NSEC_KEY in bech32 format. If a private key is not provided, the `MerchantProfile` class initializer will assign it a new one. 

# Contributing
Refer to [CONTRIBUTING.md](CONTRIBUTING.md) for specific instructions on installation instructions for developers and how to contribute.

# Acknowledgments
- [Phidata](https://www.phidata.com) - For building robust AI agents.
- [Rust-Nostr](https://rust-nostr.org/index.html) - For providing a python based Nostr SDK.
