import os
import pandas as pd
import json
import requests
from openai_helpers import *
import pinecone

from supabase import create_client, Client

from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Pinecone setup
PINECONE_KEY = os.getenv("PINECONE_KEY")
pinecone.init(PINECONE_KEY, environment='us-west1-gcp')
pinecone_index_name = 'afcfta-business-forum-chatbot'
pinecone_index = pinecone.Index(pinecone_index_name)

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        question = request.get_json()["question"]
        q_embeddings = get_embedding(question, engine=embedding_model)
        # Get preprocessed embeddings
        # qa = pd.read_csv('./processed_knowledge_base.csv')
        # Get the distances from the embeddings
        # qa['distances'] = qa.embedding.apply(lambda x: cosine_similarity(x, q_embeddings))
        # relevant_text = qa.sort_values('distances', ascending=True)['text'][0]+" "+qa.sort_values('distances', ascending=True)['text'][1]
        # relevant_text = ""
        res = pinecone_index.query(q_embeddings, top_k=10, include_metadata=True)
        relevant_text = [m['metadata']['text']+" " for m in res['matches']]

        openai_response = openai.Completion.create(
            prompt=generate_prompt(relevant_text, question),
            temperature=0,
            max_tokens=128,
            # top_p=1,
            # frequency_penalty=0,
            # presence_penalty=0,
            stop=["###", "\n\n"],
            model=gpt_model
        )
        if openai_response.choices[0].text.strip() not in ["Please contact the AfCFTA for this particular question.", "Please contact the AfCFTA for this particular question"]:
            return jsonify({
                'bot': openai_response.choices[0].text.strip()
            })
        else:
            alternative_openai_response = openai.Completion.create(
                prompt=generate_alternative_prompt(question),
                temperature=0,
                max_tokens=128,
                # top_p=1,
                # frequency_penalty=0,
                # presence_penalty=0,
                stop=["###", "\n\n"],
                model=gpt_model
            )
            return jsonify({
                'bot': alternative_openai_response.choices[0].text.strip()
            })
    result = request.args.get("result")
    return render_template("index.html", result=result)


@app.route("/webhook", methods=("GET", "POST"))
def webhook():
    # WhatsApp setup
    verify_token = os.getenv("VERIFY_TOKEN")
    token = os.getenv("WHATSAPP_TOKEN")

    if request.method == "POST":
        # Parse the request body from the POST
        body = request.get_json()

        # Check the Incoming webhook message
        print(json.dumps(body, indent=2))
        
        # info on WhatsApp text message payload: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#text-messages
        if body:
            entry = body['entry'][0]
            if (changes := entry.get('changes')) and (change := changes[0]) and (value := change.get('value')) and (messages := value.get('messages')) and messages[0]:
                phone_number_id = value['metadata']['phone_number_id']
                from_number = messages[0]['from']  # extract the phone number from the webhook payload
                msg_body = ""
                
                if messages[0]['type'] == "audio":
                    pass
                if messages[0]['type'] == "document":
                    pass
                if messages[0]['type'] == "image":
                    pass
                if messages[0]['type'] == "sticker":
                    pass
                if messages[0]['type'] == "system":
                    pass
                if messages[0]['type'] == "video":
                    pass
                if messages[0]['type'] == "interactive":
                    pass
                if messages[0]['type'] == "order":
                    pass
                if messages[0]['type'] == "unknown":
                    pass
                if messages[0]['type'] == "text":
                    msg_body = messages[0]['text']['body'] # extract the message text from the webhook payload
                    # Get info from database about the chatbot mode
                    chatpawa_users = supabase.table("chatpawa-users").select("*").eq("phone_number", from_number).execute()
                    phone_number_mode = chatpawa_users.data[0]['phone_number_mode']
                    # phone_number_lang = chatpawa_users.data[0]['phone_number_lang']
                    # if phone_number_lang != "":
                    #     phone_number_lang = "fr"
                    if phone_number_mode == "":
                        phone_number_mode = "bnvaa"
                    print(msg_body)
                    # if message is not a command, is conversation
                    if not msg_body.startswith("@"):
                        
                        ## BNVAA
                        if phone_number_mode == "bnvaa":
                            modes_setting = supabase.table("modes-settings").select("*").eq("mode_id", phone_number_mode).execute()
                            system_message = modes_setting.data[0]['mode_system_message']
                            message_array = [
                                {
                                    "role": "system",
                                    "content": system_message
                                },
                                {
                                    "role": "user",
                                    "content": f"Reponds au message suivant du citoyen; message: \"{msg_body}\"."
                                }
                            ]
                            response = chatgpt_completion(message_array)
                            respond_webhook(phone_number_id, token, from_number, response)
                            # saving messages
                            data = supabase.table("chatpawa-messages").insert({"phone_number_mode":phone_number_mode, "phone_number_id": phone_number_id, "phone_number": from_number, "user_message": msg_body, "assistant_message": response}).execute()

                        ## Business Forums
                        if phone_number_mode == "business_forum_assistant":
                            # Classify into question, greeting or other
                            tone_completion = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                            messages= [{
                                                "role": "user",
                                                "content": f"Classify the following prompt into question, greeting or other: \"{msg_body}\"."
                                }]
                            )
                            tone = tone_completion.choices[0].message.content.strip().lower()
                            
                            if tone == "question.":
                                # search similarities in knowledge base
                                q_embeddings = get_embedding(msg_body, engine=embedding_model)
                                res = pinecone_index.query(q_embeddings, top_k=10, include_metadata=True)
                                relevant_text = [m['metadata']['text']+" " for m in res['matches']]

                                openai_response = openai.Completion.create(
                                    prompt=generate_prompt(relevant_text, msg_body),
                                    temperature=0,
                                    max_tokens=128,
                                    # top_p=1,
                                    # frequency_penalty=0,
                                    # presence_penalty=0,
                                    stop=["###", "\n\n"],
                                    model=gpt_model
                                )
                                # there is an answer in knowledge base
                                if openai_response.choices[0].text.strip() not in ["Please contact the AfCFTA for this particular question.", "Please contact the AfCFTA for this particular question"]:
                                    response = requests.post(
                                        url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                        json={
                                            "messaging_product": "whatsapp",
                                            "to": from_number,
                                            "text": {"body": openai_response.choices[0].text.strip() },
                                        },
                                        headers={"Content-Type": "application/json"},
                                    )
                                # there is NO answer in the knowledge base
                                else:
                                    contact = openai.ChatCompletion.create(
                                            model="gpt-3.5-turbo",
                                                        messages= [{
                                                            "role": "user",
                                                            "content": f"Say \"You are an information service agent on the AfCFTA Business Forum. Respond to the user's following question: {msg_body}"
                                            }]
                                        )
                                    response = requests.post(
                                            url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                            json={
                                                "messaging_product": "whatsapp",
                                                "to": from_number,
                                                "text": {"body": contact.choices[0].message.content.strip() },
                                            },
                                            headers={"Content-Type": "application/json"},
                                        )
                            elif tone == "greeting.":
                                # greet
                                # answer neutral intent
                                greet = openai.ChatCompletion.create(
                                            model="gpt-3.5-turbo",
                                                        messages= [{
                                                            "role": "user",
                                                            "content": f"You are an information service agent. Respond to the user's following greeting: {msg_body}"
                                            }]
                                )
                                response = requests.post(
                                        url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                        json={
                                            "messaging_product": "whatsapp",
                                            "to": from_number,
                                            "text": {"body": greet.choices[0].message.content.strip() },
                                        },
                                        headers={"Content-Type": "application/json"},
                                )
                            else:
                                # answer neutral intent
                                okay = openai.ChatCompletion.create(
                                    model="gpt-3.5-turbo",
                                                messages= [{
                                                    "role": "user",
                                                    "content": f"Say \"ok\" in another way"
                                    }]
                                )
                                response = requests.post(
                                        url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                        json={
                                            "messaging_product": "whatsapp",
                                            "to": from_number,
                                            "text": {"body": okay.choices[0].message.content.strip() },
                                        },
                                        headers={"Content-Type": "application/json"},
                                )
                            ###
                            
                            # else:
                            #     alternative_openai_response = openai.Completion.create(
                            #         prompt=generate_alternative_prompt(msg_body),
                            #         temperature=0,
                            #         max_tokens=128,
                            #         # top_p=1,
                            #         # frequency_penalty=0,
                            #         # presence_penalty=0,
                            #         stop=["###", "\n\n"],
                            #         model=gpt_model
                            #     )

                            #     response = requests.post(
                            #         url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                            #         json={
                            #             "messaging_product": "whatsapp",
                            #             "to": from_number,
                            #             "text": {"body": alternative_openai_response.choices[0].text.strip() },
                            #         },
                            #         headers={"Content-Type": "application/json"},
                            #     )
                            ###
                            # response = requests.post(
                            #     url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                            #     json={
                            #         "messaging_product": "whatsapp",
                            #         "to": from_number,
                            #         "text": {"body": "Ack: " + msg_body},
                            #     },
                            #     headers={"Content-Type": "application/json"},
                            # )
                    # if message is command
                    else:
                        if msg_body.startswith("@help"):
                            response = requests.post(
                                url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                json={
                                    "messaging_product": "whatsapp",
                                    "to": from_number,
                                    "text": {"body": "The chatbot's default mode is set as an information service for the AfCFTA Business Forum. Send @register to be informed of additional features and/or offers." },
                                },
                                headers={"Content-Type": "application/json"},
                            )
                        if msg_body.startswith("@register"):
                            if phone_number_mode != "":
                                response_body = "You are already registered."
                                respond_webhook(phone_number_id, token, from_number, response_body)

                                # response = requests.post(
                                #     url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                #     json={
                                #         "messaging_product": "whatsapp",
                                #         "to": from_number,
                                #         "text": {"body": "You are already registered." },
                                #     },
                                #     headers={"Content-Type": "application/json"},
                                # )
                            else:
                                data = supabase.table("chatpawa-users").insert({"phone_number":from_number, "phone_number_mode": "business_forum_assistant"}).execute()
                                response_body = "Great! You are registered and we will keep you updated."
                                respond_webhook(phone_number_id, token, from_number, response_body)

                                # response = requests.post(
                                #     url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                #     json={
                                #         "messaging_product": "whatsapp",
                                #         "to": from_number,
                                #         "text": {"body": "Great! You are registered and we will keep you updated." },
                                #     },
                                #     headers={"Content-Type": "application/json"},
                                # ) 
                        if msg_body.startswith("@mode"):
                            if phone_number_mode != "":
                                response_body = "You are in "+phone_number_mode+" mode"
                                respond_webhook(phone_number_id, token, from_number, response_body)

                                # response = requests.post(
                                #     url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                #     json={
                                #         "messaging_product": "whatsapp",
                                #         "to": from_number,
                                #         "text": {"body": "You are in "+phone_number_mode+" mode" },
                                #     },
                                #     headers={"Content-Type": "application/json"},
                                # )
                            else:
                                data = supabase.table("chatpawa-users").insert({"phone_number":from_number, "phone_number_mode": "business_forum_assistant"}).execute()
                                response_body = "Your bot is now on default mode -- Check bot description to know modes"
                                respond_webhook(phone_number_id, token, from_number, response_body)

                                # response = requests.post(
                                #     url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                #     json={
                                #         "messaging_product": "whatsapp",
                                #         "to": from_number,
                                #         "text": {"body": "Your bot is now on default mode -- Check bot description to know modes" },
                                #     },
                                #     headers={"Content-Type": "application/json"},
                                # )
                    
                if messages[0]['type'] == "button":
                    msg_body = messages[0]['button']['text'] # extract the message text from the webhook payload
                # print(phone_number_id, from_number, msg_body, token)

        return "OK", 200
    if request.method == "GET":
        # Update verify token
        # This will be the Verify Token value when you set up webhook
        verify_token = os.environ.get("VERIFY_TOKEN")
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # Check if a token and mode were sent
        if mode and token:
            # Check the mode and token sent are correct
            if mode == "subscribe" and token == verify_token:
                # Respond with 200 OK and challenge token from the request
                print("WEBHOOK_VERIFIED")
                return challenge, 200
            else:
                # Responds with '403 Forbidden' if verify tokens do not match
                return "Forbidden", 403
