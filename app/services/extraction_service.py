"""Excel extraction service wrapping legacy extraction_engine."""
import asyncio
import os
from typing import Optional


async def extract_and_stage(source_paths: Optional[dict] = None):
    loop = asyncio.get_event_loop()
    from extraction_engine import run_extraction
    return await loop.run_in_executor(None, run_extraction, source_paths)
