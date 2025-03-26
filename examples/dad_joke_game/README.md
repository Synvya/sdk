# Dad Joke Example
## Introduction
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
### Clone the repository and navigate to this example
```shell
git clone https://github.com/synvya/sdk.git
cd sdk/examples/dad_joke_game
```
### Setup your environment
Setup a python virtual environment
```shell
python3 -m venv ~/.venvs/tstenv
source ~/.venvs/tstenv/bin/activate
```

Add your OpenAI API key to the `.env` file. The application will generate a new set of Nostr keys for you.
```shell
cp .env.example .env
```

### Install dependencies
```shell
pip install --upgrade pip
pip install -r requirements.txt
```

### Set your own NIP-05 ID
Edit `joker.py` to use a NIP-05 ID that you can validate
```python
NIP05 = "joker@yourdomain.com"
```
### Run the Joker
```shell
python joker.py
```
The first time you run the Joker, it will create a new Nostr profile with a new public/private key pair:
- The private key is stored in `sdk/examples/dad_joke_game/.env`
- The public key is shown on the terminal window. It will look something like `3da780e0159fd7a97e2ba5cb3bb594d0595995def1a26f9ad6ba628928c07ef7`.

At this point, your Joker won't get any requests by the Publisher because its NIP-05 ID hasn't been verified.

Copy the public key from the terminal and add it to the `.well-known/nostr.json` file on `yourdomain.com`. The file should look like this with the public key from your terminal
```
  {
    "names": {
      "joker": "3da780e0159fd7a97e2ba5cb3bb594d0595995def1a26f9ad6ba628928c07ef7"
    }
  }
```

The file should display when you go to the URL `https://yourdomain.com/.well-known/nostr.json?name=joker` with a web browser.
Now your agent has a validated NIP-05 id.

Run again to join the game.
```shell
python joker.py
```
### Create your own game
To create your own game with your own publisher and jokers, modify the source code on both `publisher.py` and `joker.py` to use a different namespace:
```python
NAMESPACE = "com.yourdomain.gamer"
```
And run your own publisher with:
```shell
python publisher.py
```
