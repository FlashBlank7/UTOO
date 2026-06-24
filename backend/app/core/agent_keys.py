import secrets

AGENT_KEY_PREFIX_LENGTH = 18


def generate_agent_api_key() -> str:
    return f"utoo_agent_{secrets.token_urlsafe(32)}"


def agent_key_prefix(api_key: str) -> str:
    return api_key[:AGENT_KEY_PREFIX_LENGTH]
