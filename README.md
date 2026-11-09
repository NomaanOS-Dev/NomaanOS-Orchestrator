# Sovereign AI Stack (SAS)

An air-gapped, zero-trust execution runtime with cryptographic auditability and hardware telemetry designed for autonomous AI agents.

## Architecture

The stack coordinates four security pillars to enforce fail-closed runtime integrity:

1. **Gatekeeper (`NomaanOS-GhostNode`)**: Enforces HMAC-SHA256 authenticated ingress, monotonic nonce tracking (replay defense), and 60-second timestamp drift windows.
2. **Sandbox Engine (`NomaanOS-Core / NoseExec`)**: Sandboxed runtime with strict binary allowlisting, path sanitization, and fail-closed subshell isolation.
3. **Hardware Telemetry (`NomaanOS-ShieldSOC`)**: Host observability module that collects genuine hardware metrics and degrades safely when sysfs sensors are unavailable.
4. **Attestation (`NomaanOS-EvidenceLedger`)**: Tamper-evident, append-only Merkle-style hash-chain with fail-closed cold-storage load validation (`LedgerIntegrityError`).

## Quick Start

### 1. Ingress Health Probe
```bash
curl -s http://localhost:8080/health
python test_attacks.py
docker compose up --build -d

Security Invariants
Zero Plaintext Bearer Tokens: All control payloads require HMAC-SHA256 signatures with single-use UUID nonces.

Fail-Closed Execution: Any violation in binary allowlists or execution paths terminates immediately without side effects.

Tamper-Evident Ledger: Modification of on-disk audit records invalidates subsequent cryptographic hash links and halts initialization.
