import threading
import time

import pytest
from werkzeug.serving import make_server

from appname import create_app
from appname.models import db
from appname.models.user import User


@pytest.fixture(scope="session")
def live_server():
    app = create_app("appname.settings.TestConfig")

    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="user@example.com").first():
            user = User("user@example.com", "safepassword")
            db.session.add(user)
            db.session.commit()

    server = make_server("127.0.0.1", 5001, app)

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    time.sleep(1)

    yield "http://127.0.0.1:5001"

    server.shutdown()
    thread.join()

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_login_page(page, live_server):
    page.goto(f"{live_server}/login")

    assert page.get_by_text("Login to your account").is_visible()


def test_user_can_login(page, live_server):
    page.goto(f"{live_server}/login")

    page.locator("input[name='email']").fill("user@example.com")
    page.locator("input[name='password']").fill("safepassword")

    page.get_by_role("button", name="Login").click()

    assert "/dashboard" in page.url