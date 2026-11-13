"""TODO: store and search vectors using PostgreSQL + pgvector."""
import json
import psycopg
from .models import Chunk
from typing import Any

class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        """TODO: create table with vector column and source/page/filter metadata."""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Ép xóa bảng 768 chiều cũ
                cur.execute("DROP TABLE IF EXISTS chunks;")
                
                # Tạo lại bảng mới với đúng kích thước
                cur.execute(f"""
                    CREATE TABLE chunks (
                        id TEXT PRIMARY KEY,
                        strategy TEXT NOT NULL,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL,
                        embedding vector({self.dimensions})
                    );
                """)
            conn.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """TODO: validate lengths/dimensions and write stable IDs without duplicates."""
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors length mismatch")

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chunks WHERE strategy = %s;", (strategy,))
                
                for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    unique_id = f"{strategy}_{chunk.chunk_id}_{i}"
                    
                    metadata_dict = {
                        "document_id": chunk.document_id,
                        "source": chunk.source,
                        "page": chunk.page
                    }
                    
                    cur.execute(
                        """
                        INSERT INTO chunks (id, strategy, text, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (unique_id, strategy, chunk.text, json.dumps(metadata_dict), str(vector))
                    )
            conn.commit()

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """TODO: filter permitted metadata in SQL, rank by cosine distance, return top-k.

        Return chunk ID, text, score and metadata. Parameterize user-supplied values.
        """
        query = "SELECT id, text, metadata, (embedding <=> %s) AS score FROM chunks WHERE strategy = %s"
        params = [str(query_vector), strategy]

        if filters:
            for k, v in filters.items():
                query += " AND metadata->>%s = %s"
                params.extend([str(k), str(v)])

        query += " ORDER BY embedding <=> %s LIMIT %s;"
        params.extend([str(query_vector), top_k])

        results = []
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                for row in cur.fetchall():
                    results.append({
                        "id": row[0],
                        "text": row[1],
                        "metadata": row[2] if isinstance(row[2], dict) else json.loads(row[2]),
                        "score": float(row[3])
                    })
        return results