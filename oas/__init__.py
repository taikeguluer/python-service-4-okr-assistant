import logging
import sys

from celery.schedules import crontab

from celery import Celery
from flask import Flask
# from flask_wtf import CSRFProtect
from oas.config import config_map


# csrf = CSRFProtect()


def make_celery(app_name, config_name):
    config_class = config_map.get(config_name)

    celery_app = Celery(app_name,
                        broker=config_class.CELERY_BROKER_URL,
                        backend=config_class.CELERY_RESULT_BACKEND,
                        include=['oas.task.task']
                        )
    celery_app.conf.beat_schedule = {
        'check-every-midnight': {
            'task': 'oas.task.task.midnight_check',
            #'schedule': crontab()
            'schedule': crontab(hour=0, minute=0)
        }
    }
    return celery_app


def create_app(config_name, **kwargs):
    config_class = config_map.get(config_name)
    if kwargs.get('logger'):
        log_levels = {"CRITICAL": logging.CRITICAL, "ERROR": logging.ERROR, "WARNING": logging.WARNING,
                      "INFO": logging.INFO, "DEBUG": logging.DEBUG, "NOTSET": logging.NOTSET}
        kwargs['logger'].setLevel(log_levels[config_class.LOG_LEVEL])
        formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        file_fh = logging.FileHandler('%s/okr_assistant_service.log' % sys.path[0], mode='a')
        file_fh.setLevel(log_levels[config_class.LOG_LEVEL])
        file_fh.setFormatter(formatter)
        kwargs['logger'].addHandler(file_fh)
        console_fh = logging.StreamHandler(sys.stdout)
        console_fh.setLevel(log_levels[config_class.LOG_LEVEL])
        console_fh.setFormatter(formatter)
        kwargs['logger'].addHandler(console_fh)
        kwargs['logger'].info(kwargs['logger'].handlers)

    app = Flask(__name__)
    app.config.from_object(config_class)

    # initial celery ,celery对象名包括
    if kwargs.get('celery'):
        init_celery(kwargs['celery'], app)

    if kwargs.get('db'):
        kwargs['db'].init_app(app)

    # csrf.init_app(app)

    from oas.server.feishu_event import app_feishu_event
    from oas.server.feishu_microapp import app_service
    app.register_blueprint(app_feishu_event, url_prefix='/')
    app.register_blueprint(app_service, url_prefix='/api/v1')

    return app


def init_celery(celery, app):
    # celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
