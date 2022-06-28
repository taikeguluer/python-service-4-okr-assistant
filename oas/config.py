import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Config(object):

    LARK_HOST = os.getenv("LARK_HOST")
    APP_ID = os.getenv("APP_ID")
    APP_SECRET = os.getenv("APP_SECRET")

    VERIFICATION_TOKEN = os.getenv("VERIFICATION_TOKEN")
    ENCRYPT_KEY = os.getenv("ENCRYPT_KEY")

    TENCENT_CLOUD_AI_HOST = os.getenv("TENCENT_CLOUD_AI_HOST")
    TENCENT_CLOUD_AI_BOTID = os.getenv("TENCENT_CLOUD_AI_BOTID")
    TENCENT_CLOUD_API_SECRETID = os.getenv("TENCENT_CLOUD_API_SECRETID")
    TENCENT_CLOUD_API_SECRETKEY = os.getenv("TENCENT_CLOUD_API_SECRETKEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_COMMIT_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    LOG_LEVEL = os.getenv("LOG_LEVEL")

    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")


class DevelopmentConfig(Config):

    DEBUG = True


class ProductConfig(Config):
    pass


config_map = {
    'dev': DevelopmentConfig,
    'prod': ProductConfig
}
