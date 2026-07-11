# శ్రావణి — Sraavani

A free Telugu audio streaming platform supporting music, podcasts, audiobooks, and stories.
Built with FastAPI (Python) + Jinja2 + PostgreSQL + AWS S3/CloudFront.

**Live:** https://telugu-audio-platform-production.up.railway.app

---

## Features

- 🎵 Stream music, podcasts, audiobooks, and stories
- 📖 Multi-chapter audiobooks with auto-play next chapter
- 🔍 Search by keyword, author, tag, year range, content type
- 🌐 Bilingual Telugu/English UI (toggle in navbar)
- 👤 Google OAuth login (Facebook/OTP coming soon)
- 📚 Favourites, listen history, resume from last position
- ⚙️ User preferences — language + preferred content types
- 🎛️ Admin panel — upload multiple files at once, publish/unpublish
- 📱 PWA — installable on Android and iOS home screen

---

## Quick Start (local development)

```bash
git clone https://github.com/mvkrishna86/telugu-audio-platform.git
cd telugu-audio-platform
python3 -m venv .venv
source .venv/bin/activate
pip install --index-url https://pypi.org/simple/ -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn app.main:app --reload
```

Open http://localhost:8000

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase publishable key |
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret |
| `AWS_REGION` | e.g. `ap-south-1` |
| `S3_BUCKET_NAME` | S3 bucket name |
| `CLOUDFRONT_DOMAIN` | CloudFront distribution URL |
| `CLOUDFRONT_KEY_PAIR_ID` | CloudFront key pair ID |
| `CLOUDFRONT_PRIVATE_KEY_B64` | Base64-encoded RSA private key |
| `CLOUDFRONT_PRIVATE_KEY_PATH` | `./cloudfront_private_key.pem` |
| `APP_SECRET_KEY` | Random secret for session signing |
| `APP_BASE_URL` | Full URL of your deployment |

---

## Project Structure

```
app/
  main.py              FastAPI entry point
  config.py            Environment variable reads
  db.py                psycopg2 helpers (query/query_one/execute)
  auth.py              Session helpers, role guards
  storage.py           S3 upload + CloudFront signed URLs
  lang.py              Bilingual support helpers
  routes/
    home.py            Home + browse pages
    content.py         Content detail, /api/play/, /api/position
    search.py          Search with filters
    library.py         Favourites + history
    auth_routes.py     Login/logout/OAuth/lang toggle
    admin.py           Admin upload, add-parts, publish, delete
    preferences.py     User preferences
  templates/           Jinja2 HTML templates
  static/
    css/style.css      Dark purple theme
    js/player.js       Audio player + auto-next chapter
    manifest.json      PWA manifest
    sw.js              Service worker
database/
  schema.sql           Run this in Railway/PostgreSQL to set up tables
```

---

## Database Setup

Run `database/schema.sql` in your PostgreSQL instance (Railway SQL console or psql).

---

## Making an Account Admin

Run in PostgreSQL:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
-- or for full superadmin access:
UPDATE users SET role = 'superadmin' WHERE email = 'your@email.com';
```

---

## Deployment (Railway)

1. Push to GitHub → Railway auto-deploys via Dockerfile
2. Set all environment variables in Railway → Variables tab
3. The CloudFront private key is stored as `CLOUDFRONT_PRIVATE_KEY_B64` (base64) and decoded at startup

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Templates | Jinja2 + HTMX |
| Auth | Supabase Auth (Google OAuth + Email) |
| Database | PostgreSQL (Railway managed) |
| File storage | AWS S3 (private bucket) |
| CDN | AWS CloudFront (signed URLs) |
| Telugu font | Noto Sans Telugu (Google Fonts) |
| Mobile | PWA (installable on Android + iOS) |
| Hosting | Railway.app |

---

## Future Plans

- Facebook + Phone OTP login
- Custom domain
- Native Android/iOS app (Expo)
- User-created playlists
- Comments and ratings
- Recommendations engine
