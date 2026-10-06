from app.core.config import get_settings
from app.schemas.api import SourceOut
from app.services.document_service import get_collection
from app.services.embedding_service import embed_texts


def retrieve(question: str) -> tuple[str, list[SourceOut]]:
    collection = get_collection()
    if collection.count() == 0:
        return "没有可用文档资料。", []
    result = collection.query(
        query_embeddings=embed_texts([question]),
        n_results=min(get_settings().top_k, collection.count()),
        include=["documents", "metadatas"],
    )
    sources = [SourceOut(content=content, **metadata)
               for content, metadata in zip(result["documents"][0], result["metadatas"][0])]
    context = "\n\n".join(
        f"[{index}] 文件：{source.file_name}，chunk：{source.chunk_index}\n{source.content}"
        for index, source in enumerate(sources, start=1)
    )
    return context or "没有相关资料。", sources
