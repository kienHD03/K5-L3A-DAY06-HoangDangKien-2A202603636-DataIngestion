"""Choose a real embedding provider (API or local) and implement this contract."""
from typing import Protocol
from openai import OpenAI


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, question: str) -> list[float]:
        ...


class MyEmbedder:
    def __init__(self, model_name: str = "text-embedding-3-small") -> None:
        self.model_name = model_name
        self.dimensions = 1536
        
        self.client = OpenAI()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model_name
        )
        return [data.embedding for data in response.data]

    def embed_query(self, question: str) -> list[float]:
        response = self.client.embeddings.create(
            input=question,
            model=self.model_name
        )
        return response.data[0].embedding