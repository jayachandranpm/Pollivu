from flask import Blueprint

polls_bp = Blueprint('polls', __name__)

from . import routes
