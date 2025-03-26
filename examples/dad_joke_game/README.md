# Dad Joke Example

This example demonstrates how Synvya leverages Nostr to address two of the critical steps required for agent to agent communication as well as multi-agent applications:
### Discoverability:
The Publisher will find all Nostr profiles with the following properties:
- `bot=true` (see [NIP-24](https://github.com/nostr-protocol/nips/blob/0619f370bca3485bb9c5870bc2defa03c7c3d10e/24.md))
- label `dad-joke-game` with namespace `com.synvya.gamer` (see [NIP-32](https://github.com/nostr-protocol/nips/blob/0619f370bca3485bb9c5870bc2defa03c7c3d10e/32.md))
- hashtag `joker` (see [NIP-24](https://github.com/nostr-protocol/nips/blob/0619f370bca3485bb9c5870bc2defa03c7c3d10e/24.md))
### Authentication:
The Joker profile must include a validated [NIP-05](https://github.com/nostr-protocol/nips/blob/0619f370bca3485bb9c5870bc2defa03c7c3d10e/05.md) identifier like `joker@yourdomain.com`.
Note that a validated NIP-05 only confirms that the Joker profile is associated with the entity controlling `https://yourdomain.com`.
### Secure communication
Communication happens through private direct messages using [NIP-17](https://github.com/nostr-protocol/nips/blob/0619f370bca3485bb9c5870bc2defa03c7c3d10e/17.md)
 

## Setup

1. Clone the repository and navigate to this example:
    ```bash
    git clone https://github.com/synvya/sdk.git
    cd sdk/examples/dad_joke_game
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Copy `.env.example` to `.env` and fill in your OpenAI API key:\
The application will generate a new set of Nostr keys for you.
    ```bash
    cp .env.example .env
    ```

4. Run the Joker to join my game:
    ```bash
    python joker.py
    ```

5. Create your own game:\
To create your own game with your own publisher and jokers, modify the source code on both `publisher.py` and `joker.py` to use a different namespace: 
    ```python
    profile.set_namespace("com.yourdomain.gamer")
    ```
And run your own publisher with:
    ```bash
    python publisher.py
    ```
