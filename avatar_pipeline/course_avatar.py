from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

from pydantic import BaseModel, Field


class ImageOperations(Protocol):
    def upload(self, content: bytes, filename: str, request_key: str) -> Mapping[str, Any]:
        raise AssertionError("Protocol method")

    def smart_crop(self, image: str, aspect: str, request_key: str) -> Mapping[str, Any]:
        raise AssertionError("Protocol method")

    def compress(self, image: str, request_key: str) -> Mapping[str, Any]:
        raise AssertionError("Protocol method")


class AvatarSubmission(BaseModel):
    course_id: str = Field(min_length=1)
    learner_id: str = Field(min_length=1)
    due_at: datetime
    submitted_at: datetime


class EducatorAvatarReport(BaseModel):
    course_id: str
    learner_id: str
    delivery_status: str
    submitted_at: datetime
    due_at: datetime
    avatar_id: str


def prepare_course_avatar(
    submission: AvatarSubmission,
    filename: str,
    content: bytes,
    images: ImageOperations,
) -> EducatorAvatarReport:
    due_at = _utc(submission.due_at)
    submitted_at = _utc(submission.submitted_at)
    request_root = f"avatar:{submission.course_id}:{submission.learner_id}:{submitted_at.isoformat()}"

    uploaded = images.upload(content, filename, f"{request_root}:upload")
    cropped = images.smart_crop(_image_ref(uploaded), "1:1", f"{request_root}:crop")
    optimized = images.compress(_image_ref(cropped), f"{request_root}:compress")

    return EducatorAvatarReport(
        course_id=submission.course_id,
        learner_id=submission.learner_id,
        delivery_status="on_time" if submitted_at <= due_at else "late",
        submitted_at=submitted_at,
        due_at=due_at,
        avatar_id=_image_ref(optimized),
    )


def _image_ref(result: Mapping[str, Any]) -> str:
    image_id = result.get("id")
    if not isinstance(image_id, str) or not image_id:
        raise RuntimeError("Image operation did not return an id")
    return image_id


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Deadline timestamps must include a timezone")
    return value.astimezone(timezone.utc)
