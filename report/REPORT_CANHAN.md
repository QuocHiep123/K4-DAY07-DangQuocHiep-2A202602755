# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đặng Quốc Hiệp — MSSV: 2A202602755
**Nhóm:** DKH — chủ đề *AI & liêm chính học thuật trong đại học*
**Vai trong nhóm:** R3 · Strategy (chunker theo heading)
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding gần như cùng hướng trong không gian ngữ nghĩa, tức là hai đoạn văn nói về cùng một ý, dù có thể dùng từ khác nhau. Cosine chỉ đo *góc* giữa hai vector, không đo độ dài, nên nó phản ánh "nói về cái gì" chứ không phải "dài bao nhiêu".

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên phải ghi rõ công cụ AI đã dùng trong bài."
- Câu B: "Người học cần khai báo việc sử dụng ChatGPT trong sản phẩm học thuật."
- Tại sao tương đồng: gần như không trùng từ nào ("sinh viên"/"người học", "ghi rõ"/"khai báo", "công cụ AI"/"ChatGPT") nhưng cùng một nghĩa. Gemini embedding cho **0.831**, chứng tỏ embedding hiểu nghĩa chứ không chỉ khớp từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tỷ lệ tương đồng từ 20% trở lên là dấu hiệu đạo văn."
- Câu B: "Thư viện mở cửa từ 8 giờ sáng đến 5 giờ chiều."
- Tại sao khác: hai chủ đề không liên quan (liêm chính học thuật và giờ mở cửa). Thực tế ra **0.556**, thấp nhất trong 5 cặp. Với Gemini embedding, "thấp" nghĩa là khoảng 0.5 chứ không phải gần 0.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ dài vector bị ảnh hưởng bởi độ dài văn bản và tần suất từ. Một chunk dài và một câu hỏi ngắn có thể cùng chủ đề nhưng cách xa nhau theo Euclid. Cosine chuẩn hoá độ dài nên chỉ so hướng, tức là so ngữ nghĩa. Khi vector đã chuẩn hoá (‖v‖ = 1), cosine bằng đúng dot product, nên tính rất rẻ.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Phép tính:* step = 500 − 50 = 450; số chunk = ceil((10000 − 50) / 450) = ceil(22.11) = **23**.
> *Kiểm chứng bằng code:* `len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000))` → **23** ✅

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng lên ceil(9900 / 400) = **25** (code cũng ra 25), vì mỗi bước chỉ tiến 400 ký tự. Overlap lớn hơn giúp một câu hoặc một điều khoản nằm ngay ranh giới vẫn xuất hiện trọn vẹn trong ít nhất một chunk, nên thông tin có thêm cơ hội lọt top-k. Đổi lại, store to hơn và top-k dễ bị hai chunk gần trùng nhau chiếm chỗ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Mình tách câu bằng regex lookbehind `(?<=[.!?])\s+`, tức là cắt ở khoảng trắng **đứng sau** dấu `.`, `!`, `?`. Dấu câu vì vậy được giữ lại trong câu (split thẳng bằng `[.!?]\s+` sẽ nuốt mất dấu). `\s+` phủ luôn cả `". "` lẫn `".\n"`. Sau đó gom `max_sentences_per_chunk` câu thành một chunk và `strip()`. Text rỗng hoặc chỉ có khoảng trắng thì trả `[]`.
> **Edge case chưa xử lý:** chữ viết tắt (`TS.`, `v.v.`, `e.g.`) và số thập phân bị cắt nhầm. Ngoài ra, heading Markdown không kết thúc bằng dấu câu nên bị dính vào câu kế bên. Trên corpus của nhóm, mình thấy chunk kiểu `"...pháp luật hiện hành. ### 2.3 Đối với các bài kiểm tra..."`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đi theo hai chiều. *Đệ quy xuống:* cắt bằng separator lớn nhất (`\n\n`), mảnh nào vẫn dài hơn `chunk_size` thì gọi lại `_split` với các separator nhỏ hơn. *Gom lên:* nối các mảnh nhỏ liền kề (bằng chính separator đó) tới khi sắp vượt `chunk_size`, để không sinh chunk vụn. Có ba base case: (1) text ≤ `chunk_size` thì trả luôn; (2) hết separator hoặc gặp `""` thì cắt cứng theo `chunk_size`, nhánh này giúp test `separators=[]` pass; (3) separator hiện tại không xuất hiện trong text thì chuyển sang separator kế tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Store chỉ chạy in-memory. Mình bỏ nhánh Chroma vì code gốc gán `_use_chroma = True` trước khi tạo client. `_make_record` copy metadata (không dùng chung object với người gọi), `setdefault("doc_id", doc.id)` và embed nội dung. `add_documents` không tự chunk: 1 `Document` = 1 record. `search` và `search_with_filter` cùng đi qua `_search_records`. Hàm này embed câu hỏi, tính dot product với từng record (vector đã chuẩn hoá nên dot = cosine), sort giảm dần, lấy `top_k` và bỏ trường `embedding` khỏi kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Mình **lọc trước** (giữ record có mọi cặp key/value khớp `metadata_filter`) rồi mới search trên tập ứng viên đã lọc. Nếu lấy top-k trước rồi mới lọc, cả k slot có thể bị tài liệu sai đối tượng chiếm hết và kết quả rỗng. Filter `None` hoặc `{}` thì tập ứng viên là toàn bộ store, nên kết quả trùng với `search()`. `delete_document` giữ lại các record có `metadata['doc_id'] != doc_id` và trả `True` nếu kích thước store giảm. Vì `doc_id` trỏ về file gốc, một lệnh xoá gỡ được toàn bộ chunk `file#0..n`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent chạy ba bước: `search_with_filter` (có nhận `metadata_filter` tuỳ chọn) → dựng prompt → gọi `llm_fn`. Ngữ cảnh được đánh số `[1] [2] [3]` kèm `(nguồn: doc_id)`. Prompt yêu cầu model chỉ dùng ngữ cảnh, trích số `[n]`, và nói rõ "không tìm thấy" nếu ngữ cảnh không có đáp án. Nếu store rỗng hoặc filter không còn ứng viên nào thì trả thông báo luôn, không gọi LLM. Trong benchmark, chống bịa có tác dụng thật: ở Q1 với chunker `fixed`/`recursive`, agent trả lời "ngữ cảnh không cung cấp tỷ lệ cụ thể" thay vì đoán ra một con số.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.13, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.07s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

`python main.py "Chunking là gì?"` cũng chạy trọn vẹn với backend `gemini-embedding-001`: top-1 là `chunking_experiment_report.md` (score 0.705).

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Embedding dùng `gemini-embedding-001` (đã chuẩn hoá). Mình ghi dự đoán trước khi chạy. Cột `mock` là điểm của `MockEmbedder`, để so sánh.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên phải ghi rõ công cụ AI đã dùng trong bài. | Người học cần khai báo việc sử dụng ChatGPT trong sản phẩm học thuật. | cao | 0.831 (mock −0.091) | ✅ |
| 2 | Đạo văn là sử dụng ý tưởng của người khác mà không trích dẫn. | Plagiarism means using someone else's work or ideas without giving them proper credit. | cao (khác ngôn ngữ, nên thấp hơn cặp 1) | 0.767 (mock −0.007) | ✅ |
| 3 | Tỷ lệ tương đồng từ 20% trở lên là dấu hiệu đạo văn. | Thư viện mở cửa từ 8 giờ sáng đến 5 giờ chiều. | thấp | 0.556 (mock 0.110) | ✅ (thấp nhất, nhưng không gần 0) |
| 4 | Được phép dùng AI để kiểm tra chính tả. | Không được phép dùng AI để kiểm tra chính tả. | thấp (nghĩa ngược nhau) | **0.924** | ❌ |
| 5 | Giảng viên chấm bài bằng công cụ AI. | Công cụ AI chấm bài của giảng viên. | cao | 0.951 (mock −0.100) | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 4: "được phép" và "không được phép" cho 0.924, gần bằng hai câu diễn đạt lại cùng một ý. Embedding mã hoá **chủ đề** (AI, kiểm tra chính tả) mạnh hơn nhiều so với **cực tính/phủ định**. Với corpus quy định, đây là rủi ro thật: truy vấn "được dùng AI khi nào" sẽ kéo về cả điều khoản *cấm*, nên phải để LLM đọc kỹ ngữ cảnh chứ không được tin vào score. Cặp 2 cũng cho thấy embedding đa ngữ khớp được câu Việt với câu Anh (0.767), và nhờ vậy câu hỏi tiếng Việt vẫn tìm được tài liệu RMIT/UNA bằng tiếng Anh. Còn mock cho điểm ngẫu nhiên quanh 0 ở mọi cặp, xác nhận nó không có ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chiến lược của mình: **`HeadingChunker(max_chars=800)`**, loại custom, chunk theo Điều/mục và gắn đường dẫn heading vào từng chunk. Mình chạy 5 câu hỏi chung của nhóm bằng `bench.py`, với embedding `gemini-embedding-001` và LLM `gemini-2.5-flash`. Log đầy đủ nằm trong `ket_qua_benchmark.txt`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Theo UEH, tỷ lệ tương đồng từ bao nhiêu % thì bị xem là có dấu hiệu đạo văn? | `ueh-dao-van…#4`: *Điều 2 > Tỷ lệ tương đồng học thuật*, là định nghĩa, **không có con số**; chunk chứa "20% trở lên" đứng **top-3** | 0.886 | Có (top-3) | "Từ 20% trở lên, không tính trích dẫn, TLTK, …" [3] ✅ |
| 2 | Sản phẩm học thuật đã chỉnh sửa nhưng vẫn vi phạm lỗi đạo văn thì xử lý ra sao? *(filter `audience=student`)* | `ueh-xu-ly-vi-pham-nguoi-hoc#2`: *Điều 3 > 2.3 Bài kiểm tra, bài tập, tiểu luận*, "giảng viên … lập biên bản chuyển đơn vị quản lý" | 0.789 | Có (top-1) | "Giảng viên phụ trách lập biên bản/thông báo chuyển đơn vị quản lý xử lý theo mức độ" [1] ✅ |
| 3 | Câu acknowledgement khi dùng công cụ AI cần nêu những thông tin gì? | `rmit-ai-acknowledgement-guide#3`: *Template for acknowledging…*, gồm cách dùng, tên công cụ và creator, năm | 0.833 | Có (top-1) | "Cách dùng; tên công cụ và nhà phát triển; năm tạo nội dung" ✅ |
| 4 | Những loại thông tin nào không được phép nhập vào công cụ AI tạo sinh? | `una-genai-policy-faculty#7`: *Information that may NOT be input…*, **chỉ có câu mở đầu**, danh sách bị tách sang chunk khác | 0.788 | Một phần | Trả lời chung chung ("thông tin cá nhân, bảo mật…"), thiếu danh sách cụ thể ⚠️ |
| 5 | Thông tư 49/2026 có hiệu lực từ ngày nào, thay thế thông tư nào? | `tt49…#0`: phần mở đầu thông tư (số hiệu, ngày ký); *Điều 22. Điều khoản thi hành* đứng **top-2** | 0.798 | Có (top-2) | "Hiệu lực 15/08/2026; thay thế TT 15/2018 và TT 30/2023" [2] ✅ |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 nếu chấm theo tài liệu. Theo nội dung (chunk thực sự chứa đáp án) là **4 / 5**, vì Q4 hụt.

Điểm theo rubric `SCORING.md`: Q1 = 1, Q2 = 2, Q3 = 2, Q4 = 1, Q5 = 1, tổng **7 / 10**. Trong khi đó, chấm ngây thơ theo `doc_id` cho 10/10. Chấm tự động theo chuỗi bằng chứng (`evidence`) cho 6/10.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Từ bản của Nguyễn Việt Dũng: cùng chiến lược recursive nhưng dùng OpenAI `text-embedding-3-small` thì Q3/Q4 (câu hỏi tiếng Việt, tài liệu tiếng Anh) bị kéo hết sang quy định UEH tiếng Việt (naive 6/10, so với 10/10 khi dùng Gemini). Model embedding quan trọng không kém chiến lược chunking.
> Khi nhóm chạy đối chứng cùng Gemini, chiến lược `FixedSizeChunker` có overlap 100 của Nguyễn Thế Khang, tuy "thô", lại **thắng mình ở Q4**. Danh sách dài bị cắt ngang ở ranh giới, nhưng nhờ overlap nên chunk top-1 vẫn chứa phần đầu danh sách ("Student records subject to FERPA… Social Security numbers"). Chunker theo heading của mình thì tách phần mở đầu section khỏi danh sách, và mảnh mở đầu lại khớp câu hỏi nhất. Bài học: nên kết hợp heading với overlap, hoặc khi phải cắt một section thì đảm bảo mảnh đầu mang theo nội dung chứ không chỉ câu dẫn.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
