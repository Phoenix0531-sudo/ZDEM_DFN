# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 1.1.x   | ✅ |
| < 1.1   | ❌ (upgrade; pre-split releases have known config hazards) |

## Reporting a vulnerability

This package reads particle files and writes local outputs; it performs no
network I/O and no unprivileged-elevation paths. Still, if you find a
security-relevant defect (e.g. a crafted input file causing arbitrary path
writes or code execution), please report it responsibly:

1. Use GitHub **Private vulnerability reporting** on this repository
   (Security tab → Report a vulnerability), or
2. Open an issue **without** exploit details if private reporting is
   unavailable, and we will coordinate disclosure.

Please do not open public issues containing exploit payloads.
