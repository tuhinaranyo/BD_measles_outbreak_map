# Deployment Guide

This app is a Streamlit Python service with a SQLite database and saved PDF files. It needs a running Python server, so it cannot run directly on Cloudflare Pages as a static website.

## Best Hosting Choices

- **Oracle Cloud Free VM**: good free option for a small always-on dashboard.
- **Amazon Lightsail / EC2**: simple paid VPS option.
- **Google Cloud Run**: good container option, but use a mounted volume or external storage if you want PDFs and SQLite to persist.
- **Streamlit Community Cloud**: easiest free public option from GitHub, but scheduled PDF downloading may need manual admin refresh or an external scheduler.
- **Cloudflare**: use Cloudflare DNS/Tunnel in front of the app, not Cloudflare Pages for the Streamlit backend.

## Environment Variables

| Name | Default | Purpose |
| --- | --- | --- |
| `MEASLES_DATA_DIR` | `./data` | Folder for `measles.db`, downloaded PDFs, and extracted debug files. Set this to a persistent disk path in production. |

## Docker

Build and run:

```bash
docker build -t bd-measles-dashboard .
docker run -p 8501:8501 -v measles-data:/app/data bd-measles-dashboard
```

Open:

```text
http://localhost:8501
http://localhost:8501/admin
```

With Docker Compose:

```bash
docker compose up -d --build
```

## VPS Setup

On a Linux VPS:

```bash
git clone https://github.com/tuhinaranyo/BD_measles_outbreak_map.git
cd BD_measles_outbreak_map
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
MEASLES_DATA_DIR=/var/lib/bd-measles ./.venv/bin/python update_data.py
MEASLES_DATA_DIR=/var/lib/bd-measles ./.venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

For a permanent service, run it with Docker Compose, systemd, or a hosting panel such as Coolify.

## Daily Updates

The app can check for new DGHS PDFs from the admin page. For automatic daily updates, schedule:

```bash
cd /path/to/BD_measles_outbreak_map
MEASLES_DATA_DIR=/var/lib/bd-measles ./.venv/bin/python update_data.py
```

Example Linux cron, every day at 8:30 PM Bangladesh time:

```cron
30 20 * * * cd /path/to/BD_measles_outbreak_map && MEASLES_DATA_DIR=/var/lib/bd-measles ./.venv/bin/python update_data.py >> /var/log/bd-measles-update.log 2>&1
```

## Cloudflare Domain

If the app runs on a VM, point your domain through Cloudflare DNS to the VM IP, or use Cloudflare Tunnel:

```bash
cloudflared tunnel --url http://localhost:8501
```

Cloudflare Pages is useful for static React/HTML sites. This project has a Python backend, PDF downloader, SQLite database, and admin editor, so it should be hosted as a server app.
