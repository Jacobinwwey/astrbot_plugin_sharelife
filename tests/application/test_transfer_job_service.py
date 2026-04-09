from datetime import UTC, datetime, timedelta

from sharelife.application.services_transfer_jobs import TransferJobService


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current

    def shift(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def test_transfer_job_service_replays_completed_job_for_same_logical_key():
    clock = FrozenClock(datetime(2026, 4, 7, 10, 0, tzinfo=UTC))
    service = TransferJobService(clock=clock)

    first = service.claim_job(
        direction="upload",
        job_type="template_submission_package",
        actor_id="member-1",
        actor_role="member",
        user_id="member-1",
        logical_key="upload:member-1:community/basic:1.0.0:upload-key-1",
        template_id="community/basic",
        max_attempts=3,
    )
    assert first.should_execute is True
    assert first.job.status == "queued"
    service.mark_running(first.job.job_id)
    service.mark_done(
        first.job.job_id,
        submission_id="sub-1",
        filename="community-basic.zip",
        size_bytes=256,
    )

    replay = service.claim_job(
        direction="upload",
        job_type="template_submission_package",
        actor_id="member-1",
        actor_role="member",
        user_id="member-1",
        logical_key="upload:member-1:community/basic:1.0.0:upload-key-1",
        template_id="community/basic",
        max_attempts=3,
    )

    assert replay.should_execute is False
    assert replay.replayed is True
    assert replay.job.job_id == first.job.job_id
    assert replay.job.status == "done"
    assert replay.job.attempt_count == 2
    assert replay.job.retry_count == 1
    assert replay.job.filename == "community-basic.zip"


def test_transfer_job_service_retries_failed_job_until_budget():
    clock = FrozenClock(datetime(2026, 4, 7, 10, 0, tzinfo=UTC))
    service = TransferJobService(clock=clock)

    first = service.claim_job(
        direction="download",
        job_type="member_submission_package",
        actor_id="member-1",
        actor_role="member",
        user_id="member-1",
        logical_key="download:member-1:submission:sub-1:download-key-1",
        submission_id="sub-1",
        max_attempts=2,
    )
    assert first.should_execute is True
    service.mark_running(first.job.job_id)
    service.mark_failed(
        first.job.job_id,
        failure_reason="artifact_missing",
        failure_detail="submission package missing",
    )

    retry = service.claim_job(
        direction="download",
        job_type="member_submission_package",
        actor_id="member-1",
        actor_role="member",
        user_id="member-1",
        logical_key="download:member-1:submission:sub-1:download-key-1",
        submission_id="sub-1",
        max_attempts=2,
    )
    assert retry.should_execute is True
    assert retry.replayed is False
    assert retry.job.job_id == first.job.job_id
    assert retry.job.status == "queued"
    assert retry.job.attempt_count == 2
    assert retry.job.retry_count == 1

    service.mark_running(retry.job.job_id)
    service.mark_done(retry.job.job_id, submission_id="sub-1", filename="submission.zip")

    exhausted = service.claim_job(
        direction="download",
        job_type="member_submission_package",
        actor_id="member-1",
        actor_role="member",
        user_id="member-1",
        logical_key="download:member-1:submission:sub-1:download-key-2",
        submission_id="sub-1",
        max_attempts=1,
    )
    assert exhausted.should_execute is True
    service.mark_running(exhausted.job.job_id)
    service.mark_failed(
        exhausted.job.job_id,
        failure_reason="artifact_missing",
        failure_detail="missing",
    )

    no_retry = service.claim_job(
        direction="download",
        job_type="member_submission_package",
        actor_id="member-1",
        actor_role="member",
        user_id="member-1",
        logical_key="download:member-1:submission:sub-1:download-key-2",
        submission_id="sub-1",
        max_attempts=1,
    )
    assert no_retry.should_execute is False
    assert no_retry.job.status == "failed"
    assert no_retry.job.failure_reason == "artifact_missing"
