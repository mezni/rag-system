import numpy as np
from sentence_transformers import SentenceTransformer

from src.ingestion.pipeline import Settings
from src.ingestion.pipeline import ChunkRecord # Assuming ChunkRecord is defined in pipeline.py

def embed_chunks(chunks: list[ChunkRecord], settings: Settings) -> None:
    model = SentenceTransformer(settings.embedding_model)
    batch_size = settings.embedding_batch_size

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start: batch_start + batch_size]
        inputs = [c.content for c in batch]
        embeddings = model.encode(inputs, convert_to_numpy=True)
        for chunk, emb in zip(batch, embeddings):
            chunk.embedding = emb.tolist()
