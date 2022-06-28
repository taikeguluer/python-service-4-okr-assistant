from flask import Blueprint

app_feishu_event = Blueprint('feishu_event', __name__)

from . import url