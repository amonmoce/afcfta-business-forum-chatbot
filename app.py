import os
import pandas as pd

import openai
from openai.embeddings_utils import get_embedding, distances_from_embeddings

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
app.debug = True

openai.api_key = os.getenv("OPENAI_API_KEY")
embedding_model = "text-embedding-ada-002"
gpt_model = "text-davinci-003"

@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        question = request.form["question"]
        q_embeddings = get_embedding(question, engine=embedding_model)
        # Get preprocessed embeddings
        qa = pd.read_csv('./processed_knowledge_base.csv')
        # Get the distances from the embeddings
        qa['distances'] = distances_from_embeddings(q_embeddings, qa['embedding'].values, distance_metric='cosine')
        relevant_text = qa.sort_values('distances', ascending=True)['text'][0]
        response = response = openai.Completion.create(
            prompt=generate_prompt(relevant_text, question),
            temperature=0,
            max_tokens=128,
            # top_p=1,
            # frequency_penalty=0,
            # presence_penalty=0,
            stop=["###", "\n\n"],
            model=gpt_model
        )
        return response.choices[0].text.strip()

    result = request.args.get("result")
    return render_template("index.html", result=result)


def generate_prompt(relevant_text, question):
    return f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"Please contact the AfCFTA for this particular question\"\n\nContext: {relevant_text}\n\n---\n\nQuestion: {question}\nAnswer:"
