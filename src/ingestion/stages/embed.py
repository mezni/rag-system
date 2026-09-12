import numpy as np
from sentence_transformers import SentenceTransformer


def embed_chunks(chunks: list, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
    model = SentenceTransformer(model_name)
    batch_size = 64

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start: batch_start + batch_size]
        inputs = [c.content for c in batch]
        embeddings = model.encode(inputs, convert_to_numpy=True)
        for chunk, emb in zip(batch, embeddings):
            chunk.embedding = emb.tolist()
