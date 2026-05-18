import os
import json
from eth_account import Account

# Enable unofficial HD features to generate a secure random mnemonic/key if needed,
# but we will just use standard creation
Account.enable_unaudited_hdwallet_features()

WALLET_FILE = os.path.join(os.path.dirname(__file__), "agent_wallet.json")
ERC8004_FILE = os.path.join(os.path.dirname(__file__), "erc8004_identity.json")

def get_or_create_wallet():
    # Generate or load the native EVM wallet
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    from dotenv import load_dotenv, set_key
    load_dotenv(env_path)
    
    address = os.getenv("AGENT_WALLET_ADDRESS")
    private_key = os.getenv("AGENT_PRIVATE_KEY")
    
    if not address or not private_key:
        acct = Account.create()
        address = acct.address
        private_key = acct.key.hex()
        set_key(env_path, "AGENT_WALLET_ADDRESS", address)
        set_key(env_path, "AGENT_PRIVATE_KEY", private_key)
    # Generate the ERC-8004 Compliance Identity Bundle
    identity = {
        "agentAddress": address,
        "name": "xRegime Oracle",
        "standard": "ERC-8004 (Trustless Agents)",
        "capabilities": ["Financial Analysis", "Speech-to-Text", "Kraken Execution"],
        "modelEnsemble": ["Qwen-7B", "Qwen-72B", "Mixtral-8x7B"],
        "reputationSource": "Dynamic Regime Score",
        "verificationProtocol": "Featherless Consensus (2/3 Vote)"
    }
    with open(ERC8004_FILE, 'w') as f:
        json.dump(identity, f, indent=4)
        
    return identity
