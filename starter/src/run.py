"""Suggested pipeline entry point; TODO: implement the orchestration."""
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from . import ingestion
from . import chunking
from .embeddings import MyEmbedder
from .store import PgVectorStore
from . import evaluation


def main() -> None:
    """Implement the Day 06 pipeline."""
    import sys
    load_dotenv()
    
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data"
    results_dir = base_dir / "results"
    benchmark_dir = base_dir / "benchmark"
    results_dir.mkdir(exist_ok=True)
    
    pdf_path = data_dir / "Business Ethics.pdf"
    qa_path = benchmark_dir / "qa_benchmark.json"
    
    # 1. Load the corpus and benchmark; validate at least 30 content pages.
    print("Loading corpus and benchmark...")
    pages = ingestion.load_pdf(pdf_path, document_id="doc_1", source="Business Ethics.pdf")
    print(f"Loaded {len(pages)} pages.")
    
    with open(qa_path, 'r', encoding='utf-8') as f:
        benchmark = json.load(f)
        
    # Khởi tạo Embedder và kết nối Store
    embedder = MyEmbedder(model_name="text-embedding-3-small") 
    
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:55433/postgres")
    store = PgVectorStore(database_url=db_url, dimensions=embedder.dimensions)
    store.create_schema()
    
    # 2 & 3. Build strategies A, B, C; Embed and store vectors.
    strategies = {
        "A": {"type": "fixed", "size": 500, "overlap": 50},
        "B": {"type": "paragraph", "max_size": 500},
        "C": {"type": "paragraph", "max_size": 500} 
    }
    
    for strat_name, config in strategies.items():
        print(f"\nProcessing Strategy {strat_name}...")
        chunks = []
        for page in pages:
            if config["type"] == "fixed":
                chunks.extend(chunking.fixed_size(page, config["size"], config["overlap"]))
            else:
                chunks.extend(chunking.by_paragraph(page, config["max_size"]))
        
        print(f"Created {len(chunks)} chunks. Generating embeddings...")
        texts = [c.text for c in chunks]
        vectors = embedder.embed_documents(texts)
        
        print("Upserting vectors into PostgreSQL...")
        store.upsert(strategy=strat_name, chunks=chunks, vectors=vectors)
        
    # 4. Run the same dev/test questions and save full top-3 traces.
    print("\nRunning benchmark questions...")
    all_traces = []
    
    for strat_name in strategies.keys():
        for q in benchmark:
            q_vector = embedder.embed_query(q["question"])
            
            # Cấu hình C sử dụng metadata filter nếu câu hỏi có chứa điều kiện lọc
            filters = None
            if strat_name == "C" and "filter" in q:
                filters = q["filter"]
                
            hits = store.search(strategy=strat_name, query_vector=q_vector, top_k=3, filters=filters)
            
            eval_result = evaluation.evaluate_query(q, hits)
            eval_result["strategy"] = strat_name
            all_traces.append(eval_result)
            
    # 5. Report retrieval metrics and prepare samples for manual assessment.
    summary = evaluation.summarize(all_traces)
    
    print("\n--- Retrieval Metrics Summary ---")
    print(json.dumps(summary, indent=2))
    
    out_file = results_dir / "traces.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_traces, f, ensure_ascii=False, indent=2)
    print(f"\nSaved full top-3 traces to {out_file}. You can now use this file for manual assessment.")


if __name__ == "__main__":
    main()