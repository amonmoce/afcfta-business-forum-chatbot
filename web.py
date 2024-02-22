import os
from flask import Blueprint, jsonify, request
from supabase import create_client, Client
import json

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
        if body :
            mode_id = body["mode_id"]
            mode_system_message = body["mode_system_message"]
            status = body["status"]
            description = body["description"]
        else:
            mode_id = request.form.get('mode_id')
            mode_system_message = request.form.get('mode_system_message')
            status = request.form.get('status')
            description = request.form.get('description')

        print(json.dumps(body, indent=2))
        set_mode = supabase.table("modes-settings").insert({
            "mode_id": mode_id, 
            "mode_system_message": mode_system_message, 
            "status": status,
            "description": description
        }).execute()
    return "ok", 200



@web_bp.route("/list", methods=("GET", "POST"))
def list():
    if request.method == "GET":
        list = supabase.table("chatpawa-users-history").select("user_phone_number").eq("mode", "logtoray").execute()
        print(list)
        return json.dumps(list.data), 200