# తెలుగు వినండి — Telugu Audio Platform

A free Telugu audio streaming platform supporting music, podcasts, audiobooks, and stories.
Built with FastAPI (Python) + HTMX + Supabase + AWS S3/CloudFront.

---

## Quick Start (local development)

### 1. Clone and set up environment
```bash
git clone https://github.com/mvkrishna86/telugu-audio-platform.git
cd telugu-audio-platform
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in your Supabase and AWS credentials
```

### 2. Set up the database
- Go to your Supabase project → SQL Editor
- Paste and run the contents of `database/schema.sql`

### 3. Set up AWS S3 + CloudFront
- Create an S3 bucket (block all public access)
- Create a CloudFront distribution pointing to the bucket
- Create a CloudFront key pair and download the private key (`.pem`)
- Set `CLOUDFRONT_PRIVATE_KEY_PATH` in `.env` to the path of the `.pem` file

### 4. Set up Supabase Auth
- In Supabase → Authentication → Providers: enable Google, Facebook, Phone
- Add `http://localhost:8000/auth/callback` to allowed redirect URLs

### 5. Run the app
```bash
uvicorn app.main:app --reload
```
Open http://localhost:8000

---

## Project Structure

```
app/
  main.py              # FastAPI app entry
  config.py            # All environment variable reads
  db.py                # Supabase client
  auth.py              # Session helpers + role checks
  storage.py           # S3 upload + CloudFront signed URLs
  routes/
    home.py            # Home + browse pages
    content.py         # Content detail + play API
    search.py          # Search
    library.py         # Bookmarks + history
    auth_routes.py     # Login / logout / OAuth callback
    admin.py           # Admin upload + management
  templates/           # Jinja2 HTML templates (Telugu UI)
  static/
    css/style.css      # Dark theme with Telugu font
    js/player.js       # Audio player + position save
    manifest.json      # PWA manifest
    sw.js              # Service worker (offline shell)
database/
  schema.sql           # PostgreSQL schema — run in Supabase
```

---

## Deployment (Railway.app)

1. Push this repo to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Add all environment variables from `.env.example`
4. Railway auto-detects the `Dockerfile` and deploys

---

## Making someone an Admin

Run this in Supabase SQL Editor (replace the email):

```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12) |
| Templates | Jinja2 + HTMX |
| Auth | Supabase Auth (Google, Facebook, Phone OTP, Email) |
| Database | Supabase (PostgreSQL) |
| File storage | AWS S3 |
| CDN | AWS CloudFront (signed URLs) |
| Telugu font | Noto Sans Telugu (Google Fonts) |
| Mobile | PWA (installable on Android + iOS) |
