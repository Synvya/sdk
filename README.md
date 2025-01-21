AgentStr
========
AgentStr is an extension of [Phidata](https://www.phidata.com) AI agents that allows for agents to communicate with other agents in separate computers using the Nostr communication protocol.

The goal is for Agent A operated by Company A to be able to work with Agent B operated by Company B to achieve a common goal. For example: Company A wants to buy a product sold by Company B so Agent A and Agent B can coordinate and execute the transaction. 

As a first example, AgentStr implements the [NIP-15](https://github.com/nostr-protocol/nips/blob/master/15.md) Nostr Marketplace with `merchant` and `customer` profiles implemented each as a Phidata Toolkit available to Phidata agents. 

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
    from agentstr.core import AgentStr
    # Create the agent
    agent = AgentStr("Synvya Inc", "Seller")

    # Test AgentStr new capabilities
    print(f"Public key: {agent.get_public_key()}\nPrivate key: {agent.get_private_key()}")
    print(f"Company: {agent.get_company()}\nRole: {agent.get_role()}")

    # Test phidata inherited capabilities
    agent.print_response("Tell me a dad joke") 
    ```
5. Export your OpenAI key and run the code
    ```
    export OPENAI_API_KEY="sk-***"
    python main.py
    ```

# Contributing
Refer to [CONTRIBUTING.md](CONTRIBUTING.md) for specific instructions on installation instructions for developers and how to contribute.

# Acknowledgments
- [Phidata](https://www.phidata.com) - For building robust AI agents.
