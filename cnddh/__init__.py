from flask import Flask
from database import db
from flask_login import LoginManager
import logging

from werkzeug.contrib.sessions import FilesystemSessionStore

app = Flask(__name__)
app.secret_key = '\x16\xc8?\xe2j\xce\x13\x89@<\xb52\x17XC\xc8\xa7\xa8\xba\xe1a\xcar:'

from config import PROD, DEBUG
app.config['DEBUG']=DEBUG

from config import ECHO, DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_ECHO'] = ECHO
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'

try:
    from config import AMBIENTE
except ImportError:
    AMBIENTE = 'windows'

from config import UPLOADS_DEFAULT_DEST

app.config['UPLOADS_DEFAULT_DEST'] = UPLOADS_DEFAULT_DEST
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

from flask_uploads import configure_uploads
from uploadsets import anexos_upload

configure_uploads(app, (anexos_upload,))

db.init_app(app)

try:
    from config import LOG, LOGPATH
except ImportError:
    LOGPATH = 'C:\Temp\logs'

logger = logging.getLogger()
logger.setLevel(logging.ERROR)    
    
if LOG:
    import logging.handlers
    
    fh = logging.handlers.RotatingFileHandler(LOGPATH, maxBytes=10 * 1024 * 1024)
    fh.setLevel(logging.ERROR)

    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.info(u'Starting...')

from cnddh import views, filters
