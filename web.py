import os
from flask import Blueprint, jsonify, request
from supabase import create_client, Client

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

web_bp = Blueprint('web', __name__)

@web_bp.route("/set_mode", methods=("GET", "POST"))
def set_mode():
    if request.method == "POST":
        # Parse the request body from the POST
        body = request.get_json()
        set_mode = supabase.table("modes-settings").insert({
            "mode_id": body["mode_id"], 
            "mode_system_message": body["mode_system_message"], 
            "status": body["status"],
            "description": body["description"]
        }).execute()
    return "ok", 200