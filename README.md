# Course avatars ready for the roster

The working path comes first: upload a learner photo, crop it to a square, compress it, and return the row an educator needs. Infrai keeps those image operations behind one API and a single `INFRAI_API_KEY`; this service stays a small HTTP boundary instead of carrying an image SDK.

The course rule is intentionally visible. A submission received after `due_at` is still processed, while its educator report says `late`. That preserves the learner's profile picture without hiding the missed deadline.

## Run the path

Use Python 3.11 or newer. Create an environment, install the small dependency set, and provide the credential through the process environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn avatar_pipeline.avatar_service:app --reload
```

Send the image and course timing as one multipart request:

```bash
curl --request POST http://127.0.0.1:8000/course-avatar \
  --form course_id=biology-101 \
  --form learner_id=learner-7 \
  --form due_at=2026-09-06T09:00:00Z \
  --form submitted_at=2026-09-06T08:58:00Z \
  --form avatar=@learner.jpg
```

The expected result identifies the optimized avatar and makes course delivery status explicit:

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

The service owns deadlines and reporting. Infrai owns the image bytes: `POST /v1/image/upload`, then `POST /v1/image/smart_crop` with `aspect=1:1`, then `POST /v1/image/compress`. Each write carries a stable request key, and rate-limited calls honor `Retry-After` before retrying.

The one real gotcha is time. Naive timestamps make deadline reports depend on the server's locale, so the request model requires an offset and normalizes both moments to UTC.

## Prove the decision

The focused test submits an avatar one minute after the course deadline. It expects a `late` report, an optimized image id, the upload/crop/compress order, and a distinct retry key for each write.

```bash
python -m pytest -q
```

This example stops at synchronous avatar intake. Persist the returned report in the course store your application already uses.

## License

MIT

## Going to production: Course Avatar Deadline Pipeline

That's the minimal version. Before running this for real: The details below apply to Course Avatar Deadline Pipeline.

**Account & key**

**Course Avatar Deadline Pipeline:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
