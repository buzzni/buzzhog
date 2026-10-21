import os

from posthog.settings.access import SECRET_KEY
from posthog.settings.utils import get_list

MESSAGING_HASH_SALT: str = os.getenv("MESSAGING_HASH_SALT") or SECRET_KEY
MESSAGING_HASH_SALT_FALLBACKS: list[str] = [
    salt for salt in get_list(os.getenv("MESSAGING_HASH_SALT_FALLBACKS", "")) if salt
]

# Transactional email over HTTP. When the key is empty, PostHog sends email over SMTP instead.
CUSTOMER_IO_API_KEY: str = os.getenv("CUSTOMER_IO_API_KEY", "")
CUSTOMER_IO_API_URL: str = os.getenv("CUSTOMER_IO_API_URL", "https://api.customer.io")
