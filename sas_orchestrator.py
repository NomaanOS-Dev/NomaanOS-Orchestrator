import os
import sys
import json
import time
import uuid
import hashlib
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Setup relative paths to the 4 modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "NomaanOS-Core", "src"))
sys.path.insert(0, os.path.join(BASE_DIR, "NomaanOS-EvidenceLedger"))
sys.path.insert(0, os.path.join(BASE_DIR, "NomaanOS-GhostNode"))
sys.path.insert(0, os.path.join(BASE_DIR, "NomaanOS-ShieldSOC"))

from engine import NoseExec
from ledger_persistent import PersistentEvidenceLedger
from ghost_core import compute_hmac_signature, SWARM_SECRET_KEY, ClusterRegistry, MAX_TIMESTAMP_DRIFT_SEC
import hmac
from host_telemetry import get_genuine_telemetry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SAS-ORCHESTRATOR] %(message)s"
)

ORCHESTRATOR_PORT = int(os.environ.get("SAS_PORT", 8080))
LEDGER_STORAGE = os.environ.get("SAS_LEDGER_PATH", os.path.join(BASE_DIR, "audit_ledger.jsonl"))

# Singletons
cluster_registry = ClusterRegistry()
sandbox_engine = NoseExec(allowed_binaries=["whoami", "hostname", "uname", "echo", "date", "uptime"])
evidence_ledger = PersistentEvidenceLedger(LEDGER_STORAGE)

class SASRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            telemetry = get_genuine_telemetry()
            payload = {
                "status": "OPERATIONAL",
                "enclave_mode": "FAIL_CLOSED",
                "ledger_blocks": len(evidence_ledger.chain),
                "telemetry": telemetry
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/execute":
            try:
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length).decode("utf-8"))

                # 1. Zero-Trust HMAC Authentication
                sig = req.get("signature")
                ts = req.get("timestamp")
                nonce = req.get("nonce")
                cmd = req.get("cmd", [])

                if not (sig and ts and nonce and cmd):
                    self._reject(400, "Missing required cryptographic handshake parameters")
                    return

                if abs(time.time() - float(ts)) > MAX_TIMESTAMP_DRIFT_SEC:
                    self._reject(403, "Timestamp expired: Replay window exceeded")
                    return

                if not cluster_registry.is_valid_nonce(str(nonce)):
                    self._reject(403, "Nonce replay detected: Fail-Closed enforcement")
                    return

                raw_data = json.dumps({"cmd": cmd})
                expected_sig = compute_hmac_signature(SWARM_SECRET_KEY, float(ts), str(nonce), raw_data)
                if not hmac.compare_digest(sig, expected_sig):
                    self._reject(403, "Cryptographic signature mismatch")
                    return

                # 2. Sandboxed Fail-Closed Execution
                exec_res = sandbox_engine.execute(cmd)
                
                # 3. Telemetry & Tamper-Proof Cryptographic Attestation
                telemetry = get_genuine_telemetry()
                event_block = {
                    "nonce": nonce,
                    "timestamp": ts,
                    "cmd": cmd,
                    "exec_result": exec_res,
                    "telemetry": telemetry
                }
                event_hash = hashlib.sha256(json.dumps(event_block, sort_keys=True).encode("utf-8")).hexdigest()
                ledger_record = evidence_ledger.record_evidence("sas_command_execution", event_hash)

                # 4. Return Verified Response
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response_payload = {
                    "status": "SUCCESS",
                    "execution": exec_res,
                    "attestation": {
                        "block_index": ledger_record["index"],
                        "block_hash": ledger_record["current_hash"],
                        "prev_hash": ledger_record["previous_hash"]
                    }
                }
                self.wfile.write(json.dumps(response_payload).encode("utf-8"))

            except Exception as e:
                self._reject(500, f"Internal Enclave Error: {str(e)}")
            return

        self.send_response(404)
        self.end_headers()

    def _reject(self, code: int, reason: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "BLOCKED", "reason": reason}).encode("utf-8"))

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    logging.info(f"Sovereign AI Stack (SAS) Unified Orchestrator listening on port {ORCHESTRATOR_PORT}")
    logging.info(f"Active audit ledger: {LEDGER_STORAGE}")
    server = HTTPServer(("0.0.0.0", ORCHESTRATOR_PORT), SASRequestHandler)
    server.serve_forever()
