# streamlit_app.py
import streamlit as st
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# -----------------------------
# Initialize model and FAISS index
# -----------------------------
model = SentenceTransformer('all-MiniLM-L6-v2')

# Global storage for documents and embeddings
documents = []
embeddings = None
index = None

def build_index():
    global embeddings, index
    if not documents:
        return
    texts = [doc["text"] for doc in documents]
    embeddings = model.encode(texts)
    embeddings = np.array(embeddings).astype("float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

def add_document(title, text):
    doc_id = len(documents) + 1
    documents.append({"id": doc_id, "title": title, "text": text})
    build_index()

def search(query, k=3):
    if index is None or not documents:
        return []
    query_embedding = model.encode([query]).astype("float32")
    distances, indices = index.search(query_embedding, k)
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(documents):
            doc = documents[idx]
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"],
                "score": float(distances[0][i])
            })
    return results

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🔎 Simple Vector Store with Metadata")

# Section: Add new document
st.header("📄 Add a new document")
title = st.text_input("Title")
text = st.text_area("Text")
if st.button("Add Document"):
    if title and text:
        add_document(title, text)
        st.success(f"Added document: {title}")
    else:
        st.warning("Please provide both title and text.")

# Section: Query
st.header("❓ Query the store")
query = st.text_input("Enter your query:")
if query:
    results = search(query, k=3)
    if results:
        st.subheader("Results")
        for r in results:
            st.write(f"**{r['title']}** (score: {r['score']:.4f})")
            st.write(r['text'])
            st.write("---")
    else:
        st.info("No results found. Try adding documents first.")
