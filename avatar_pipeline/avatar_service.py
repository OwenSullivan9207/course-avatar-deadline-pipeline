from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .course_avatar import AvatarSubmission, EducatorAvatarReport, prepare_course_avatar
from .infrai_images import InfraiError, InfraiImages


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    images = InfraiImages()
    application.state.images = images
    yield
    images.close()


app = FastAPI(title="Course avatar intake", lifespan=lifespan)


@app.exception_handler(InfraiError)
async def infrai_error_handler(_request: object, exc: InfraiError) -> JSONResponse:
    status = exc.status_code if 400 <= exc.status_code < 500 else 502
    return JSONResponse(status_code=status, content={"detail": {"code": exc.code, "error": exc.detail}})


@app.post("/course-avatar", response_model=EducatorAvatarReport)
async def submit_course_avatar(
    course_id: str = Form(),
    learner_id: str = Form(),
    due_at: str = Form(),
    submitted_at: str = Form(),
    avatar: UploadFile = File(),
) -> EducatorAvatarReport:
    submission = AvatarSubmission(
        course_id=course_id,
        learner_id=learner_id,
        due_at=due_at,
        submitted_at=submitted_at,
    )
    content = await avatar.read()
    if not content:
        raise HTTPException(status_code=400, detail="avatar must not be empty")
    return prepare_course_avatar(
        submission,
        avatar.filename or "avatar",
        content,
        app.state.images,
    )
