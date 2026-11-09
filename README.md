# Sovereign AI Stack (SAS)

Sovereign AI Stack (SAS) is an air-gapped, zero-trust execution runtime for autonomous AI agents. It combines authenticated ingress, fail-closed execution, hardware telemetry, and cryptographic attestation to create a verifiable enclave-like control plane.

## Overview

The orchestrator coordinates four security components:

1. NomaanOS-GhostNode — enforces HMAC-SHA256 authenticated ingress, replay protection, and timestamp drift checks.
2. NomaanOS-Core / NoseExec — runs sandboxed commands with strict binary allowlisting and fail-closed execution behavior.
3. NomaanOS-ShieldSOC — collects genuine host telemetry and safely falls back when sensors are unavailable.
4. NomaanOS-EvidenceLedger — records tamper-evident audit evidence in an append-only, hash-linked ledger.

This repository acts as the runtime orchestrator and integration point for the SAS stack.

## Repository layout

- `sas_orchestrator.py` — HTTP entry point that exposes health and execution endpoints.
- `docker-compose.yml` — local container orchestration for the enclave service.
- `Dockerfile` — runtime image definition for the orchestrator.
- `ARCHITECTURE.md` — architecture and dataflow details.
- `NomaanOS-Core/` — sandbox runtime submodule.
- `NomaanOS-GhostNode/` — ingress gateway / validation submodule.
- `NomaanOS-ShieldSOC/` — telemetry submodule.
- `NomaanOS-EvidenceLedger/` — attestation ledger submodule.

## Security invariants

- Zero plaintext bearer tokens: all control payloads require HMAC-SHA256 signatures with nonce and timestamp validation.
- Fail-closed execution: disallowed binaries, path traversal, or invalid execution paths halt without side effects.
- Tamper-evident ledger: any revision to on-disk evidence breaks the hash chain and invalidates subsequent attestation.

## Quick start

### Prerequisites

- Docker and Docker Compose
- Git with submodules enabled

### Clone and initialize submodules

```bash
git clone https://github.com/NomaanOS-Dev/NomaanOS-Orchestrator.git
cd NomaanOS-Orchestrator
git submodule update --init --recursive
```

### Run locally

```bash
docker compose up --build -d
```

### Health check

```bash
curl -s http://localhost:8080/health
```

Example response:

```json
{
  "status": "OPERATIONAL",
  "enclave_mode": "FAIL_CLOSED",
  "ledger_blocks": 0,
  "telemetry": {
    "arch": "x86_64",
    "os": "Linux",
    "kernel": "5.15.0"
  }
}
```

### Execute a signed command

The `/execute` endpoint expects a JSON payload with:

- `cmd`: list of command arguments
- `timestamp`: Unix timestamp
- `nonce`: unique nonce value
- `signature`: HMAC-SHA256 signature over the payload using the configured swarm secret

Example:

```bash
curl -X POST http://localhost:8080/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "cmd": ["echo", "hello"],
    "timestamp": 1730000000,
    "nonce": "4b5650d5-7dd4-4f16-93d0-4f0d5d42f8b6",
    "signature": "<hmac-sha256-signature>"
  }'
```

## Architecture summary

The orchestrator acts as the unified runtime boundary:

```text
Autonomous Client / Agent
        |
        v
HMAC-SHA256 + Nonce + Timestamp
        |
        v
NomaanOS-GhostNode (Ingress Validation)
        |
        v
NomaanOS-Core (NoseExec Sandbox)
        |
        v
NomaanOS-ShieldSOC (Telemetry Probe)
        |
        v
NomaanOS-EvidenceLedger (Cryptographic Attestation)
```

## Notes

- The stack is intentionally designed to degrade safely and fail closed when telemetry or validation checks cannot be completed.
- The orchestrator listens on port `8080` by default.
- The ledger is stored in an append-only JSONL file or configured runtime path.

## Related docs

- `ARCHITECTURE.md` — system design and pipeline flow
- `docker-compose.yml` — local deployment configuration
- `Dockerfile` — runtime packaging
