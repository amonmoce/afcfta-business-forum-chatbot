import os
from flask import Blueprint, jsonify, request, render_template
from supabase import create_client, Client
import json
from helpers import *

token = os.getenv("WHATSAPP_TOKEN")
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
        list = supabase.table("chatpawa-users-history").select("user_phone_number, created_at, confirmation, phone_number_id").eq("mode", "logtoray").execute()
        print(list)
        url = os.environ.get("URL_TO_CLICK")
        return render_template("list.html", waiting_list=list.data, url=url)
        # return json.dumps(list.data), 200
    


@web_bp.route("/confirm", methods=("GET", "POST"))
def confirm():
    if request.method == "POST":
        number = request.get_json()['user_phone_number']
        phone_number_id = request.get_json()['phone_number_id']
        confirmation = supabase.table("chatpawa-users-history").update({"confirmation": "oui"}).match({'user_phone_number': number, 'mode': "logtoray"}).execute()
        send_template_message(phone_number_id, token, number, "confirmation_rendez_vous")
        return "ok", 200