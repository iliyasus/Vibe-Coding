from __future__ import annotations

import hmac
import os
import secrets
import sqlite3
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("MINESHIELD_DB", BASE_DIR / "server_info.db"))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("MINESHIELD_SECRET_KEY") or os.urandom(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
_initialized_databases: set[Path] = set()


@app.context_processor
def inject_template_state() -> dict[str, Any]:
    static_dir = Path(app.static_folder or BASE_DIR / "static")
    return {
        "logo_available": (static_dir / "images" / "logo.png").is_file(),
        "current_user": get_current_user(),
        "csrf_token": get_csrf_token,
    }


def get_csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def get_current_user() -> dict[str, str] | None:
    username = session.get("username")
    if not username:
        return None
    connection = connect_db()
    try:
        account = connection.execute(
            "SELECT username, role FROM accounts WHERE username = ?",
            (username,),
        ).fetchone()
    finally:
        connection.close()
    if account is None:
        session.clear()
        return None
    return dict(account)


def login_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if get_current_user() is None:
            flash("Сначала войдите в аккаунт.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(role: str) -> Callable:
    def decorate(view: Callable) -> Callable:
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if user is None or user["role"] != role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorate


def authenticate(username: str, password: str) -> bool:
    if len(password) > 256:
        return False
    connection = connect_db()
    try:
        account = connection.execute(
            "SELECT password FROM accounts WHERE username = ?",
            (username,),
        ).fetchone()
        if account is None or not isinstance(account["password"], str):
            return False
        stored_password = account["password"]
        if stored_password.startswith(("scrypt:", "pbkdf2:")):
            return check_password_hash(stored_password, password)
        if not hmac.compare_digest(stored_password, password):
            return False
        connection.execute(
            "UPDATE accounts SET password = ? WHERE username = ?",
            (generate_password_hash(password), username),
        )
        connection.commit()
        return True
    finally:
        connection.close()


def get_linked_player(username: str) -> sqlite3.Row | None:
    connection = connect_db()
    try:
        return connection.execute(
            """
            SELECT id, name, season_id, info, status
            FROM players
            WHERE linked_account = ?
            """,
            (username,),
        ).fetchone()
    finally:
        connection.close()


def valid_account_name(username: str) -> bool:
    return 3 <= len(username) <= 32 and all(
        character.isalnum() or character in "_.-" for character in username
    )


def connect_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path or DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path | str | None = None) -> None:
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect_db(path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                password TEXT,
                role TEXT
            );
            CREATE TABLE IF NOT EXISTS server_history (
                id INTEGER PRIMARY KEY,
                text TEXT
            );
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY,
                history_text TEXT
            );
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                season_id INTEGER,
                info TEXT,
                status TEXT,
                linked_account TEXT,
                image_file_id TEXT
            );
            CREATE TABLE IF NOT EXISTS favorites (
                chat_id INTEGER,
                player_id INTEGER,
                PRIMARY KEY (chat_id, player_id)
            );
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO accounts (username, password, role)
            VALUES ('admin', ?, 'admin')
            """,
            (generate_password_hash("admin123"),),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO server_history (id, text)
            VALUES (1, ?)
            """,
            (
                "MineShield — история игроков, событий и сезонов сервера. "
                "Здесь можно познакомиться с проектом и его участниками.",
            ),
        )
        for season_id in range(1, 5):
            connection.execute(
                """
                INSERT OR IGNORE INTO seasons (id, history_text)
                VALUES (?, ?)
                """,
                (
                    season_id,
                    f"В этом разделе собраны события {season_id} сезона.",
                ),
            )

        player_count = connection.execute(
            "SELECT COUNT(*) FROM players"
        ).fetchone()[0]
        if player_count == 0:
            connection.executemany(
                """
                INSERT INTO players (name, season_id, info, status)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        "Луна",
                        4,
                        "Демонстрационная карточка. Исследует мир и строит уютные базы.",
                        "Активен",
                    ),
                    (
                        "Редстоун",
                        3,
                        "Демонстрационная карточка. Любит механизмы и автоматические фермы.",
                        "Участник",
                    ),
                    (
                        "Блок",
                        2,
                        "Демонстрационная карточка. Строит города и помогает новичкам.",
                        "На паузе",
                    ),
                ],
            )
        connection.commit()
    finally:
        connection.close()


def get_server_history() -> str:
    connection = connect_db()
    try:
        row = connection.execute(
            "SELECT text FROM server_history WHERE id = 1"
        ).fetchone()
        return row["text"] if row and row["text"] else "Информация пока не добавлена."
    finally:
        connection.close()


def get_seasons() -> list[sqlite3.Row]:
    connection = connect_db()
    try:
        return connection.execute(
            "SELECT id, history_text FROM seasons ORDER BY id"
        ).fetchall()
    finally:
        connection.close()


def get_player_count() -> int:
    connection = connect_db()
    try:
        return connection.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    finally:
        connection.close()


def get_admin_players() -> list[sqlite3.Row]:
    connection = connect_db()
    try:
        return connection.execute(
            """
            SELECT id, name, season_id, info, status, linked_account
            FROM players
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()
    finally:
        connection.close()


def get_player_accounts() -> list[sqlite3.Row]:
    connection = connect_db()
    try:
        return connection.execute(
            "SELECT username FROM accounts WHERE role = 'player' ORDER BY username"
        ).fetchall()
    finally:
        connection.close()


def get_announcements(limit: int = 5) -> list[sqlite3.Row]:
    connection = connect_db()
    try:
        return connection.execute(
            """
            SELECT announcements.text, announcements.created_at, players.name
            FROM announcements
            JOIN players ON players.id = announcements.player_id
            ORDER BY announcements.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()


def get_players(query: str = "", season_id: int | None = None) -> list[dict[str, Any]]:
    connection = connect_db()
    try:
        if season_id is None:
            rows = connection.execute(
                "SELECT id, name, season_id, status FROM players ORDER BY name COLLATE NOCASE"
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, name, season_id, status
                FROM players
                WHERE season_id = ?
                ORDER BY name COLLATE NOCASE
                """,
                (season_id,),
            ).fetchall()
    finally:
        connection.close()

    normalized_query = query.casefold()
    players = [dict(row) for row in rows]
    if normalized_query:
        players = [
            player
            for player in players
            if normalized_query in (player["name"] or "").casefold()
        ]
    return players


@app.get("/")
def home():
    return render_template(
        "index.html",
        player_count=get_player_count(),
        seasons=get_seasons(),
        announcements=get_announcements(),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user() is not None:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if authenticate(username, password):
            session.clear()
            session["username"] = username
            flash("Вы вошли в аккаунт.", "success")
            return redirect(url_for("home"))
        flash("Неверный логин или пароль.", "error")
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for("home"))


@app.route("/account/password", methods=["GET", "POST"])
@login_required
def change_password():
    username = get_current_user()["username"]
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirmation = request.form.get("confirmation", "")
        if not authenticate(username, current_password):
            flash("Текущий пароль указан неверно.", "error")
        elif len(new_password) < 8 or len(new_password) > 128:
            flash("Новый пароль должен содержать от 8 до 128 символов.", "error")
        elif new_password != confirmation:
            flash("Новые пароли не совпадают.", "error")
        else:
            connection = connect_db()
            try:
                connection.execute(
                    "UPDATE accounts SET password = ? WHERE username = ?",
                    (generate_password_hash(new_password), username),
                )
                connection.commit()
            finally:
                connection.close()
            flash("Пароль изменён.", "success")
            return redirect(url_for("change_password"))
    return render_template("change_password.html")


@app.route("/profile", methods=["GET", "POST"])
@role_required("player")
def profile():
    user = get_current_user()
    player = get_linked_player(user["username"])
    if request.method == "POST":
        if player is None:
            flash("К аккаунту пока не привязана карточка игрока.", "error")
        else:
            info = request.form.get("info", "").strip()
            if len(info) > 2000:
                flash("Описание не должно превышать 2000 символов.", "error")
            else:
                connection = connect_db()
                try:
                    connection.execute(
                        "UPDATE players SET info = ? WHERE id = ?",
                        (info, player["id"]),
                    )
                    connection.commit()
                finally:
                    connection.close()
                flash("Описание профиля сохранено.", "success")
                return redirect(url_for("profile"))
    return render_template("profile.html", player=player)


@app.post("/profile/announcement")
@role_required("player")
def create_announcement():
    user = get_current_user()
    player = get_linked_player(user["username"])
    text = request.form.get("text", "").strip()
    if player is None:
        flash("К аккаунту пока не привязана карточка игрока.", "error")
    elif not text or len(text) > 500:
        flash("Объявление должно содержать от 1 до 500 символов.", "error")
    else:
        connection = connect_db()
        try:
            connection.execute(
                "INSERT INTO announcements (player_id, text) VALUES (?, ?)",
                (player["id"], text),
            )
            connection.commit()
        finally:
            connection.close()
        flash("Объявление опубликовано на главной странице.", "success")
    return redirect(url_for("profile"))


@app.get("/admin")
@role_required("admin")
def admin():
    return render_template(
        "admin.html",
        history_text=get_server_history(),
        seasons=get_seasons(),
        players=get_admin_players(),
        accounts=get_player_accounts(),
    )


@app.before_request
def ensure_database_initialized() -> None:
    database_path = Path(DB_PATH).resolve()
    if database_path not in _initialized_databases:
        init_db(database_path)
        _initialized_databases.add(database_path)
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        submitted = request.form.get("csrf_token", "")
        if (
            not expected
            or not submitted
            or not submitted.isascii()
            or not hmac.compare_digest(expected, submitted)
        ):
            abort(400)


@app.post("/admin/history")
@role_required("admin")
def update_history():
    text = request.form.get("text", "").strip()
    if not text or len(text) > 10000:
        flash("История должна содержать от 1 до 10000 символов.", "error")
    else:
        connection = connect_db()
        try:
            connection.execute(
                "UPDATE server_history SET text = ? WHERE id = 1", (text,)
            )
            connection.commit()
        finally:
            connection.close()
        flash("История сервера обновлена.", "success")
    return redirect(url_for("admin"))


@app.post("/admin/seasons/<int:season_id>")
@role_required("admin")
def update_season(season_id: int):
    text = request.form.get("history_text", "").strip()
    if not text or len(text) > 5000:
        flash("История сезона должна содержать от 1 до 5000 символов.", "error")
    else:
        connection = connect_db()
        try:
            cursor = connection.execute(
                "UPDATE seasons SET history_text = ? WHERE id = ?",
                (text, season_id),
            )
            connection.commit()
        finally:
            connection.close()
        if cursor.rowcount:
            flash(f"История сезона {season_id} обновлена.", "success")
        else:
            abort(404)
    return redirect(url_for("admin"))


@app.post("/admin/accounts")
@role_required("admin")
def create_player_account():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not valid_account_name(username):
        flash("Логин: от 3 до 32 букв, цифр или символов . _ -.", "error")
    elif len(password) < 8 or len(password) > 128:
        flash("Пароль должен содержать от 8 до 128 символов.", "error")
    else:
        connection = connect_db()
        try:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO accounts (username, password, role)
                VALUES (?, ?, 'player')
                """,
                (username, generate_password_hash(password)),
            )
            connection.commit()
        finally:
            connection.close()
        if cursor.rowcount:
            flash(f"Аккаунт игрока «{username}» создан.", "success")
        else:
            flash("Аккаунт с таким логином уже существует.", "error")
    return redirect(url_for("admin"))


@app.post("/admin/accounts/<username>/password")
@role_required("admin")
def reset_player_account_password(username: str):
    new_password = request.form.get("new_password", "")
    confirmation = request.form.get("confirmation", "")
    if len(new_password) < 8 or len(new_password) > 128:
        flash("Пароль должен содержать от 8 до 128 символов.", "error")
    elif new_password != confirmation:
        flash("Пароли не совпадают.", "error")
    else:
        connection = connect_db()
        try:
            cursor = connection.execute(
                """
                UPDATE accounts SET password = ?
                WHERE username = ? AND role = 'player'
                """,
                (generate_password_hash(new_password), username),
            )
            connection.commit()
        finally:
            connection.close()
        if not cursor.rowcount:
            abort(404)
        flash(f"Пароль аккаунта «{username}» изменён.", "success")
    return redirect(url_for("admin"))


@app.post("/admin/accounts/<username>/delete")
@role_required("admin")
def delete_player_account(username: str):
    connection = connect_db()
    try:
        cursor = connection.execute(
            "DELETE FROM accounts WHERE username = ? AND role = 'player'",
            (username,),
        )
        if cursor.rowcount:
            connection.execute(
                "UPDATE players SET linked_account = NULL WHERE linked_account = ?",
                (username,),
            )
            connection.commit()
    finally:
        connection.close()
    if not cursor.rowcount:
        abort(404)
    flash(f"Аккаунт «{username}» удалён; карточка игрока сохранена.", "success")
    return redirect(url_for("admin"))


@app.post("/admin/players")
@role_required("admin")
def create_player_card():
    name = request.form.get("name", "").strip()
    status = request.form.get("status", "").strip()
    info = request.form.get("info", "").strip()
    linked_account = request.form.get("linked_account", "").strip() or None
    try:
        season_id = int(request.form.get("season_id", ""))
    except ValueError:
        season_id = 0

    connection = connect_db()
    try:
        season_exists = connection.execute(
            "SELECT 1 FROM seasons WHERE id = ?", (season_id,)
        ).fetchone()
        account_valid = True
        if linked_account:
            account_valid = connection.execute(
                """
                SELECT 1 FROM accounts
                WHERE username = ? AND role = 'player'
                """,
                (linked_account,),
            ).fetchone() is not None and connection.execute(
                "SELECT 1 FROM players WHERE linked_account = ?",
                (linked_account,),
            ).fetchone() is None

        if not name or len(name) > 80 or len(status) > 80 or len(info) > 2000:
            flash("Проверьте имя, статус и описание карточки.", "error")
        elif season_exists is None:
            flash("Выберите существующий сезон.", "error")
        elif not account_valid:
            flash("Аккаунт не найден, не является игроком или уже привязан.", "error")
        else:
            connection.execute(
                """
                INSERT INTO players (name, season_id, info, status, linked_account)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, season_id, info, status, linked_account),
            )
            connection.commit()
            flash(f"Карточка игрока «{name}» создана.", "success")
    finally:
        connection.close()
    return redirect(url_for("admin"))


@app.post("/admin/players/<int:player_id>/update")
@role_required("admin")
def update_player_card(player_id: int):
    name = request.form.get("name", "").strip()
    status = request.form.get("status", "").strip()
    info = request.form.get("info", "").strip()
    try:
        season_id = int(request.form.get("season_id", ""))
    except ValueError:
        season_id = 0

    connection = connect_db()
    try:
        season_exists = connection.execute(
            "SELECT 1 FROM seasons WHERE id = ?", (season_id,)
        ).fetchone()
        if not name or len(name) > 80 or len(status) > 80 or len(info) > 2000:
            flash("Проверьте имя, статус и описание карточки.", "error")
        elif season_exists is None:
            flash("Выберите существующий сезон.", "error")
        else:
            cursor = connection.execute(
                """
                UPDATE players
                SET name = ?, season_id = ?, status = ?, info = ?
                WHERE id = ?
                """,
                (name, season_id, status, info, player_id),
            )
            connection.commit()
            if cursor.rowcount:
                flash(f"Карточка игрока «{name}» обновлена.", "success")
            else:
                abort(404)
    finally:
        connection.close()
    return redirect(url_for("admin"))


@app.post("/admin/players/<int:player_id>/delete")
@role_required("admin")
def delete_player_card(player_id: int):
    connection = connect_db()
    try:
        connection.execute("DELETE FROM favorites WHERE player_id = ?", (player_id,))
        connection.execute("DELETE FROM announcements WHERE player_id = ?", (player_id,))
        cursor = connection.execute("DELETE FROM players WHERE id = ?", (player_id,))
        connection.commit()
    finally:
        connection.close()
    if not cursor.rowcount:
        abort(404)
    flash("Карточка игрока удалена.", "success")
    return redirect(url_for("admin"))


@app.get("/history")
def history():
    return render_template("history.html", history_text=get_server_history())


@app.get("/seasons")
def seasons():
    return render_template("seasons.html", seasons=get_seasons())


@app.get("/seasons/<int:season_id>")
def season_detail(season_id: int):
    connection = connect_db()
    try:
        season = connection.execute(
            "SELECT id, history_text FROM seasons WHERE id = ?",
            (season_id,),
        ).fetchone()
    finally:
        connection.close()
    if season is None:
        abort(404)
    return render_template(
        "season_detail.html",
        season=season,
        players=get_players(season_id=season_id),
    )


@app.get("/players")
def players():
    query = request.args.get("q", "").strip()
    return render_template(
        "players.html",
        query=query,
        players=get_players(query),
        searched=bool(query),
    )


@app.get("/favorites")
def favorites():
    return render_template("favorites.html", players=get_players())


@app.get("/players/<int:player_id>")
def player_detail(player_id: int):
    connection = connect_db()
    try:
        player = connection.execute(
            """
            SELECT id, name, season_id, info, status
            FROM players
            WHERE id = ?
            """,
            (player_id,),
        ).fetchone()
    finally:
        connection.close()
    if player is None:
        abort(404)
    return render_template("player_detail.html", player=player)


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(_error):
    return render_template("403.html"), 403


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
