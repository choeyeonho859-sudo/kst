# KST Website

A responsive, dark-themed starter website for KST with:
- Home page and artist roster
- Music submission form
- SQLite submission storage
- Optional Discord webhook notifications
- Password-protected admin page for reviewing submissions
- `/health` endpoint for uptime monitoring

## Run locally

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables before running:

**Windows PowerShell**
```powershell
$env:SECRET_KEY="replace-with-a-long-random-secret"
$env:ADMIN_PASSWORD="choose-a-strong-unique-password"
python app.py
```

**macOS/Linux**
```bash
export SECRET_KEY="replace-with-a-long-random-secret"
export ADMIN_PASSWORD="choose-a-strong-unique-password"
python app.py
```

Open `http://127.0.0.1:5000`.

## Publish it for 24/7 access

1. Create a private GitHub repository and upload these project files.
2. Create a web service on Render and connect that repository.
3. Use the settings in `render.yaml`, or set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn wsgi:app --workers 2 --threads 4 --timeout 60`
   - Health check path: `/health`
4. Set environment variables in the host dashboard:
   - `SECRET_KEY`: a long, random secret
   - `ADMIN_PASSWORD`: a strong, unique password
   - `DISCORD_WEBHOOK_URL`: optional Discord webhook URL
5. Choose an **always-on paid instance** if you need the website to stay available continuously. Free hosting tiers may sleep, restart, or have limited persistent storage.
6. Confirm the deployed `/health` URL returns `{"status":"ok","service":"KST website"}`.

## Important hosting note

This starter uses SQLite for simplicity. On many cloud hosts, the local filesystem can be temporary and may be reset during redeploys. For real public use, attach a persistent disk or move submissions to a managed PostgreSQL database. Do not rely on a free-tier service for guaranteed 24/7 uptime.

## Edit the artist list

Update the `artists` lists in `app.py`. Replace the sample entries with confirmed artist names and descriptions.

## Discord notifications

Create a webhook in the channel where submissions should be announced, then set `DISCORD_WEBHOOK_URL` as a server environment variable. Never publish the webhook URL in GitHub or in frontend code; anyone who obtains it may be able to post to that channel.

## Admin

Visit `/admin/login`. The password comes from the `ADMIN_PASSWORD` environment variable. This is a basic starter admin panel, not a complete multi-user moderation system.
