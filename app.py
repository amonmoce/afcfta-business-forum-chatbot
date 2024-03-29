import os
from dotenv import load_dotenv
import pandas as pd
import json
import requests
from helpers import *
# import pinecone
# from langchain.chat_models import ChatOpenAI
# from langchain.chains import ConversationChain
# from langchain.memory import ConversationBufferMemory
# from langchain.prompts import PromptTemplate

from supabase import create_client, Client

from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_cors import CORS
from web import web_bp
# from index import index_bp
import datetime
load_dotenv()

app = Flask(__name__)
app.register_blueprint(web_bp, url_prefix="/web")
# app.register_blueprint(index_bp, url_prefix="/webhook")

CORS(app)

# Pinecone setup
# PINECONE_KEY = os.getenv("PINECONE_KEY")
# pinecone.init(PINECONE_KEY, environment='us-west1-gcp')
# pinecone_index_name = 'afcfta-business-forum-chatbot'
# pinecone_index = pinecone.Index(pinecone_index_name)

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route("/", methods=("GET", "POST"))
def index():
    # if request.method == "POST":
    #     question = request.get_json()["question"]
    #     q_embeddings = get_embedding(question, engine=embedding_model)
    #     # Get preprocessed embeddings
    #     # qa = pd.read_csv('./processed_knowledge_base.csv')
    #     # Get the distances from the embeddings
    #     # qa['distances'] = qa.embedding.apply(lambda x: cosine_similarity(x, q_embeddings))
    #     # relevant_text = qa.sort_values('distances', ascending=True)['text'][0]+" "+qa.sort_values('distances', ascending=True)['text'][1]
    #     # relevant_text = ""
    #     res = pinecone_index.query(q_embeddings, top_k=10, include_metadata=True)
    #     relevant_text = [m['metadata']['text']+" " for m in res['matches']]

    #     openai_response = openai.Completion.create(
    #         prompt=generate_prompt(relevant_text, question),
    #         temperature=0,
    #         max_tokens=128,
    #         # top_p=1,
    #         # frequency_penalty=0,
    #         # presence_penalty=0,
    #         stop=["###", "\n\n"],
    #         model=gpt_model
    #     )
    #     if openai_response.choices[0].text.strip() not in ["Please contact the AfCFTA for this particular question.", "Please contact the AfCFTA for this particular question"]:
    #         return jsonify({
    #             'bot': openai_response.choices[0].text.strip()
    #         })
    #     else:
    #         alternative_openai_response = openai.Completion.create(
    #             prompt=generate_alternative_prompt(question),
    #             temperature=0,
    #             max_tokens=128,
    #             # top_p=1,
    #             # frequency_penalty=0,
    #             # presence_penalty=0,
    #             stop=["###", "\n\n"],
    #             model=gpt_model
    #         )
    #         return jsonify({
    #             'bot': alternative_openai_response.choices[0].text.strip()
    #         })
    # result = request.args.get("result")
    # return render_template("index.html", result=result)
    return render_template("index.html")

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
                if messages[0]['type'] == "location":
                    pass
                if messages[0]['type'] == "document":
                    pass
                if messages[0]['type'] == "image":
                #     "image": {
                #     "mime_type": "image/jpeg",
                #     "sha256": "QW+LqZdVo+mYd73LTXYaCvVZ2N+woGMClbTRAoYihbA=",
                #     "id": "816050752774702"
                #   }
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
                    # phone_number_lang = chatpawa_users.data[0]['phone_number_lang']
                    phone_number_mode = ""
                    if len(chatpawa_users.data) == 0: # for new users
                        default_phone_number_mode = supabase.table("modes-settings").select("*").eq("status", "default").execute()
                        phone_number_mode = default_phone_number_mode.data[0]['mode_id']
                        data = supabase.table("chatpawa-users").insert({"phone_number":from_number, "phone_number_mode": phone_number_mode}).execute()
                    else:
                        phone_number_mode = chatpawa_users.data[0]['phone_number_mode']
                    modes_setting = supabase.table("modes-settings").select("*").eq("mode_id", phone_number_mode).execute()
                    system_message = modes_setting.data[0]['mode_system_message']
                    
                    print(msg_body)
                    # if message is not a command, is conversation
                    if not msg_body.startswith("@"):
                        
                        ## Africallia
                        # if phone_number_mode == "africallia":
                        # message_array = [
                        #     {
                        #         "role": "system",
                        #         "content": system_message
                        #     },
                        #     {
                        #         "role": "user",
                        #         "content": f"{msg_body}"
                        #     }
                        # ]
                        history_query = supabase.table("chatpawa-users-history").select("*").match({'user_phone_number': from_number, 'mode': phone_number_mode}).execute()
                        
                        print(history_query)
                        # history is not null and history length is less than 24h (86400 seconds)
                        if history_query.data != [] and float(history_query.data[0]['history_length']) < 86400:
                            history = history_query.data[0]['history']
                            history.append({
                                    "role": "user",
                                    "content": f"{msg_body}"
                            });
                        else:
                            history = []
                            history.append({
                                    "role": "system",
                                    "content": system_message
                            });

                            history.append({
                                    "role": "user",
                                    "content": f"{msg_body}"
                            });
                           
                        response = chatgpt_completion(history)
                        if response != "error":
                            respond_webhook(phone_number_id, token, from_number, response)
                            # saving messages
                            data = supabase.table("chatpawa-messages").insert({"phone_number_mode":phone_number_mode, "phone_number": from_number, "user_message": msg_body, "assistant_message": response}).execute()
                            print(history, len(history))
                            history.append({
                                    "role": "assistant",
                                    "content": response
                            });
                            history_content_words = [e["content"].split() for e in history]
                            history_size = sum([len(content) for content in history_content_words])
                            if history_query.data != []:
                                dt = history_query.data[0]['created_at']
                                dt = datetime.datetime.strptime(dt.split()[0],"%Y-%m-%dT%H:%M:%S.%f%z")
                                history_length_td = datetime.datetime.now() - dt.replace(tzinfo=None)
                                history_length = history_length_td.total_seconds()
                                history_query = supabase.table("chatpawa-users-history").update({"history": history, "history_size": history_size, "history_length": history_length}).match({'user_phone_number': from_number, 'mode': phone_number_mode}).execute()
                            else:
                                history_length = 0
                                history_query = supabase.table("chatpawa-users-history").insert({"history": history, "history_size": history_size, "history_length": history_length, 'user_phone_number': from_number, 'mode': phone_number_mode, 'phone_number_id': phone_number_id}).execute()


                        # ## BNVAA
                        # if phone_number_mode == "bnvaa":
                        #     message_array = [
                        #         {
                        #             "role": "system",
                        #             "content": system_message
                        #         },
                        #         {
                        #             "role": "user",
                        #             "content": f"Reponds au message suivant du citoyen; message: \"{msg_body}\"."
                        #         }
                        #     ]
                            
                        #     response = chatgpt_completion(message_array)
                        #     if response != "error":
                        #         respond_webhook(phone_number_id, token, from_number, response)
                        #         # saving messages
                        #         data = supabase.table("chatpawa-messages").insert({"phone_number_mode":phone_number_mode, "phone_number": from_number, "user_message": msg_body, "assistant_message": response}).execute()

                        # ## Duran
                        # if phone_number_mode == "duran":
                        #     # llm = ChatOpenAI(temperature=1)
                        #     # memory = ConversationBufferMemory()
                        #     # prompt_template = system_message + "\n{history}\nHuman: {input}\nAI:"
                        #     # conversation = ConversationChain(
                        #     #     llm=llm, 
                        #     #     memory = memory,
                        #     #     verbose=False,
                        #     #     prompt=PromptTemplate.from_template(prompt_template)
                        #     # )
                        #     message_array = [
                        #         # {
                        #         #     "role": "user",
                        #         #     "content": system_message
                        #         # },
                        #         {
                        #             "role": "user",
                        #             "content": system_message + "\n\n"+msg_body
                        #         }

                        #     ]
                            
                        #     # if msg_body.startswith("1"):
                        #     #     response = "Sur quel sujet vous voulez excercer votre anglais (vous pouvez entrer le sujet en francais)?"
                        #     #     respond_webhook(phone_number_id, token, from_number, response)
                                
                        #     # elif msg_body.startswith("2"):
                        #     #     response = chatgpt_completion(message_array["ask_question"])
                        #     #     if response != "error":
                        #     #         respond_webhook(phone_number_id, token, from_number, response)
                        #     #         # saving messages
                        #     #         data = supabase.table("chatpawa-messages").insert({"phone_number_mode":phone_number_mode, "phone_number": from_number, "user_message": msg_body, "assistant_message": response}).execute()
                        #     # else:
                        #     response = chatgpt_completion(message_array)
                        #     # response = conversation.predict(input=msg_body)
                        #     if response != "error":
                        #         respond_webhook(phone_number_id, token, from_number, response)
                        #         # saving messages
                        #         data = supabase.table("chatpawa-messages").insert({"phone_number_mode":phone_number_mode, "phone_number": from_number, "user_message": msg_body, "assistant_message": response}).execute()
                        
                        # ## Fitness
                        # if phone_number_mode == "fitness":
                        #     message_array = [
                        #         {
                        #             "role": "system",
                        #             "content": system_message
                        #         },
                        #         {
                        #             "role": "user",
                        #             "content": msg_body
                        #         }
                        #     ]
                            
                        #     response = chatgpt_completion(message_array)
                        #     if response != "error":
                        #         respond_webhook(phone_number_id, token, from_number, response)
                        #         # saving messages
                        #         data = supabase.table("chatpawa-messages").insert({"phone_number_mode":phone_number_mode, "phone_number": from_number, "user_message": msg_body, "assistant_message": response}).execute()

                        ## Business Forums
                        # if phone_number_mode == "business_forum_assistant":
                        #     # Classify into question, greeting or other
                        #     tone_completion = openai.ChatCompletion.create(
                        #         model="gpt-3.5-turbo",
                        #                     messages= [{
                        #                         "role": "user",
                        #                         "content": f"Classify the following prompt into question, greeting or other: \"{msg_body}\"."
                        #         }]
                        #     )
                        #     tone = tone_completion.choices[0].message.content.strip().lower()
                            
                        #     if tone == "question.":
                        #         # search similarities in knowledge base
                        #         q_embeddings = get_embedding(msg_body, engine=embedding_model)
                        #         res = pinecone_index.query(q_embeddings, top_k=10, include_metadata=True)
                        #         relevant_text = [m['metadata']['text']+" " for m in res['matches']]

                        #         openai_response = openai.Completion.create(
                        #             prompt=generate_prompt(relevant_text, msg_body),
                        #             temperature=0,
                        #             max_tokens=128,
                        #             # top_p=1,
                        #             # frequency_penalty=0,
                        #             # presence_penalty=0,
                        #             stop=["###", "\n\n"],
                        #             model=gpt_model
                        #         )
                        #         # there is an answer in knowledge base
                        #         if openai_response.choices[0].text.strip() not in ["Please contact the AfCFTA for this particular question.", "Please contact the AfCFTA for this particular question"]:
                        #             response = requests.post(
                        #                 url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                        #                 json={
                        #                     "messaging_product": "whatsapp",
                        #                     "to": from_number,
                        #                     "text": {"body": openai_response.choices[0].text.strip() },
                        #                 },
                        #                 headers={"Content-Type": "application/json"},
                        #             )
                        #         # there is NO answer in the knowledge base
                        #         else:
                        #             contact = openai.ChatCompletion.create(
                        #                     model="gpt-3.5-turbo",
                        #                                 messages= [{
                        #                                     "role": "user",
                        #                                     "content": f"Say \"You are an information service agent on the AfCFTA Business Forum. Respond to the user's following question: {msg_body}"
                        #                     }]
                        #                 )
                        #             response = requests.post(
                        #                     url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                        #                     json={
                        #                         "messaging_product": "whatsapp",
                        #                         "to": from_number,
                        #                         "text": {"body": contact.choices[0].message.content.strip() },
                        #                     },
                        #                     headers={"Content-Type": "application/json"},
                        #                 )
                        #     elif tone == "greeting.":
                        #         # greet
                        #         # answer neutral intent
                        #         greet = openai.ChatCompletion.create(
                        #                     model="gpt-3.5-turbo",
                        #                                 messages= [{
                        #                                     "role": "user",
                        #                                     "content": f"You are an information service agent. Respond to the user's following greeting: {msg_body}"
                        #                     }]
                        #         )
                        #         response = requests.post(
                        #                 url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                        #                 json={
                        #                     "messaging_product": "whatsapp",
                        #                     "to": from_number,
                        #                     "text": {"body": greet.choices[0].message.content.strip() },
                        #                 },
                        #                 headers={"Content-Type": "application/json"},
                        #         )
                        #     else:
                        #         # answer neutral intent
                        #         okay = openai.ChatCompletion.create(
                        #             model="gpt-3.5-turbo",
                        #                         messages= [{
                        #                             "role": "user",
                        #                             "content": f"Say \"ok\" in another way"
                        #             }]
                        #         )
                        #         response = requests.post(
                        #                 url="https://graph.facebook.com/v12.0/" + phone_number_id + "/messages?access_token=" + token,
                        #                 json={
                        #                     "messaging_product": "whatsapp",
                        #                     "to": from_number,
                        #                     "text": {"body": okay.choices[0].message.content.strip() },
                        #                 },
                        #                 headers={"Content-Type": "application/json"},
                        #         )
                    
                    else:
                        if msg_body.startswith("@help"):
                            response_body = "Here are chatpawa's commands:\n\n\n @mode: Know your current mode or change the mode by adding the mode name like @mode africallia\n\n@list_modes: Know the available modes\n\n@privacy(soon): Know the privacy policy for the mode you are at\n\n@agree(soon): Agree to the privacy policy\n\n@disagree(soon): Disagree to the privacy policy. You won't be able to use chatpawa"
                            respond_webhook(phone_number_id, token, from_number, response_body)
                        if msg_body.startswith("@privacy"):
                            pass
                        if msg_body.startswith("@agree"):
                            pass
                        if msg_body.startswith("@disagree"):
                            pass
                        if msg_body.startswith("@list_modes"):
                            phone_number_modes = supabase.table("modes-settings").select("*").execute()
                            response_body = "List of chatpawa's mode:\n\n"
                            for i, m in enumerate(phone_number_modes.data):
                                response_body+=m['mode_id']+": "+m['description']+"\n\n"
                            respond_webhook(phone_number_id, token, from_number, response_body)

                        if msg_body.startswith("@mode"):
                            words = msg_body.split()
                            if len(words) == 1:
                                # Send the current mode
                                mode_settings = supabase.table("modes-settings").select("*").eq("mode_id", phone_number_mode).execute()
                                response_body = phone_number_mode+": "+mode_settings.data[0]['description']
                                respond_webhook(phone_number_id, token, from_number, response_body)
                            if len(words) == 2:
                                # Update current mode to the one specified
                                verify_phone_number_mode = supabase.table("modes-settings").select("*").eq("mode_id", words[1]).execute()
                                if len(verify_phone_number_mode.data) > 0:
                                    data = supabase.table("chatpawa-users").update({"phone_number_mode": words[1]}).eq("phone_number", from_number).execute()
                                    response_body = "Le mode "+ words[1]+" est activé -- \n"+verify_phone_number_mode.data[0]['description']
                                    respond_webhook(phone_number_id, token, from_number, response_body)
                                else:
                                    response_body = "This mode does not exist. Send @list_mode to know all the modes"
                                    respond_webhook(phone_number_id, token, from_number, response_body)
                if messages[0]['type'] == "button":
                    msg_body = messages[0]['button']['text'] # extract the message text from the webhook payload

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







# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=8001)