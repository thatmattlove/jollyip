# Standard Library
import ipaddress

# Third Party
from ping3 import verbose_ping


def ping_host(host, source=None, count=4, ttl=4, size=64, timeout=4, unit="ms"):
    ...
