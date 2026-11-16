import mineshield


def post_as(client, path, data):
    with client.session_transaction() as browser_session:
        token = browser_session.get("csrf_token")
    if token is None:
        client.get("/")
        with client.session_transaction() as browser_session:
            token = browser_session.get("csrf_token")
    if token is None:
        client.get("/login")
        with client.session_transaction() as browser_session:
            token = browser_session["csrf_token"]
    return client.post(path, data={**data, "csrf_token": token})


def login_as_admin(client):
    response = post_as(
        client,
        "/login",
        {"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 302


def make_client(monkeypatch, tmp_path):
    database = tmp_path / "test_server_info.db"
    monkeypatch.setattr(mineshield, "DB_PATH", database)
    mineshield.init_db(database)
    mineshield.app.config.update(TESTING=True)
    return mineshield.app.test_client()


def test_home_shows_site_navigation_and_demo_data(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert "MineShield".encode() in response.data
    assert "Архив сезонов".encode() in response.data
    assert b'class="hero-art"' not in response.data


def test_custom_logo_is_shown_only_in_header(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    static_dir = tmp_path / "static"
    logo_path = static_dir / "images" / "logo.png"
    logo_path.parent.mkdir(parents=True)
    logo_path.write_bytes(b"test image")
    monkeypatch.setattr(mineshield.app, "static_folder", str(static_dir))

    response = client.get("/")

    assert response.status_code == 200
    assert response.data.count(b"/static/images/logo.png") == 1
    assert b'class="brand-mark"' not in response.data


def test_history_page_shows_server_history(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/history")

    assert response.status_code == 200
    assert "история игроков".encode() in response.data


def test_season_page_shows_history_and_players(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/seasons/4")

    assert response.status_code == 200
    assert "события 4 сезона".encode() in response.data
    assert "Луна".encode() in response.data


def test_player_search_is_case_insensitive(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/players?q=ЛУНА")

    assert response.status_code == 200
    assert "Луна".encode() in response.data
    assert "Редстоун".encode() not in response.data


def test_player_profile_and_missing_page(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    player = mineshield.get_players("Луна")[0]

    profile = client.get(f"/players/{player['id']}")
    missing = client.get("/players/9999")

    assert profile.status_code == 200
    assert "Исследует мир".encode() in profile.data
    assert missing.status_code == 404


def test_favorites_page_shows_players_and_storage_notice(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/favorites")

    assert response.status_code == 200
    assert "Избранные".encode() in response.data
    assert "Луна".encode() in response.data
    assert b'data-favorite-player-card="1"' in response.data
    assert b'data-favorites-grid' in response.data
    assert b"favorites.js" in response.data


def test_favorites_page_includes_all_players(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    connection = mineshield.connect_db()
    connection.executemany(
        "INSERT INTO players (name, season_id) VALUES (?, ?)",
        [(f"Игрок {index}", 1) for index in range(25)],
    )
    connection.commit()
    connection.close()

    response = client.get("/favorites")

    assert len(mineshield.get_players()) == 28
    assert b'data-favorite-player-card="28"' in response.data


def test_favorite_toggle_is_available_from_search_and_profile(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    player = mineshield.get_players("Луна")[0]

    search = client.get("/players")
    profile = client.get(f"/players/{player['id']}")
    season = client.get("/seasons/4")

    assert b'data-favorite-toggle="1"' in search.data
    assert b'data-favorite-toggle="1"' in profile.data
    assert b'data-favorite-toggle="1"' in season.data


def test_reinitializing_database_preserves_existing_content(monkeypatch, tmp_path):
    make_client(monkeypatch, tmp_path)
    connection = mineshield.connect_db()
    connection.execute(
        "UPDATE server_history SET text = ? WHERE id = 1",
        ("Сохранённая история сервера",),
    )
    connection.commit()
    connection.close()

    mineshield.init_db()

    assert mineshield.get_server_history() == "Сохранённая история сервера"
    assert mineshield.get_player_count() == 3


def test_default_admin_can_login_and_password_is_hashed(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = post_as(
        client,
        "/login",
        {"username": "admin", "password": "admin123"},
    )
    connection = mineshield.connect_db()
    password = connection.execute(
        "SELECT password FROM accounts WHERE username = 'admin'"
    ).fetchone()["password"]
    connection.close()

    assert response.status_code == 302
    assert response.location == "/"
    assert password.startswith("scrypt:")
    assert "Панель".encode() in client.get("/admin").data


def test_login_rejects_bad_password_and_protected_page_requires_signin(
    monkeypatch, tmp_path
):
    client = make_client(monkeypatch, tmp_path)

    response = post_as(
        client,
        "/login",
        {"username": "admin", "password": "incorrect"},
    )

    assert response.status_code == 200
    assert "Неверный логин".encode() in response.data
    protected = client.get("/admin")
    assert protected.status_code == 302
    assert protected.location == "/login"


def test_state_changes_require_csrf_token(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)

    response = client.post("/admin/history", data={"text": "Forged update"})

    assert response.status_code == 400
    assert mineshield.get_server_history() != "Forged update"


def test_non_ascii_csrf_token_is_rejected(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)

    response = client.post(
        "/admin/history",
        data={"csrf_token": "токен", "text": "Forged update"},
    )

    assert response.status_code == 400


def test_admin_can_create_account_card_and_edit_site_content(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)

    account_response = post_as(
        client,
        "/admin/accounts",
        {"username": "player-one", "password": "player-pass-1"},
    )
    card_response = post_as(
        client,
        "/admin/players",
        {
            "name": "Участник",
            "season_id": "4",
            "status": "Активен",
            "info": "Описание",
            "linked_account": "player-one",
        },
    )
    history_response = post_as(
        client,
        "/admin/history",
        {"text": "Обновлённая летопись"},
    )

    assert account_response.status_code == 302
    assert card_response.status_code == 302
    assert history_response.status_code == 302
    assert mineshield.get_server_history() == "Обновлённая летопись"
    player = mineshield.get_linked_player("player-one")
    assert player["name"] == "Участник"


def test_player_edits_profile_publishes_announcement_and_cannot_admin(
    monkeypatch, tmp_path
):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)
    post_as(
        client,
        "/admin/accounts",
        {"username": "player-one", "password": "player-pass-1"},
    )
    post_as(
        client,
        "/admin/players",
        {
            "name": "Участник",
            "season_id": "4",
            "status": "Активен",
            "info": "До изменений",
            "linked_account": "player-one",
        },
    )
    with client.session_transaction() as browser_session:
        token = browser_session["csrf_token"]
    client.post("/logout", data={"csrf_token": token})

    login_response = post_as(
        client,
        "/login",
        {"username": "player-one", "password": "player-pass-1"},
    )
    assert login_response.status_code == 302
    assert client.get("/admin").status_code == 403
    assert "Участник".encode() in client.get("/profile").data

    profile_response = post_as(
        client,
        "/profile",
        {"info": "Новое описание игрока"},
    )
    announcement_response = post_as(
        client,
        "/profile/announcement",
        {"text": "Сегодня начался стрим!"},
    )
    home_response = client.get("/")

    assert profile_response.status_code == 302
    assert announcement_response.status_code == 302
    assert mineshield.get_linked_player("player-one")["info"] == "Новое описание игрока"
    assert "Сегодня начался стрим!".encode() in home_response.data


def test_admin_can_update_season_and_player_card(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)

    season_response = post_as(
        client,
        "/admin/seasons/4",
        {"history_text": "История четвёртого сезона"},
    )
    card_response = post_as(
        client,
        "/admin/players/1/update",
        {
            "name": "Новая Луна",
            "season_id": "4",
            "status": "Строитель",
            "info": "Новое описание",
        },
    )

    assert season_response.status_code == 302
    assert card_response.status_code == 302
    assert mineshield.get_seasons()[3]["history_text"] == "История четвёртого сезона"
    assert mineshield.get_players("Новая Луна")[0]["status"] == "Строитель"


def test_account_can_change_password(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)
    response = post_as(
        client,
        "/account/password",
        {
            "current_password": "admin123",
            "new_password": "new-admin-pass",
            "confirmation": "new-admin-pass",
        },
    )

    assert response.status_code == 302

    with client.session_transaction() as browser_session:
        token = browser_session["csrf_token"]
    client.post("/logout", data={"csrf_token": token})

    assert post_as(
        client,
        "/login",
        {"username": "admin", "password": "admin123"},
    ).status_code == 200
    assert post_as(
        client,
        "/login",
        {"username": "admin", "password": "new-admin-pass"},
    ).status_code == 302


def test_legacy_plaintext_password_is_upgraded_after_successful_login(
    monkeypatch, tmp_path
):
    make_client(monkeypatch, tmp_path)
    connection = mineshield.connect_db()
    connection.execute(
        "INSERT INTO accounts (username, password, role) VALUES (?, ?, ?)",
        ("legacy-player", "old-password", "player"),
    )
    connection.commit()
    connection.close()

    assert mineshield.authenticate("legacy-player", "old-password")
    connection = mineshield.connect_db()
    stored_password = connection.execute(
        "SELECT password FROM accounts WHERE username = ?",
        ("legacy-player",),
    ).fetchone()["password"]
    connection.close()

    assert stored_password.startswith("scrypt:")
    assert stored_password != "old-password"


def test_admin_can_delete_player_card(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)

    response = post_as(client, "/admin/players/1/delete", {})

    assert response.status_code == 302
    assert mineshield.get_players("Луна") == []


def test_admin_can_reset_player_password_without_exposing_hash(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)
    post_as(
        client,
        "/admin/accounts",
        {"username": "player-one", "password": "player-pass-1"},
    )

    response = post_as(
        client,
        "/admin/accounts/player-one/password",
        {
            "new_password": "updated-pass-1",
            "confirmation": "updated-pass-1",
        },
    )

    connection = mineshield.connect_db()
    stored_password = connection.execute(
        "SELECT password FROM accounts WHERE username = ?",
        ("player-one",),
    ).fetchone()["password"]
    connection.close()

    assert response.status_code == 302
    assert stored_password.startswith("scrypt:")
    assert mineshield.authenticate("player-one", "updated-pass-1")
    assert not mineshield.authenticate("player-one", "player-pass-1")
    assert "updated-pass-1".encode() not in client.get("/admin").data


def test_admin_can_delete_player_account_and_keep_card(monkeypatch, tmp_path):
    admin_client = make_client(monkeypatch, tmp_path)
    login_as_admin(admin_client)
    post_as(
        admin_client,
        "/admin/accounts",
        {"username": "player-one", "password": "player-pass-1"},
    )
    post_as(
        admin_client,
        "/admin/players",
        {
            "name": "Участник",
            "season_id": "4",
            "status": "Активен",
            "info": "Описание",
            "linked_account": "player-one",
        },
    )

    response = post_as(
        admin_client,
        "/admin/accounts/player-one/delete",
        {},
    )

    connection = mineshield.connect_db()
    account = connection.execute(
        "SELECT 1 FROM accounts WHERE username = ?",
        ("player-one",),
    ).fetchone()
    linked_account = connection.execute(
        "SELECT linked_account FROM players WHERE name = ?",
        ("Участник",),
    ).fetchone()["linked_account"]
    connection.close()

    assert response.status_code == 302
    assert account is None
    assert linked_account is None
    assert mineshield.get_players("Участник")


def test_admin_cannot_reset_or_delete_admin_account(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    login_as_admin(client)

    reset_response = post_as(
        client,
        "/admin/accounts/admin/password",
        {
            "new_password": "new-admin-pass",
            "confirmation": "new-admin-pass",
        },
    )
    delete_response = post_as(client, "/admin/accounts/admin/delete", {})

    assert reset_response.status_code == 404
    assert delete_response.status_code == 404
    assert mineshield.authenticate("admin", "admin123")
