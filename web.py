from flask import Blueprint, jsonify

web_bp = Blueprint('web', __name__)

@web_bp.route("/set_mode", methods=("GET", "POST"))
def set_mode():
    return "ok", 200