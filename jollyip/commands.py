"""All command definitions."""

# Standard Library
import re
import sys
import socket
import ipaddress

# Third Party
from click import (
    ParamType,
    ClickException,
    echo,
    style,
    option,
    command,
    confirm,
    argument,
)
from icmplib import ping
from rich.table import Table
from rich.console import Console

try:
    import stackprinter

    stackprinter.set_excepthook(style="darkbg2")
except ImportError:
    pass


INFO = {"fg": "white"}
LABEL = {"fg": "magenta", "bold": True}
INFO_SUCCESS = {"fg": "green"}
LABEL_SUCCESS = {"fg": "green", "bold": True, "underline": True}
INFO_FAIL = {"fg": "yellow"}
LABEL_FAIL = {"fg": "yellow", "bold": True, "underline": True}
ERROR = {"fg": "red", "bold": True}
WARNING = {"fg": "yellow"}
WARNING_LABEL = {"fg": "red", "bold": True}


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


class Number(ParamType):
    """Custom click type to accept an integer or float value."""

    name = "number"

    def convert(self, value, param, ctx):
        """Validate & convert input value to a float or integer."""

        try:
            converted = float(value)
        except ValueError:
            self.fail(f"'{value}' is not a valid number", param, ctx)

        if converted.is_integer():
            converted = int(converted)

        return converted


NUMBER = Number()


def _find_ipv6_prev(ip_range):
    """Parse an IPv6 range such as 2001:db8::1-a.

    Returns a tuple of valid IPv6Address objects
    """
    start_addr = ipaddress.ip_address(ip_range[0])
    start_host = start_addr.exploded.split(":")[-1]
    start = int(start_host, 16)
    end = int(ip_range[1], 16)
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

        if len(ip_range) == 1:
            # If item is a single host, yield its address object
            yield ipaddress.ip_address(ip_range[0])

        elif len(ip_range) == 2:
            """
            If item is a range, summarize the range into multiple
            subnets, then flatten those subnets into a single iterable
            of individual address objects.

            If item is in format '192.0.2.1-2', convert to
            '192.0.2.1-192.0.2.2'.
            """
            if bool(re.search(r"^[0-9]+$", ip_range[1])):
                increase_by = int(ip_range[1]) - 1
                ip_range[1] = str(ipaddress.ip_address(ip_range[0]) + increase_by)
            elif bool(re.search(r"^[a-fA-F]$", ip_range[1])):
                ip_range = _find_ipv6_prev(ip_range)

            range_obj = tuple(ipaddress.ip_address(ip) for ip in ip_range)
            range_sum = tuple(ipaddress.summarize_address_range(*range_obj))
            _target = tuple(ip for net in range_sum for ip in net)

            for i in _target:
                yield i
        else:
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
            target_base = ipaddress.ip_network(target)
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
            raise ClickException(style(f"'{target}' is not DNS-resolvable"))
        _target = (is_resolvable,)

    return _target, num_hosts


CMD_HELP = (
    style("Ping ", **INFO)
    + style("<target>\n\n", **LABEL)
    + style("<target> ", **LABEL)
    + style("Can be an IPv4 or IPv6 host, subnet, or range, or an FQDN.\n\n", **INFO)
    + style("Examples:\n", **INFO)
    + style("\n\n  jollyip ", **INFO)
    + style("192.0.2.1", **LABEL)
    + style("\n\n  jollyip ", **INFO)
    + style("192.0.2.0/24", **LABEL)
    + style("\n\n  jollyip ", **INFO)
    + style("192.0.2.1-5", **LABEL)
    + style("\n\n  jollyip ", **INFO)
    + style("192.0.2.1-5,9-14", **LABEL)
    + style("\n\n  jollyip ", **INFO)
    + style("2001:db8::1", **LABEL)
    + style("\n\n  jollyip ", **INFO)
    + style("2001:db8::/126", **LABEL)
    + style("\n\n  jollyip ", **INFO)
    + style("2001:db8::1-a", **LABEL)
)


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
        raise ClickException(style("jollyIP must be run as root", **ERROR))

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
            style("\nYou are trying to reach ", **WARNING)
            + style(lots_of_targets, **WARNING_LABEL)
            + style(" targets, which seems like a lot.", **WARNING,)
            + style("\nAre you sure you want to continue?", **INFO),
            show_default=True,
            abort=True,
        )

    echo(
        style("Starting jolly ping to ", **INFO)
        + style(str(target), **LABEL)
        # + source_msg
        + style("...", **INFO)
        + "\n"
    )
    tx = 0
    success = 0
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
                echo(
                    " " * 2
                    + style(host_str, **LABEL_FAIL)
                    + style(" is unreachable", **INFO_FAIL)
                )
            elif response.is_alive:
                success += 1
                output = str(round(response.avg_rtt, 2))
                echo(
                    " " * 2
                    + style("Response from ", **INFO_SUCCESS)
                    + style(host_str, **LABEL_SUCCESS)
                    + style(" received in ", **INFO_SUCCESS)
                    + style(output, **LABEL_SUCCESS)
                    + style(" ms", **INFO_SUCCESS)
                )

        echo(
            "\n"
            + style("Completed jolly ping to ", **INFO)
            + style(str(target), **LABEL)
            + "\n"
        )

        # Add the final stats to the table and print the table
        table.add_row(str(num_targets), str(tx), str(success), str(failed))
        console.print(table)

    except KeyboardInterrupt:
        echo(style("Stopping ping to ", **INFO) + style(str(target), **LABEL))

        # Add the current stats to the table and print the table
        table.add_row(str(num_targets), str(tx), str(success), str(failed))
        console.print(table)

        # Halt execution on keyboard interrupt
        sys.exit()

    except Exception as e:
        raise ClickException(style(str(e), **ERROR))
