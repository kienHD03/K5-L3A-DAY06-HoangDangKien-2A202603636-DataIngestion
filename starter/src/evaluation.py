"""TODO: evaluate retrieved evidence and preserve per-query traces."""
from typing import Any


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """TODO: check source/page and enough gold evidence; keep hit@1 and hit@3 trace.

    Accept any documented alternative gold evidence. Do not infer human grounding
    or chunk coherence labels from exact string match.
    """
    gold_source = question.get("gold_source_id")
    gold_page = question.get("gold_page")
    evidence = question.get("evidence_quote", "")
    
    # Hỗ trợ trường hợp gold_page là một danh sách các trang hợp lệ
    valid_pages = gold_page if isinstance(gold_page, list) else [gold_page]

    hit_at_1 = False
    hit_at_3 = False

    for i, hit in enumerate(hits[:3]):
        meta = hit.get("metadata", {})
        hit_source = meta.get("source")
        hit_page = meta.get("page")
        hit_text = hit.get("text", "")

        is_source_match = (hit_source == gold_source)
        is_page_match = (hit_page in valid_pages)
        is_evidence_match = (evidence.lower() in hit_text.lower()) if evidence else True

        if is_source_match and is_page_match and is_evidence_match:
            if i == 0:
                hit_at_1 = True
            hit_at_3 = True

    return {
        "question_id": question.get("id"),
        "split": question.get("split"),
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hits": hits
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """TODO: aggregate Hit@1 and Evidence Hit@3 by strategy and dev/test split."""
    metrics = {}
    
    for trace in traces:
        split = trace.get("split", "unknown")
        strategy = trace.get("strategy", "unknown_strategy")
        
        if strategy not in metrics:
            metrics[strategy] = {}
        if split not in metrics[strategy]:
            metrics[strategy][split] = {"total": 0, "hit_at_1": 0, "hit_at_3": 0}
            
        metrics[strategy][split]["total"] += 1
        if trace.get("hit_at_1"):
            metrics[strategy][split]["hit_at_1"] += 1
        if trace.get("hit_at_3"):
            metrics[strategy][split]["hit_at_3"] += 1

    summary = {}
    for strategy, splits in metrics.items():
        summary[strategy] = {}
        for split, stats in splits.items():
            total = stats["total"]
            summary[strategy][split] = {
                "total": total,
                "hit@1_score": stats["hit_at_1"] / total if total > 0 else 0.0,
                "hit@3_score": stats["hit_at_3"] / total if total > 0 else 0.0
            }
            
    return summary