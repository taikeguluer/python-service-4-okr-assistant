from flask_restful import Api
from . import app_service
from .view import ActivationView, DbInitiationView, ConfigurationView, ToolView

# 将 user 模块蓝图加入Api进行管理
api = Api(app_service)

# 进行路由分发，类似于Django中的url工作内容（视图处理类， 请求路径）
api.add_resource(ActivationView, '/activation')
api.add_resource(DbInitiationView, '/dbinitiation')
api.add_resource(ConfigurationView, '/configuration')
api.add_resource(ToolView, '/tool')
