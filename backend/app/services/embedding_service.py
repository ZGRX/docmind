from openai import OpenAI, OpenAIError

from app.core.config import get_settings
from app.core.errors import AppError


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    if not settings.openai_api_key or settings.openai_api_key == "replace-me":
        raise AppError(503, "请先在 backend/.env 配置 OPENAI_API_KEY")
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    try:
        response = client.embeddings.create(model=settings.embedding_model, input=texts)
    except OpenAIError as exc:
        raise AppError(502, "Embedding API 调用失败，请检查地址、模型和密钥") from exc
    return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
