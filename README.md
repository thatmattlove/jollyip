<div align="center">
  <br/>
  <h1>Jolly IP</h1>
  <br/>
  <strong>Scan an IP range, but happily.</strong>
  <br/>
  <br/>
  <pre>
  Jolly IP is the happier, Java-free alternative to Angry IP Scanner.</pre>
</div>

## Installation

```console
$ pip3 install --user jollyip
```

- jollyIP requires **Python 3.5 or later**
- jollyIP must be run as root (`sudo jollyip`)

## About

Jolly IP was made during a fit of rage, after being told I had to install Java in order to install [Angry IP Scanner](https://angryip.org/) on macOS (which I refuse to do). While Angry IP is a great app, as a network engineer, most of the time I just need a quick CLI solution to scan something or generate some ARP entries. Jolly IP has the added advantage of being able to specify hosts, subnets, ranges, or any combination thereof in a single command.

As such, very little testing outside macOS has been done. That said, The [underlying ICMP library](https://github.com/ValentinBELYN/icmplib) supports macOS, Linux, and Windows, as do all other minor dependencies. If you run into a compatibility issue, please [raise an issue](https://github.com/checktheroads/jollyip/issues) and I'll do what I can.

## Usage

### IP

```console
# jollyip 192.0.2.1
Starting jolly ping to 192.0.2.1...

  Response from 192.0.2.1 received in 28.32 ms

Completed jolly ping to 192.0.2.1

┏━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓
┃ Targets ┃ Transmitted ┃ Alive ┃ Unreachable ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩
│ 1       │ 1           │ 1     │ 0           │
└─────────┴─────────────┴───────┴─────────────┘
```

### Subnet

```console
# jollyip 2001:db8::/126
Starting jolly ping to 2001:db8::/126...

  Response from 2001:db8::1 received in 117.16 ms
  Response from 2001:db8::2 received in 102.13 ms
  2001:db8::3 is unreachable

Completed jolly ping to 2001:db8::/126
```

### Range

```console
# jollyip 192.0.2.1-6
Starting jolly ping to 192.0.2.1-6...

  Response from 192.0.2.1 received in 26.68 ms
  Response from 192.0.2.2 received in 26.52 ms
  Response from 192.0.2.3 received in 24.91 ms
  192.0.2.4 is unreachable
  192.0.2.5 is unreachable
  Response from 192.0.2.6 received in 30.06 ms

Completed jolly ping to 192.0.2.1-6

┏━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓
┃ Targets ┃ Transmitted ┃ Alive ┃ Unreachable ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩
│ 6       │ 6           │ 4     │ 2           │
└─────────┴─────────────┴───────┴─────────────┘
```

### Complex Range
```console
# jollyip 192.0.2.1,192.0.2.9-13,192.0.2.64/29
Starting jolly ping to 192.0.2.1,192.0.2.9-13,192.0.2.64/29...

  Response from 192.0.2.1 received in 29.96 ms
  192.0.2.9 is unreachable
  Response from 192.0.2.10 received in 26.49 ms
  Response from 192.0.2.11 received in 23.04 ms
  Response from 192.0.2.12 received in 25.28 ms
  192.0.2.13 is unreachable
  192.0.2.64 is unreachable
  192.0.2.65 is unreachable
  192.0.2.66 is unreachable
  192.0.2.67 is unreachable
  192.0.2.68 is unreachable
  192.0.2.69 is unreachable
  192.0.2.70 is unreachable
  192.0.2.71 is unreachable

Completed jolly ping to 192.0.2.1,192.0.2.9-13,192.0.2.64/29

┏━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓
┃ Targets ┃ Transmitted ┃ Alive ┃ Unreachable ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩
│ 14      │ 14          │ 4     │ 10          │
└─────────┴─────────────┴───────┴─────────────┘
```

### Mixing Protocols
```console
# jollyip 2001:db8::0/126,192.0.0.241,192.0.2.1-2

Starting jolly ping to 2001:db8::/126,192.0.0.241,192.0.2.1-2...

  Response from 2001:db8::1 received in 107.85 ms
  Response from 2001:db8::2 received in 112.27 ms
  2001:db8::3 is unreachable
  Response from 192.0.0.241 received in 43.93 ms
  Response from 192.0.2.1 received in 29.02 ms
  Response from 192.0.2.2 received in 25.38 ms

Completed jolly ping to 2001:db8::/126,192.0.0.241,192.0.2.1-2

┏━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓
┃ Targets ┃ Transmitted ┃ Alive ┃ Unreachable ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩
│ 7       │ 7           │ 5     │ 2           │
└─────────┴─────────────┴───────┴─────────────┘
```