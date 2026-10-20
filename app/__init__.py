"""Camada web (Flask). Só apresenta dados; toda a análise fica no pacote `motor`."""

import os

from dotenv import load_dotenv
from flask import Flask

from motor import texto

from . import db, servicos


def create_app(config=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or os.urandom(32).hex(),
        DATABASE_URL=os.environ.get("DATABASE_URL", "sqlite:///instance/agrohack.db"),
        SEED_DEMO=os.environ.get("SEED_DEMO", "1") == "1",
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # arquivos de até 10 MB
    )
    if config:
        app.config.update(config)

    app.teardown_appcontext(db.fechar)
    app.jinja_env.filters.update(num=texto.num, moeda=texto.moeda, data=texto.data, dias=texto.dias)

    from .views import bp
    app.register_blueprint(bp)
    servicos.iniciar_banco(app)
    return app
