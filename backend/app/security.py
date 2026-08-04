import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit


async def validate_public_url(url: str) -> None:
    """Reject URLs that could be used to reach local or private infrastructure."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only absolute HTTP(S) URLs are supported")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not supported")

    try:
        records = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM),
        )
    except socket.gaierror as exc:
        raise ValueError("The hostname could not be resolved") from exc

    addresses = {ipaddress.ip_address(record[4][0]) for record in records}
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Private, loopback, or reserved network addresses are not allowed")
