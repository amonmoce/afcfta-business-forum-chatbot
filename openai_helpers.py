
import os
import requests
import openai
from openai.embeddings_utils import get_embedding, distances_from_embeddings, cosine_similarity


# Openai setup
openai.api_key = os.getenv("OPENAI_API_KEY")
embedding_model = "text-embedding-ada-002"
gpt_model = "text-davinci-003"
chatgpt_model = "gpt-3.5-turbo"


def generate_prompt(relevant_text, question):
    return f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"Please contact the AfCFTA for this particular question\"\n\nContext: {relevant_text}\n\n---\n\nQuestion: {question}\nAnswer:"

def generate_alternative_prompt(question):
    return f"Imagine a conversation between a customer service agent in charge of answering questions on the AfCFTA Business Forum, and a person interested in the forum\"\n\Interested: {question}\n\n---\n\nAgent:"

def chatgpt_completion(message_array):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages= message_array
    )
    return completion.choices[0].message.content

def respond_webhook(id, tk, destination_number, response):

    response = requests.post(
        url="https://graph.facebook.com/v12.0/" + id + "/messages?access_token=" + tk,
        json={
            "messaging_product": "whatsapp",
            "to": destination_number,
            "text": {"body": response },
        },
        headers={"Content-Type": "application/json"},
    )