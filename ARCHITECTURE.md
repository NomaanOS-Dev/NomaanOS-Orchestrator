# Sovereign AI Stack (SAS) - Architecture Specification

A modular, zero-trust execution sandbox with cryptographic attestation and fail-closed ingress for autonomous AI systems.

## Dataflow Pipeline
[ Autonomous Client / Agent ]
│
▼ (HMAC-SHA256 + Nonce + Timestamp)
┌──────────────────────────────────────────┐
│  NomaanOS-GhostNode (Ingress Gateway)     │
│  - Replay Defense (Nonce Tracking)       │
│  - Drift Enforcement (<= 60s window)     │
└─────────────────────┬────────────────────┘
│ Validated
▼
┌──────────────────────────────────────────┐
│  NomaanOS-Core (NoseExec Sandbox)        │
│  - Binary Allowlist Enforcement          │
│  - Sanitized Enclave Environment         │
│  - Non-Zero Exit Code Fail-Closed        │
└─────────────────────┬────────────────────┘
│ Execution Output + Telemetry Probe
▼
┌──────────────────────────────────────────┐
│  NomaanOS-ShieldSOC (Hardware Probe)     │
│  - Genuine Host Architecture Metrics     │
│  - Fail-safe Kernel Fallbacks            │
└─────────────────────┬────────────────────┘
│ Canonical Event Digest
▼
┌──────────────────────────────────────────┐
│  NomaanOS-EvidenceLedger (Cryptographic) │
│  - Append-Only Merkle Hash Chain         │
│  - LedgerIntegrityError on Cold Tamper   │
└──────────────────────────────────────────┘
## Security Invariants

1. **Ingress:** Zero unauthenticated execution. Bearer tokens rejected in favor of signed payloads.
2. **Execution:** Path traversal, subshell injection, and unlisted binaries fail-closed.
3. **Attestation:** State modification without prior block consensus violates ledger hash invariants.
