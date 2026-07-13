import ipaddress

from fastapi import HTTPException, Request

_PRIVATE_NETWORKS = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
    ipaddress.IPv4Network("127.0.0.0/8"),
]


def is_private_ip(ip: str) -> bool:
    try:
        addr = ipaddress.IPv4Address(ip)
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        return False


async def require_internal_network(request: Request) -> None:
    client_host = request.client.host if request.client else None
    if not client_host or not is_private_ip(client_host):
        raise HTTPException(
            status_code=403,
            detail="Access restricted to internal network",
        )
