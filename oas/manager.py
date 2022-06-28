import logging
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger()
db = SQLAlchemy()
from oas import make_celery, create_app
celery = make_celery(__name__, "dev")
app = create_app("dev", celery=celery, db=db, logger=logger)
