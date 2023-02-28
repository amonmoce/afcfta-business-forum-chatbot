import os
import pandas as pd

import openai
from openai.embeddings_utils import get_embedding, distances_from_embeddings, cosine_similarity
import pinecone

from flask import Flask, redirect, render_template, request, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Openai setup
openai.api_key = os.getenv("OPENAI_API_KEY")
embedding_model = "text-embedding-ada-002"
gpt_model = "text-davinci-003"

# Pinecone setup
PINECONE_KEY = os.getenv("PINECONE_KEY")
pinecone.init(PINECONE_KEY, environment='us-west1-gcp')
pinecone_index_name = 'afcfta-business-forum-chatbot'
pinecone_index = pinecone.Index(pinecone_index_name)

@app.route("/", methods=("GET", "POST"))
# @cross_origin()
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
        return openai_response.choices[0].text.strip()

    result = request.args.get("result")
    return render_template("index.html", result=result)


def generate_prompt(relevant_text, question):
    return f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"Please contact the AfCFTA for this particular question\"\n\nContext: {relevant_text}\n\n---\n\nQuestion: {question}\nAnswer:"
