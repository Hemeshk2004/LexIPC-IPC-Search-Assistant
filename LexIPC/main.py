from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from ddgs import DDGS

import os

# -------------------------------------------------------------
# Flask app setup
# -------------------------------------------------------------
app = Flask(__name__)
CORS(app)  # enable CORS for all routes (frontend can access)

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyApO-92ScwixSHKLdG79SX2IpbsaQ6ODTQ")

# -------------------------------------------------------------
# Initialize Gemini model
# -------------------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY
)

# -------------------------------------------------------------
# Load Chroma Vector Store (local knowledge base)
# -------------------------------------------------------------
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectorstore = Chroma(persist_directory="db", embedding_function=embedding_model)

# Convert to retriever (fetch top 3 chunks)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# -------------------------------------------------------------
# DuckDuckGo Web Search Fallback
# -------------------------------------------------------------
def duckduckgo_web_search(query):
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return None

        # Combine all snippets into one context block
        web_context = "\n".join([r.get("body", "") for r in results])
        return web_context
    except Exception as e:
        print("DuckDuckGo error:", e)
        return None

# -------------------------------------------------------------
# Route: /process_query
# -------------------------------------------------------------
@app.route('/process_query', methods=['POST'])
def process_query():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'No query provided'}), 400

        # --------------------------------------------------
        # 1️⃣ Retrieve relevant documents using RAG
        # --------------------------------------------------
        docs = retriever.invoke(query)

        # --------------------------------------------------
        # 2️⃣ If NO RAG results → fallback to DuckDuckGo
        # --------------------------------------------------
        if not docs:
            web_data = duckduckgo_web_search(query)

            if web_data:
                prompt = f"""
                You are a helpful assistant. Use ONLY the following web search data
                to answer the question accurately.

                Web Search Data:
                {web_data}

                Question: {query}
                """

                answer = llm.invoke(prompt).content

                return jsonify({
                    "answer": answer,
                    "sources": ["DuckDuckGo Web Search"]
                })

            return jsonify({
                'answer': 'No relevant information found in RAG or web search.',
                'sources': []
            })

        # --------------------------------------------------
        # 3️⃣ If RAG returns data → Answer from RAG
        # --------------------------------------------------
        context = "\n\n".join(doc.page_content for doc in docs)

        prompt = f"You are a helpful assistant. Use the context below to answer the question.\n\nContext:\n{context}\n\nQuestion: {query}"
        answer = llm.invoke(prompt).content

        sources = [doc.metadata.get("source", "Unknown") for doc in docs]

        return jsonify({
            "answer": answer,
            "sources": sources
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------
# Run Flask App
# -------------------------------------------------------------
if __name__ == '__main__':
    print("⚖️  LawFinder Flask API running on http://localhost:5008")
    app.run(host='0.0.0.0', port=5008, debug=True)
