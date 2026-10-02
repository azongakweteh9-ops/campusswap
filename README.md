# CampusSwap

A web site for buying, selling, lending and borrowing study materials on campus.
Flask + SQLite backend, plain HTML/CSS/JS front end.

## Quick start (after extracting the zip)
Requires Python 3.9 or newer.
```
cd campusswap
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 in your browser. The database file is created on first run.
Run the tests with `python test_app.py`.

Default admin: `admin@campus.edu` / `admin`. Change it before you submit.
To try the flow, sign up two student accounts (use a private window for the second one).

## Create the GitHub repository
1. Install Git and create a free account at github.com.
2. On GitHub, click **New repository**, name it `campusswap`, leave it empty (no README or .gitignore), and click **Create repository**.
3. In the extracted `campusswap` folder, run:
```
git init
git add .
git commit -m "Add SRS and design documents"
git branch -M main
git remote add origin https://github.com/<your-username>/campusswap.git
git push -u origin main
```
4. For a better commit history, follow the commit plan in `SUBMISSION.md` instead of one big commit.
5. If Git asks for a password, use a personal access token (GitHub > Settings > Developer settings).

## Documents
- `docs/SRS.md`: requirements, use case, ER and status diagrams, test plan (GitHub draws the diagrams)
- `SUBMISSION.md`: commit plan, checklist, screenshots, report and slide outlines, demo script

## API endpoints
| Method | Path | Purpose |
|---|---|---|
| POST | /api/register, /api/login, /api/logout | Auth (session cookie) |
| GET | /api/items?q=&category=&type= | Search and filter |
| GET/PUT/DELETE | /api/items/<id> | Read, edit (owner), delete (owner/admin) |
| POST | /api/items | Create listing |
| POST | /api/items/<id>/request | Request to buy or borrow |
| PATCH | /api/transactions/<id> | Owner sets Approved, Declined, Returned |
| GET | /api/dashboard | My listings, incoming and outgoing requests |

Status flow: Pending -> Approved or Declined -> Returned (borrow only).
Data model: users, items, transactions (see app.py SCHEMA).

## Project structure
```
app.py          Flask API and database schema
static/index.html   Browser front end (served at /)
test_app.py     Automated tests
requirements.txt
SUBMISSION.md   Checklist for hand-in
docs/SRS.md     Requirements and design
```

## Known limitations
No online payments, no email verification (only a .edu format check), no chat or ratings, and the dev server is not for production use.
