from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    NO_CONTEXT_MESSAGE = "Không tìm thấy thông tin trong cơ sở tri thức để trả lời câu hỏi này."

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def build_prompt(self, question: str, chunks: list[dict]) -> str:
        context_lines = []
        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata", {})
            source = metadata.get("doc_id") or metadata.get("source") or chunk.get("id", "unknown")
            context_lines.append(f"[{index}] (nguồn: {source})\n{chunk['content'].strip()}")
        context = "\n\n".join(context_lines)
        return (
            "Bạn là trợ lý trả lời câu hỏi dựa trên cơ sở tri thức.\n"
            "Chỉ dùng thông tin trong NGỮ CẢNH bên dưới. Trích dẫn số [n] của đoạn đã dùng.\n"
            "Nếu ngữ cảnh không chứa câu trả lời, hãy nói rõ là không tìm thấy thông tin.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n"
            "TRẢ LỜI:"
        )

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        chunks = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        if not chunks:
            return self.NO_CONTEXT_MESSAGE
        return self.llm_fn(self.build_prompt(question, chunks))
