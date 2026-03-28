# Celery + Redis Setup Guide

## Prerequisites

```bash
# Install Redis (Ubuntu/Debian)
sudo apt install redis-server
sudo systemctl start redis

# Install Python dependencies
pip install -r requirements.txt
```

## Running the full stack

Open 4 terminals:

```bash
# Terminal 1 — Flask API
python run.py

# Terminal 2 — Celery Worker
celery -A celery_app.celery worker --loglevel=info

# Terminal 3 — Celery Beat (scheduled jobs)
celery -A celery_app.celery beat --loglevel=info

# Terminal 4 — Flower monitor (optional)
celery -A celery_app.celery flower --port=5555
# Open http://localhost:5555 to monitor tasks
```

## Scheduled Jobs

| Job | Schedule | Trigger |
|-----|----------|---------|
| Interview Reminders | Daily 08:00 IST | Automatic via Beat |
| Monthly Placement Report | 1st of month 07:00 IST | Automatic via Beat |

## Manual Triggers (Admin panel)

- `POST /api/jobs/reminders/trigger` — fire reminders now
- `POST /api/jobs/report/trigger`    — generate report now

## User-triggered jobs

- `POST /api/jobs/export/student`  — student exports their history CSV
- `POST /api/jobs/export/company`  — company exports applicants CSV
- `GET  /api/jobs/status/<task_id>` — poll job state (PENDING/SUCCESS/FAILURE)
- `GET  /api/jobs/download/<filename>` — download generated file

## Environment Variables

```env
REDIS_URL=redis://localhost:6379/0
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-app-password
GCHAT_WEBHOOK_URL=https://chat.googleapis.com/...  # optional
```
