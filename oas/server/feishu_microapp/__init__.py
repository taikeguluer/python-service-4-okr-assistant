from flask import Blueprint

app_service = Blueprint('service', __name__)

from . import url
