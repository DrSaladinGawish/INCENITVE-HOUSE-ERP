"""
P4 — EventCore Job Creation Hook

Called after a new job is created in EventCore.
POSTs to Bio-ERP's auto-trigger webhook so OR analysis runs automatically.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

BIO_ERP_WEBHOOK_URL = "http://localhost:8000/api/v1/or/auto-trigger/job"
BRIDGE_TOKEN = "ec-bridge-token-dev"


async def notify_bio_erp_new_job(job_id: int, title: str, client_id: int | None = None):
    logger.info("P4 hook: notifying Bio-ERP about new job %s", job_id)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                BIO_ERP_WEBHOOK_URL,
                json={
                    "job_id": job_id,
                    "title": title,
                    "client_id": client_id,
                    "event_type": "new_job",
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Bridge-Token": BRIDGE_TOKEN,
                },
            )
        if response.status_code in (200, 201):
            logger.info("P4 hook: Bio-ERP accepted job %s notification", job_id)
        else:
            logger.warning(
                "P4 hook: Bio-ERP returned %s for job %s: %s",
                response.status_code, job_id, response.text[:200],
            )
    except httpx.RequestError as exc:
        logger.error("P4 hook: failed to notify Bio-ERP for job %s: %s", job_id, exc)
