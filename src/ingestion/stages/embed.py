from src.core.models.chunk import Chunk as ChunkModel
from src.ingestion.config import Settings


def embed_chunks(chunks: list[ChunkModel], settings: Settings) -> None:
    # Lazy import: sentence-transformers pulls in torch (~80s first load). Only
    # installed/loaded when an embedding batch is actually produced, so test
    # collection and dry pipeline runs stay fast.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(settings.embedding_model)
    batch_size = settings.embedding_batch_size

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start: batch_start + batch_size]
        inputs = [c.content for c in batch]
        embeddings = model.encode(inputs, convert_to_numpy=True)
        for chunk, emb in zip(batch, embeddings):
            chunk.embedding = emb.tolist()
