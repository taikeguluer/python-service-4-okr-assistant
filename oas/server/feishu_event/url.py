from flask_restful import Api
from . import app_feishu_event
from .view import FeishuEventView

api = Api(app_feishu_event)

api.add_resource(FeishuEventView, '/')
