# Nostr Utils

Use this python script to invoke the low level nostr API:


## Setup

1. Clone the repository and navigate to this example:

```bash
git clone https://github.com/agentstr/agentstr.git
cd agentstr/examples/basic_merchant
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

4. Run the example:

```bash
python nostr_utils.py
```

## Usage

If you're deleting or updating existing events, you will need to provide the `nsec` used to publish the original events in `.env`.
