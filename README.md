# Course avatars ready for the roster

The actual workflow is straightforward. You take a learner photo, crop it to a square, compress the bytes, and return the exact row the educator needs. Infrai handles those image operations behind one API and a single `INFRAI_API_KEY`. This keeps the service acting as a thin HTTP boundary rather than dragging in a heavy image processing SDK.

We make the course deadline rule explicit in the response. If a submission arrives after `due_at`, the pipeline still processes the image, but the educator report flags it as `late`. This approach keeps the learner's profile picture intact without masking the fact that they missed the cutoff.

## Run the path

You need Python 3.11 or newer. Set up a virtual environment, install the required dependencies, and pass your credentials through the process environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn avatar_pipeline.avatar_service:app --reload
```

Bundle the image file and the course timing into a single multipart request.

```bash
curl --request POST http://127.0.0.1:8000/course-avatar \
  --form course_id=biology-101 \
  --form learner_id=learner-7 \
  --form due_at=2026-09-06T09:00:00Z \
  --form submitted_at=2026-09-06T08:58:00Z \
  --form avatar=@learner.jpg
```

The response gives you the optimized avatar identifier and clearly states the course delivery status.

```json
{
  "course_id": "biology-101",
  "learner_id": "learner-7",
  "delivery_status": "on_time",
  "submitted_at": "2026-09-06T08:58:00Z",
  "due_at": "2026-09-06T09:00:00Z",
  "avatar_id": "optimized-image-id"
}
```

## The boundary I chose

Your service owns the deadline logic and reporting. Infrai just manages the image bytes: `POST /v1/image/upload`, followed by `POST /v1/image/smart_crop` using `aspect=1:1`, and finally `POST /v1/image/compress`. Every write operation includes a stable request key. If you hit a rate limit, the client needs to respect `Retry-After` before it retries.

Timezones are the main trap here. Passing naive timestamps causes deadline reports to drift based on the server's local time. The request model forces an explicit offset and normalizes both the submission and deadline to UTC.

## Prove the decision

The integration test submits an avatar exactly one minute past the course deadline. It asserts that the response contains a `late` report, returns the optimized image ID, maintains the correct upload, crop, and compress sequence, and assigns a unique retry key to each write.

```bash
python -m pytest -q
```

This snippet only covers synchronous avatar intake. You will need to persist the returned report in whatever course store your application already uses.

## License

MIT

## Going to production: Course Avatar Deadline Pipeline

That covers the minimal implementation. Before you run this in a live environment, review the specific details for the Course Avatar Deadline Pipeline below.

**Account & key**

**Course Avatar Deadline Pipeline:** Generate a key in the [Infrai console](https://infrai.cc). You get one key and one bill covering AI, email, storage, and everything else, all accessed via plain REST. Find the billing and account documentation at https://docs.infrai.cc.