"""All command definitions."""

# Standard Library
import re
import sys
import socket
import ipaddress

# Third Party
from click import option, command, confirm, argument
from icmplib import ping
from rich.table import Table
from rich.console import Console

# Project
from jollyip.types import NUMBER
from jollyip.formatting import fail, info, error, success

try:
    import stackprinter
    from devtools import debug

    stackprinter.set_excepthook(style="darkbg2")
except ImportError:
    __builtins__["debug"] = debug
    pass


def _verify_root():
    """Verify the command is running with root privileges."""
    import os

    uid = os.getegid()
    if uid != 0:
        return False
    return True


def _verify_hostname(host):
    """Verify a hostname is resolvable."""
    try:
        resolved = socket.getaddrinfo(host, None)[0][4][0]
        ip = ipaddress.ip_address(resolved)
        return ip
    except (socket.gaierror, ValueError):
        return False


def _find_ipv6_prev(ip_range):
    """Parse an IPv6 range such as 2001:db8::1-a.

    Returns a tuple of valid IPv6Address objects
    """
    start_addr = ipaddress.ip_address(ip_range[0])
    start_host = start_addr.exploded.split(":")[-1]
    start = int(start_host, 16)
    end = int(ip_range[1], 16) - 1
    end_host = hex(start + end)[2:]
    end_addr_str = ":".join(start_addr.exploded.split(":")[:-1] + [end_host])
    end_addr = ipaddress.ip_address(end_addr_str)
    return start_addr, end_addr


def _parse_ip_range(range_str):
    """Parse an IP range such as 192.0.2.1-192.0.2.9,192.0.2.100.

    Returns a generator of valid addresses in the range.
    """
    for section in range_str.split(","):
        ip_range = section.split("-")
        debug(ip_range)

        try:
            if len(ip_range) == 1:
                net = ipaddress.ip_network(ip_range[0], strict=False)
                if net.num_addresses != 1:
                    net = net.hosts()
                for ip in net:
                    yield ip

            elif len(ip_range) == 2:
                """
                If item is a range, summarize the range into multiple
                subnets, then flatten those subnets into a single iterable
                of individual address objects.

                If item is in format '192.0.2.1-2', convert to
                '192.0.2.1-192.0.2.2'.
                """
                start = ipaddress.ip_address(ip_range[0])

                if start.version == 4 and bool(re.search(r"^[0-9]+$", ip_range[1])):
                    end_str = ".".join(ip_range[0].split(".")[:-1] + [ip_range[1]])
                    end = ipaddress.ip_address(end_str)

                elif start.version == 6 and bool(
                    re.search(r"^[0-9a-fA-F]+$", ip_range[1])
                ):
                    start, end = _find_ipv6_prev(ip_range)

                range_sum = tuple(ipaddress.summarize_address_range(start, end))
                _target = tuple(ip for net in range_sum for ip in net)

                for i in _target:
                    yield i

            else:
                raise RuntimeError()
        except ValueError as e:
            error(str(e))
        except RuntimeError:
            raise ValueError()


def _process_target(target):
    """Convert input target IP, range, or subnet to iterable of valid targets."""
    num_hosts = 1
    try:
        if bool(re.search(r"-|,", target)):
            # If target contains hyphens or commas, process it as a range
            _target = tuple(_parse_ip_range(target))
            num_hosts = len(_target)
        else:
            target_base = ipaddress.ip_network(target, strict=False)
            if target_base.num_addresses != 1:
                """
                If target is a network, return only the usable
                addresses (remove network & broadcast addresses).
                """
                _target = target_base.hosts()
                num_hosts = target_base.num_addresses - 2
            else:
                _target = target_base
                num_hosts = target_base.num_addresses
    except ValueError:
        is_resolvable = _verify_hostname(target)
        if not is_resolvable:
            error("'{t}' is not DNS-resolvable", t=str(target))
        _target = (is_resolvable,)

    return _target, num_hosts


HELP1 = info(
    "Ping {t}\n\n{t} Can be an IPv4 or IPv6 host, subnet, range, or an FQDN.\n\n",
    t="<target>",
    callback=None,
)

HELP2 = info("Examples:", callback=None)

HELP3 = info("\n\njollyip {t}", t="192.0.2.1", callback=None)
HELP4 = info("\n\njollyip {t}", t="2001:db8::/126", callback=None)
HELP5 = info("\n\njollyip {t}", t="192.0.2.1-5", callback=None)
HELP6 = info("\n\njollyip {t}", t="www.google.com", callback=None)
ALL_HELP = (HELP1, HELP2, HELP3, HELP4, HELP5, HELP6)

CMD_HELP = "".join(ALL_HELP)


@command(help=CMD_HELP)
@argument("target")
@option("--timeout", type=NUMBER, default=0.5, help="ICMP Timeout")
def run_ping(target, timeout):
    """Validate & execute pings."""

    """
    Sending ICMP packets requires the use of a raw socket, which is a
    privileged operation on most systems. The below checks if the
    current user ID is equal to 0, or root. If it is not, an error is
    raised.
    """

    is_root = _verify_root()
    if not is_root:
        error("jollyIP must be run as root.")

    """
    Verify if the input target is an IP address or network. The
    `ip_network()` function of the `ipaddress` module will reflect a
    single host as a network, e.g. 192.0.2.1/32. If the target is not a
    IPv4 or IPv6 address, we assume that it is a hostname. The below
    ensures that whatever target is specified, it will be iterable for
    simpler iteration.
    """
    target_iter, num_targets = _process_target(target)

    # Warn the user if the number of targets is more than 256.
    if num_targets > 254:
        lots_of_targets = "{:,}".format(num_targets)
        confirm(
            info(
                "\nYou are trying to reach {lots} targets, which seems like a lot."
                + "\nAre you sure you want to continue?",
                callback=None,
                lots=lots_of_targets,
            ),
            show_default=True,
            abort=True,
        )

    info("Starting jolly ping to {t}...\n", t=str(target))

    tx = 0
    successful = 0
    failed = 0

    # Create a pretty table to summarize the output.
    console = Console()
    table = Table(show_header=True, header_style="bold white", border_style="white")
    table.add_column("Targets", style=" bold white")
    table.add_column("Transmitted", style=" bold white")
    table.add_column("Alive", style=" bold green")
    table.add_column("Unreachable", style=" bold red")

    try:
        for host in target_iter:
            host_str = str(host)
            response = ping(host_str, count=1, timeout=timeout)
            tx += 1

            if not response.is_alive:
                failed += 1
                fail("  {host} is unreachable", host=host_str)
            elif response.is_alive:
                successful += 1
                output = str(round(response.avg_rtt, 2))
                success(
                    "  Response from {host} received in {time} ms",
                    host=host_str,
                    time=output,
                )

        info("\nCompleted jolly ping to {host}\n", host=str(target))

        # Add the final stats to the table and print the table
        table.add_row(str(num_targets), str(tx), str(successful), str(failed))
        console.print(table)

    except KeyboardInterrupt:
        info("Stopping ping to {host}", host=str(target))

        # Add the current stats to the table and print the table
        table.add_row(str(num_targets), str(tx), str(successful), str(failed))
        console.print(table)

        # Halt execution on keyboard interrupt
        sys.exit()

    except Exception as e:
        error(str(e))
