"""Benchmark 5 câu hỏi của nhóm trên corpus data/ai-liem-chinh-hoc-thuat.

Chạy:
    python bench.py                      # chiến lược của tôi (STRATEGY bên dưới)
    python bench.py --strategy all       # cả 3 chiến lược của nhóm + A/B filter, ghi ket_qua_benchmark.txt

Mỗi thành viên chỉ đổi dòng STRATEGY; mọi thứ khác (corpus, embedder, query, cách chấm) giữ nguyên.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from src import (
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    RecursiveChunker,
    _mock_embed,
)

STRATEGY = "heading"  # <- dòng duy nhất mỗi thành viên đổi: "fixed" | "recursive" | "heading"

ROOT = Path(__file__).parent
CORPUS_DIR = ROOT / "data" / "ai-liem-chinh-hoc-thuat"
CACHE_PATH = ROOT / ".cache" / "embeddings.json"
OUTPUT_PATH = ROOT / "ket_qua_benchmark.txt"
TOP_K = 3

# ---------------------------------------------------------------------------
# 5 benchmark query của nhóm. `evidence` là chuỗi đặc trưng phải xuất hiện trong
# ngữ cảnh truy xuất được thì mới coi là "ngữ cảnh trả lời được" (chấm mức nội dung).
# ---------------------------------------------------------------------------
QUERIES = [
    {
        "id": "Q1",
        "query": "Theo quy định của UEH, tỷ lệ tương đồng từ bao nhiêu phần trăm thì sản phẩm học thuật bị xem là có dấu hiệu đạo văn?",
        "gold_doc": "ueh-dao-van-ai-quy-dinh-chung",
        "evidence": ["20% trở lên"],
        "gold_answer": "Từ 20% trở lên (không tính trích dẫn, tài liệu tham khảo, mô tả phương pháp phổ biến, thuật ngữ, văn bản pháp luật, tên riêng); tỷ lệ này không phải căn cứ duy nhất.",
        "filter": None,
    },
    {
        "id": "Q2",
        # Không nêu người hỏi là ai; corpus có 2 file UEH cùng từ vựng nhưng khác audience và khác đáp án.
        "query": "Sản phẩm học thuật đã chỉnh sửa nhưng vẫn vi phạm lỗi đạo văn thì xử lý ra sao?",
        "gold_doc": "ueh-xu-ly-vi-pham-nguoi-hoc",
        "evidence": ["lập biên bản"],
        "gold_answer": "(Người học, bài thuộc học phần) Giảng viên phụ trách học phần lập biên bản/thông báo chuyển về đơn vị quản lý để xử lý tùy mức độ vi phạm (Phụ lục 3). Tài liệu giảng viên có đáp án khác: sản phẩm không được công nhận/nghiệm thu.",
        "filter": {"audience": "student"},
    },
    {
        "id": "Q3",
        "query": "Khi ghi nhận việc dùng công cụ AI trong bài làm, câu acknowledgement cần nêu những thông tin gì?",
        "gold_doc": "rmit-ai-acknowledgement-guide",
        "evidence": ["the name of the AI tool and its creator"],
        "gold_answer": "Cách đã dùng công cụ AI, tên công cụ và đơn vị tạo ra nó, năm tạo nội dung; mẫu: 'I used [tool] (Creator, year) to ...'. Không còn bắt buộc ghi số phiên bản hay ngày dùng.",
        "filter": None,
    },
    {
        "id": "Q4",
        "query": "Những loại thông tin nào không được phép nhập vào công cụ AI tạo sinh?",
        "gold_doc": ["una-genai-policy-general", "una-genai-policy-faculty"],
        "evidence": ["Social Security numbers"],
        "gold_answer": "Hồ sơ sinh viên theo FERPA, hồ sơ tuyển sinh, số an sinh xã hội, thông tin thẻ, dữ liệu y tế/bảo hiểm, dữ liệu người tham gia nghiên cứu, hồ sơ nhân sự, ngân sách, thông tin donor, hộ chiếu/visa, tài liệu có bản quyền...",
        "filter": None,
    },
    {
        "id": "Q5",
        "query": "Thông tư 49/2026/TT-BGDĐT có hiệu lực từ ngày nào và thay thế những thông tư nào?",
        "gold_doc": "tt49-2026-ung-dung-cong-nghe-ai",
        "evidence": ["15 tháng 08 năm 2026", "30/2023/TT-BGDĐT"],
        "gold_answer": "Hiệu lực từ 15/08/2026; Thông tư 15/2018/TT-BGDĐT và Thông tư 30/2023/TT-BGDĐT hết hiệu lực từ ngày đó.",
        "filter": None,
    },
]


# ---------------------------------------------------------------------------
# Chunker theo heading (chiến lược custom của nhóm)
# ---------------------------------------------------------------------------
class HeadingChunker:
    """Chunk văn bản quy định theo heading Markdown (## Điều ..., ### ...).

    Lý do: văn bản quy định được người soạn chia sẵn theo Điều/mục — mỗi mục là một đơn vị
    ngữ nghĩa trọn vẹn. Mỗi chunk được gắn lại đường dẫn heading (H1 > H2 > H3) để mảnh con
    không mất ngữ cảnh "đang nói về điều gì, của trường nào". Mục dài quá max_chars thì
    hạ xuống RecursiveChunker và gắn lại tiêu đề vào từng mảnh con.
    """

    HEADING = re.compile(r"^(#{1,6})\s+(.*)$")

    def __init__(self, max_chars: int = 800) -> None:
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        sections: list[tuple[list[str], list[str]]] = []  # (heading path, body lines)
        path: list[str] = []
        body: list[str] = []
        for line in text.splitlines():
            match = self.HEADING.match(line)
            if match:
                if any(b.strip() for b in body):
                    sections.append((list(path), body))
                body = []
                level = len(match.group(1))
                path = path[: level - 1] + [match.group(2).strip()]
            else:
                body.append(line)
        if any(b.strip() for b in body):
            sections.append((list(path), body))

        chunks: list[str] = []
        for heading_path, lines in sections:
            header = " > ".join(heading_path)
            content = "\n".join(lines).strip()
            budget = max(200, self.max_chars - len(header) - 2)
            if len(content) <= budget:
                pieces = [content]
            else:
                pieces = RecursiveChunker(chunk_size=budget).chunk(content)
            chunks.extend(f"{header}\n{piece}" if header else piece for piece in pieces)
        return chunks


def make_chunker(name: str):
    if name == "fixed":
        return FixedSizeChunker(chunk_size=500, overlap=100)
    if name == "recursive":
        return RecursiveChunker(chunk_size=500)
    if name == "heading":
        return HeadingChunker(max_chars=800)
    raise ValueError(f"unknown strategy: {name}")


STRATEGY_LABELS = {
    "fixed": "FixedSizeChunker(chunk_size=500, overlap=100)",
    "recursive": "RecursiveChunker(chunk_size=500)",
    "heading": "HeadingChunker(max_chars=800) — custom, theo Điều/mục",
}


# ---------------------------------------------------------------------------
# Embedding: Gemini có cache theo hash nội dung (chạy lại không tốn quota); fallback mock.
# ---------------------------------------------------------------------------
class CachedGeminiEmbedder:
    def __init__(self, model_name: str) -> None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("missing GEMINI_API_KEY / GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self._backend_name = f"{model_name} (cached)"
        self.cache: dict[str, list[float]] = {}
        if CACHE_PATH.exists():
            self.cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self.model_name}|{text}".encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def prefetch(self, texts: list[str], batch_size: int = 90) -> None:
        # Free tier: 100 embedding/phút -> gửi batch <100 và chờ khi bị 429.
        missing = list(dict.fromkeys(t for t in texts if self._key(t) not in self.cache))
        for start in range(0, len(missing), batch_size):
            batch = missing[start : start + batch_size]
            for attempt in range(5):
                try:
                    response = self.client.models.embed_content(model=self.model_name, contents=batch)
                    break
                except Exception as exc:  # noqa: BLE001
                    if "429" not in str(exc) or attempt == 4:
                        raise
                    print(f"[rate-limit] chờ 65s rồi thử lại ({start}/{len(missing)})", flush=True)
                    time.sleep(65)
            for text, emb in zip(batch, response.embeddings):
                self.cache[self._key(text)] = self._normalize([float(v) for v in emb.values])
            self.save()

    def save(self) -> None:
        CACHE_PATH.parent.mkdir(exist_ok=True)
        CACHE_PATH.write_text(json.dumps(self.cache), encoding="utf-8")

    def __call__(self, text: str) -> list[float]:
        key = self._key(text)
        if key not in self.cache:
            self.prefetch([text])
        return self.cache[key]


def make_embedder():
    provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip().lower()
    if provider == "gemini":
        try:
            return CachedGeminiEmbedder(os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"))
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] Gemini embedder unavailable ({exc}); falling back to mock")
    return _mock_embed


def make_llm():
    """LLM thật (Gemini) nếu có key; nếu không thì LLM trích đoạn đầu ngữ cảnh."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash")
    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)

            def gemini_llm(prompt: str) -> str:
                for attempt in range(4):
                    try:
                        response = client.models.generate_content(model=model, contents=prompt)
                        return (response.text or "").strip()
                    except Exception as exc:  # noqa: BLE001
                        if ("429" not in str(exc) and "503" not in str(exc)) or attempt == 3:
                            raise
                        time.sleep(30)
                return ""

            gemini_llm.backend = model  # type: ignore[attr-defined]
            return gemini_llm
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] Gemini LLM unavailable ({exc}); using extractive demo LLM")

    def extractive_llm(prompt: str) -> str:
        context = prompt.split("NGỮ CẢNH:", 1)[-1].split("CÂU HỎI:", 1)[0]
        return "[extractive] " + " ".join(context.split())[:300]

    extractive_llm.backend = "extractive-demo"  # type: ignore[attr-defined]
    return extractive_llm


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------
def parse_markdown(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    _, frontmatter, body = text.split("---", 2)
    metadata = {}
    for key, value in re.findall(r"^(\w+):\s*(.+)$", frontmatter, re.M):
        metadata[key] = value.strip().strip('"')
    return metadata, body.strip()


def load_corpus() -> list[tuple[str, dict, str]]:
    return [(p.stem, *parse_markdown(p)) for p in sorted(CORPUS_DIR.glob("*.md"))]


def build_documents(strategy: str, corpus) -> list[Document]:
    chunker = make_chunker(strategy)
    docs: list[Document] = []
    for stem, metadata, body in corpus:
        for i, chunk in enumerate(chunker.chunk(body)):
            docs.append(
                Document(
                    id=f"{stem}#{i}",
                    content=chunk,
                    metadata={**metadata, "doc_id": stem, "chunk_index": i, "strategy": strategy},
                )
            )
    return docs


# ---------------------------------------------------------------------------
# Chấm điểm
# ---------------------------------------------------------------------------
def gold_docs(q: dict) -> set[str]:
    gold = q["gold_doc"]
    return set(gold) if isinstance(gold, list) else {gold}


def score_query(q: dict, results: list[dict]) -> dict:
    gold = gold_docs(q)
    doc_ids = [r["metadata"]["doc_id"] for r in results]
    has_evidence = [q["evidence"][0] in r["content"] for r in results]
    context = "\n".join(r["content"] for r in results)
    evidence_in_context = all(e in context for e in q["evidence"])

    # Chấm ngây thơ: chỉ nhìn doc_id.
    naive = 2 if doc_ids and doc_ids[0] in gold else (1 if gold & set(doc_ids) else 0)
    # Chấm mức nội dung: chunk chứa bằng chứng phải là chunk của doc gold.
    first_hit = next((i for i, (d, h) in enumerate(zip(doc_ids, has_evidence)) if d in gold and h), None)
    if first_hit is None or not evidence_in_context:
        content = 0
    else:
        content = 2 if first_hit == 0 else 1
    return {"naive": naive, "content": content, "hit_rank": None if first_hit is None else first_hit + 1}


def run_strategy(strategy: str, corpus, embedder, llm, out, with_agent: bool = True) -> dict:
    docs = build_documents(strategy, corpus)
    if hasattr(embedder, "prefetch"):
        embedder.prefetch([d.content for d in docs] + [q["query"] for q in QUERIES])
    store = EmbeddingStore(collection_name=f"bench_{strategy}", embedding_fn=embedder)
    store.add_documents(docs)
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm)

    lengths = [len(d.content) for d in docs]
    out(f"\n{'=' * 100}\nSTRATEGY: {STRATEGY_LABELS[strategy]}")
    out(f"chunks={store.get_collection_size()}  avg_len={sum(lengths) / len(lengths):.0f}  "
        f"min={min(lengths)}  max={max(lengths)}\n{'=' * 100}")

    totals = {"naive": 0, "content": 0}
    rows = []
    for q in QUERIES:
        results = store.search_with_filter(q["query"], top_k=TOP_K, metadata_filter=q["filter"])
        s = score_query(q, results)
        totals["naive"] += s["naive"]
        totals["content"] += s["content"]
        out(f"\n[{q['id']}] {q['query']}")
        out(f"  filter={q['filter']}  gold={sorted(gold_docs(q))}  evidence={q['evidence']}")
        for rank, r in enumerate(results, start=1):
            preview = " ".join(r["content"].split())[:150]
            out(f"  {rank}. score={r['score']:.3f}  {r['id']:40}  {preview}")
        out(f"  -> naive(doc_id)={s['naive']}/2   content(evidence)={s['content']}/2   evidence_rank={s['hit_rank']}")
        answer = ""
        if with_agent:
            try:
                answer = agent.answer(q["query"], top_k=TOP_K, metadata_filter=q["filter"])
            except Exception as exc:  # noqa: BLE001
                answer = f"[LLM error: {exc}]"
            out("  agent: " + " ".join(answer.split())[:600])
        rows.append({"q": q, "results": results, "score": s, "answer": answer})
    out(f"\nTOTAL {strategy}: naive(doc_id)={totals['naive']}/10   content(evidence)={totals['content']}/10")
    return {"strategy": strategy, "store": store, "totals": totals, "rows": rows,
            "chunks": len(docs), "avg_len": sum(lengths) / len(lengths)}


def run_ab_filter(run: dict, out) -> None:
    store = run["store"]
    for q in QUERIES:
        if not q["filter"]:
            continue
        out(f"\n--- A/B metadata filter [{run['strategy']}] {q['id']}: {q['query']}")
        for label, flt in (("KHÔNG filter", None), (f"filter={q['filter']}", q["filter"])):
            results = store.search_with_filter(q["query"], top_k=TOP_K, metadata_filter=flt)
            s = score_query(q, results)
            out(f"  {label}:  content={s['content']}/2")
            for rank, r in enumerate(results, start=1):
                out(f"    {rank}. score={r['score']:.3f}  {r['id']:40}  audience={r['metadata'].get('audience')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default=STRATEGY, choices=["fixed", "recursive", "heading", "all"])
    parser.add_argument("--no-agent", action="store_true", help="bỏ bước gọi LLM")
    args = parser.parse_args()

    load_dotenv(override=False)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    lines: list[str] = []

    def out(line: str = "") -> None:
        print(line)
        lines.append(line)

    corpus = load_corpus()
    embedder = make_embedder()
    llm = make_llm()
    out(f"Corpus: {CORPUS_DIR.relative_to(ROOT)}  ({len(corpus)} tài liệu)")
    out(f"Embedding backend: {getattr(embedder, '_backend_name', 'mock')}")
    out(f"LLM backend: {getattr(llm, 'backend', '?')}")

    strategies = ["fixed", "recursive", "heading"] if args.strategy == "all" else [args.strategy]
    runs = [run_strategy(s, corpus, embedder, llm, out, with_agent=not args.no_agent) for s in strategies]

    out(f"\n{'=' * 100}\nA/B METADATA FILTER\n{'=' * 100}")
    for run in runs:
        run_ab_filter(run, out)

    out(f"\n{'=' * 100}\nTỔNG HỢP\n{'=' * 100}")
    out(f"{'strategy':12} {'chunks':>7} {'avg_len':>8} {'naive/10':>9} {'content/10':>11}")
    for run in runs:
        out(f"{run['strategy']:12} {run['chunks']:>7} {run['avg_len']:>8.0f} "
            f"{run['totals']['naive']:>9} {run['totals']['content']:>11}")

    if args.strategy == "all":
        OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nĐã ghi {OUTPUT_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
