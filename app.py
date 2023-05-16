import os
import pandas as pd
import json
import requests

import openai
from openai.embeddings_utils import get_embedding, distances_from_embeddings, cosine_similarity
import pinecone

from supabase import create_client, Client

from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Openai setup
openai.api_key = os.getenv("OPENAI_API_KEY")
embedding_model = "text-embedding-ada-002"
gpt_model = "text-davinci-003"
chatgpt_model = "gpt-3.5-turbo"

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

                if messages[0]['type'] == "text":
                    msg_body = messages[0]['text']['body'] # extract the message text from the webhook payload
                    print(msg_body)
                    # Check if text is command
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
                        # Get info from database about the chatbot mode
                        phone_number_mode = supabase.table("chatpawa-modes").select("*").eq("phone_number_id", phone_number_id).execute()

                        if len(phone_number_mode.data) > 0:
                            response = requests.post(
                                url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                json={
                                    "messaging_product": "whatsapp",
                                    "to": from_number,
                                    "text": {"body": "You are already registered." },
                                },
                                headers={"Content-Type": "application/json"},
                            )
                        else:
                            data = supabase.table("chatpawa-modes").insert({"phone_number_id":phone_number_id, "phone_number_mode": "business_forum_assistant"}).execute()
                            response = requests.post(
                                url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                json={
                                    "messaging_product": "whatsapp",
                                    "to": from_number,
                                    "text": {"body": "Great! You are registered and we will keep you updated." },
                                },
                                headers={"Content-Type": "application/json"},
                            ) 
                    if msg_body.startswith("@mode"):
                        # Get info from database about the chatbot mode
                        phone_number_mode = supabase.table("chatpawa-modes").select("*").eq("phone_number_id", phone_number_id).execute()

                        if len(phone_number_mode.data) > 0:
                            print (phone_number_mode.data)
                            response = requests.post(
                                url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                json={
                                    "messaging_product": "whatsapp",
                                    "to": from_number,
                                    "text": {"body": "You are in "+phone_number_mode.data[0]['phone_number_mode']+" mode" },
                                },
                                headers={"Content-Type": "application/json"},
                            )
                        else:
                            data = supabase.table("chatpawa-modes").insert({"phone_number_id":phone_number_id, "phone_number_mode": "business_forum_assistant"}).execute()
                            response = requests.post(
                                url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                                json={
                                    "messaging_product": "whatsapp",
                                    "to": from_number,
                                    "text": {"body": "Your bot is now on default mode -- Check bot description to know modes" },
                                },
                                headers={"Content-Type": "application/json"},
                            )
                
                if messages[0]['type'] == "button":
                    msg_body = messages[0]['button']['text'] # extract the message text from the webhook payload
                # print(phone_number_id, from_number, msg_body, token)
                # if message is not a command
                if ~msg_body.startswith("@"):
                    # Classify into question, greeting or other
                    tone_completion = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                                    messages= [{
                                        "role": "user",
                                        "content": f"Classify the following prompt into question, greeting or other: \"{msg_body}\"."
                        }]
                    )
                    tone = tone_completion.choices[0].message.content.strip().lower()
                    print("The tone is: "+tone)
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

def generate_prompt(relevant_text, question):
    return f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"Please contact the AfCFTA for this particular question\"\n\nContext: {relevant_text}\n\n---\n\nQuestion: {question}\nAnswer:"

def generate_alternative_prompt(question):
    return f"Imagine a conversation between a customer service agent in charge of answering questions on the AfCFTA Business Forum, and a person interested in the forum\"\n\Interested: {question}\n\n---\n\nAgent:"
