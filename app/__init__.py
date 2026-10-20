"""Camada web (Flask). Só apresenta dados; toda a análise fica no pacote `motor`."""

import os

from flask import Flask, render_template


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-apenas-local")
    if config:
        app.config.update(config)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
