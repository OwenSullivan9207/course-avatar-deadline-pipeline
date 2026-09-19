from datetime import datetime, timezone
from typing import Any, Mapping

from avatar_pipeline.course_avatar import AvatarSubmission, prepare_course_avatar


class RecordingImages:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def upload(self, content: bytes, filename: str, request_key: str) -> Mapping[str, Any]:
        self.calls.append(("upload", (content, filename, request_key)))
        return {"id": "uploaded-image"}

    def smart_crop(self, image: str, aspect: str, request_key: str) -> Mapping[str, Any]:
        self.calls.append(("smart_crop", (image, aspect, request_key)))
        return {"id": "square-image"}

    def compress(self, image: str, request_key: str) -> Mapping[str, Any]:
        self.calls.append(("compress", (image, request_key)))
        return {"id": "optimized-image"}


def test_late_avatar_is_processed_and_visible_in_educator_report() -> None:
    images = RecordingImages()
    submission = AvatarSubmission(
        course_id="biology-101",
        learner_id="learner-7",
        due_at=datetime(2026, 9, 6, 9, 0, tzinfo=timezone.utc),
        submitted_at=datetime(2026, 9, 6, 9, 1, tzinfo=timezone.utc),
    )

    report = prepare_course_avatar(submission, "profile.jpg", b"photo", images)

    assert report.delivery_status == "late"
    assert report.avatar_id == "optimized-image"
    assert [call[0] for call in images.calls] == ["upload", "smart_crop", "compress"]
    assert images.calls[1][1][1] == "1:1"
    keys = [call[1][-1] for call in images.calls]
    assert len(keys) == len(set(keys))
