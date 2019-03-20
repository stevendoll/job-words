from flask_bootstrap import Bootstrap
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

import logging
from logging.handlers import RotatingFileHandler
import os

from config import Config


app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config.from_object(Config)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = "login"


# if app.config['LOG_TO_STDOUT']:
#     stream_handler = logging.StreamHandler()
#     stream_handler.setLevel(logging.INFO)
#     app.logger.addHandler(stream_handler)
# else:
#     if not os.path.exists('logs'):
#         os.mkdir('logs')
#     file_handler = RotatingFileHandler('logs/jobwords.log',
#                                        maxBytes=10240, backupCount=10)
#     file_handler.setFormatter(logging.Formatter(
#         '%(asctime)s %(levelname)s: %(message)s '
#         '[in %(pathname)s:%(lineno)d]'))
#     file_handler.setLevel(logging.INFO)
#     app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info("App startup")
# app.logger.info(app.config['SQLALCHEMY_DATABASE_URI'])


from app import routes, models

if __name__ == "__main__":
    app.run()
