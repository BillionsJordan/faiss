from flask import Blueprint

blueprint = Blueprint('internal', __name__)

# test whether the program running normally
@blueprint.route('/ping')
def ping():
    return "pong"
