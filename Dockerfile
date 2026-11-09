FROM python:3.12-slim-bookworm

# Security: Install no extraneous packages, run as unprivileged user
RUN useradd -u 10001 -m -s /bin/bash nomaanos

WORKDIR /app

# Copy all 4 modules and orchestrator
COPY NomaanOS-Core /app/NomaanOS-Core
COPY NomaanOS-EvidenceLedger /app/NomaanOS-EvidenceLedger
COPY NomaanOS-GhostNode /app/NomaanOS-GhostNode
COPY NomaanOS-ShieldSOC /app/NomaanOS-ShieldSOC
COPY sas_orchestrator.py /app/sas_orchestrator.py

# Create ledger persistence directory with proper ownership
RUN mkdir -p /app/data && chown -R nomaanos:nomaanos /app

USER nomaanos

ENV PYTHONUNBUFFERED=1
ENV SAS_PORT=8080
ENV SAS_LEDGER_PATH=/app/data/audit_ledger.jsonl

EXPOSE 8080

CMD ["python", "sas_orchestrator.py"]
