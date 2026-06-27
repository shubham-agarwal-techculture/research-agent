"""Twice-daily scheduler service."""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from research_agent.config import AppConfig
from research_agent.pipeline import ResearchPipeline

logger = logging.getLogger(__name__)


def _parse_run_time(value: str) -> tuple[int, int]:
    hour_str, minute_str = value.split(":", 1)
    return int(hour_str), int(minute_str)


class SchedulerService:
    def __init__(self, config: AppConfig, pipeline: ResearchPipeline) -> None:
        self.config = config
        self.pipeline = pipeline
        self.scheduler = BlockingScheduler(timezone=ZoneInfo(config.timezone))

    def _run_all_job(self) -> None:
        logger.info("Scheduled research run triggered")
        runs = self.pipeline.run_all_active()
        logger.info("Scheduled run finished: %s topic(s) processed", len(runs))

    def start(self) -> None:
        for index, run_time in enumerate(self.config.scheduler.run_times):
            hour, minute = _parse_run_time(run_time)
            self.scheduler.add_job(
                self._run_all_job,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=f"research-run-{index}",
                replace_existing=True,
            )
            logger.info("Scheduled daily run at %s (%s)", run_time, self.config.timezone)

        logger.info("Scheduler started. Press Ctrl+C to stop.")
        self.scheduler.start()
