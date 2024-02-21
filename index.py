import os
from flask import Blueprint, jsonify, request
from supabase import create_client, Client
import json
from helpers import *

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

index_bp = Blueprint('webhook', __name__)

# Pinecone setup
PINECONE_KEY = os.getenv("PINECONE_KEY")
pinecone.init(PINECONE_KEY, environment='us-west1-gcp')
pinecone_index_name = 'afcfta-business-forum-chatbot'
pinecone_index = pinecone.Index(pinecone_index_name)

@index_bp.route("/", methods=("GET", "POST"))
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
