import os
import sqlite3
import secrets
from datetime import datetime, timezone
from functools import wraps

import requests
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("KST_DB_PATH", os.path.join(APP_DIR, "kst.sqlite3"))
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_name TEXT NOT NULL,
                track_title TEXT NOT NULL,
                track_link TEXT NOT NULL,
                message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'New'
            )
        """
        )


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)

    return wrapper


@app.context_processor
def inject_globals():
    return {"site_name": "KST", "current_year": datetime.now().year}


@app.get("/")
def home():
    artists = [
        {"name": "eaven", "role": "Founder · Music Producer", "tag": "EDM / Trance"},
        {"name": "Artist 02", "role": "Official Artist", "tag": "Electronic"},
        {"name": "Artist 03", "role": "Music Producer", "tag": "DnB"},
    ]
    return render_template("index.html", artists=artists)


@app.get("/artists")
def artists_page():
    artists = [
        {"name": "eaven", "role": "Founder · Music Producer", "tag": "EDM / Trance"},
        {"name": "Artist 02", "role": "Official Artist", "tag": "Electronic"},
        {"name": "Artist 03", "role": "Music Producer", "tag": "DnB"},
    ]
    return render_template("artists.html", artists=artists)


@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        artist_name = request.form.get("artist_name", "").strip()
        track_title = request.form.get("track_title", "").strip()
        track_link = request.form.get("track_link", "").strip()
        message = request.form.get("message", "").strip()

        if not all([artist_name, track_title, track_link]):
            flash("필수 항목을 모두 입력해 주세요.", "error")
            return render_template("submit.html")
        if len(artist_name) > 80 or len(track_title) > 120 or len(track_link) > 500 or len(message) > 1500:
            flash("입력 내용이 너무 깁니다. 내용을 줄여 주세요.", "error")
            return render_template("submit.html")
        if not (track_link.startswith("https://") or track_link.startswith("http://")):
            flash("곡 링크는 http:// 또는 https://로 시작해야 합니다.", "error")
            return render_template("submit.html")

        created_at = datetime.now(timezone.utc).isoformat()
        with db() as conn:
            conn.execute(
                "INSERT INTO submissions (artist_name, track_title, track_link, message, created_at) VALUES (?, ?, ?, ?, ?)",
                (artist_name, track_title, track_link, message, created_at),
            )

        webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
        if webhook:
            try:
                requests.post(
                    webhook,
                    json={
                        "content": "🎵 **새 KST 음악 제출**",
                        "embeds": [
                            {
                                "title": track_title,
                                "url": track_link,
                                "fields": [
                                    {"name": "아티스트", "value": artist_name[:100], "inline": True},
                                    {"name": "메시지", "value": (message or "없음")[:1000], "inline": False},
                                ],
                            }
                        ],
                    },
                    timeout=5,
                ).raise_for_status()
            except requests.RequestException:
                app.logger.warning("Discord webhook notification failed.")

        return render_template("submitted.html")
    return render_template("submit.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "KST website"}, 200


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        expected = os.environ.get("ADMIN_PASSWORD")
        if not expected:
            flash("서버 환경 변수 ADMIN_PASSWORD를 먼저 설정해 주세요.", "error")
        elif secrets.compare_digest(request.form.get("password", ""), expected):
            session["is_admin"] = True
            return redirect(url_for("admin"))
        else:
            flash("비밀번호가 올바르지 않습니다.", "error")
    return render_template("admin_login.html")


@app.post("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))


@app.get("/admin")
@admin_required
def admin():
    with db() as conn:
        submissions = conn.execute("SELECT * FROM submissions ORDER BY id DESC").fetchall()
    return render_template("admin.html", submissions=submissions)


@app.post("/admin/<int:submission_id>/status")
@admin_required
def update_status(submission_id):
    status = request.form.get("status", "New")
    if status not in {"New", "Reviewing", "Accepted", "Declined"}:
        abort(400)
    with db() as conn:
        conn.execute("UPDATE submissions SET status = ? WHERE id = ?", (status, submission_id))
    return redirect(url_for("admin"))


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="페이지를 찾을 수 없습니다."), 404


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
