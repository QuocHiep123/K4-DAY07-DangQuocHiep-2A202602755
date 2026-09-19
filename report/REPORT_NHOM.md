# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** DKH
**Thành viên:**
- Đặng Quốc Hiệp — 2A202602755 (R3 · Strategy — HeadingChunker)
- Nguyễn Thế Khang — 2A202602964 (R1 · Data — FixedSizeChunker)
- Nguyễn Việt Dũng — 2A202602812 (R2 · Benchmark — RecursiveChunker)
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định về **sử dụng AI và liêm chính học thuật** trong đại học (đạo văn, khai báo AI, xử lý vi phạm, bảo mật dữ liệu khi dùng AI). Nguồn là văn bản cấp Bộ (Việt Nam) và chính sách của 3 trường (UEH, RMIT, UNA). Thư mục: `data/ai-liem-chinh-hoc-thuat/`.

**Tại sao nhóm chọn chủ đề này?**
> Đây là quy định đại học mà sinh viên cần tra cứu thật và thường xuyên ("có được dùng ChatGPT không, phải ghi nguồn thế nào, vi phạm thì bị gì"). Thông tư 49/2026 vừa có hiệu lực từ 15/08/2026. Chủ đề này cũng hợp để thử metadata filter: cùng một hành vi vi phạm nhưng quy định xử lý **khác nhau theo đối tượng** (người học và giảng viên), và corpus song ngữ Việt–Anh cho phép kiểm tra embedding đa ngữ.

### Danh sách tài liệu (Data Inventory)

Tất cả lấy ngày **2026-09-19**. Số ký tự tính trên phần thân, đã bỏ frontmatter.

| # | Tên tài liệu (`doc_id`) | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `tt49-2026-ung-dung-cong-nghe-ai` | luatvietnam.vn/…/thong-tu-49-2026-tt-bgddt-… | 49/2026/TT-BGDĐT, ban hành 2026-06-30, hiệu lực 2026-08-15 | 12,643 | audience=all, department=moet, category=national-regulation, language=vi, jurisdiction=VN |
| 2 | `ueh-dao-van-ai-quy-dinh-chung` | daotao.ueh.edu.vn/quy-dinh-ve-viec-kiem-soat-… | 4002/QĐ-ĐHKT-NCPTGKTC, 2025-12-18 | 11,842 | audience=all, academic-affairs, university-policy, vi, VN |
| 3 | `ueh-xu-ly-vi-pham-nguoi-hoc` | (cùng URL UEH) | 4002/QĐ-ĐHKT-NCPTGKTC, 2025-12-18 | 2,783 | **audience=student**, academic-affairs, university-policy, vi, VN |
| 4 | `ueh-xu-ly-vi-pham-giang-vien` | (cùng URL UEH) | 4002/QĐ-ĐHKT-NCPTGKTC, 2025-12-18 | 2,771 | **audience=faculty**, academic-affairs, university-policy, vi, VN |
| 5 | `rmit-vn-academic-integrity-ai` | rmit.edu.vn/students/…/academic-integrity | not-stated | 11,327 | audience=student, academic-affairs, university-policy, en, VN |
| 6 | `rmit-ai-acknowledgement-guide` | rmit.libguides.com/referencing_AI_tools/acknowledging | last-updated 2026-07-29 | 3,003 | audience=student, library, guideline, en, AU |
| 7 | `una-genai-policy-general` | una.edu/academics/generative-ai-policy.html | not-stated | 5,442 | audience=all, provost, university-policy, en, US |
| 8 | `una-genai-policy-faculty` | (cùng URL UNA) | not-stated | 7,562 | audience=faculty, provost, university-policy, en, US |
| 9 | `una-genai-policy-staff` | (cùng URL UNA) | not-stated | 1,145 | audience=staff, provost, university-policy, en, US |
| 10 | `una-genai-policy-students` | (cùng URL UNA) | not-stated | 5,111 | audience=student, provost, university-policy, en, US |

Kết quả script kiểm tra CP2: **10 file, mọi file `OK`, `sources.csv` khớp 1-1**, audience = `{student: 4, all: 3, faculty: 2, staff: 1}`.

Hai trang nguồn (UEH và UNA) gộp quy định cho nhiều đối tượng trên **một** trang, nên nhóm **tách thành nhiều file theo `audience`**. Nếu không tách, `metadata_filter={"audience": "student"}` sẽ không lọc được gì. `document_version` chỉ ghi khi nguồn thật sự nêu, không có thì ghi `not-stated`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | str | `ueh-xu-ly-vi-pham-nguoi-hoc` | Trỏ về file gốc; `delete_document` và truy vết nguồn trích dẫn `[n]` |
| `audience` | enum | `student` / `faculty` / `staff` / `all` | Lọc đúng đối tượng khi cùng hành vi có chế tài khác nhau (Q2) |
| `department` | str | `academic-affairs`, `library`, `moet` | Tách hướng dẫn thư viện (cách ghi nguồn) khỏi quy chế xử lý |
| `category` | enum | `national-regulation`, `university-policy`, `guideline` | Ưu tiên văn bản pháp quy khi hỏi về hiệu lực và căn cứ pháp lý |
| `language` | str | `vi`, `en` | Có thể lọc theo ngôn ngữ trả lời mong muốn |
| `jurisdiction` / `issuer` | str | `VN` / `Đại học Kinh tế TP.HCM (UEH)` | Tránh trộn quy định của trường Mỹ vào câu hỏi về trường Việt Nam |
| `source_url`, `retrieved_at`, `document_version` | str | `…/academic-integrity`, `2026-09-19`, `4002/QĐ-…` | Provenance: kiểm tra độ mới và dẫn nguồn khi trả lời |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Nhóm chạy `ChunkingStrategyComparator().compare(body, chunk_size=500)` trên phần thân (đã bỏ frontmatter) của 3 tài liệu. Cột HeadingChunker được thêm vào để so sánh.

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `ueh-xu-ly-vi-pham-nguoi-hoc` (2,783) | FixedSizeChunker (`fixed_size`) | 7 | 440 | Kém: cắt giữa từ/câu (chunk 2 bắt đầu bằng "dẫn hoặc đơn vị quản lý…") |
| | SentenceChunker (`by_sentences`) | 5 | 554 | Trung bình: heading `### 2.3` dính vào câu trước vì không có dấu chấm |
| | RecursiveChunker (`recursive`) | 6 | 462 | Khá: cắt theo đoạn `\n\n` |
| | *HeadingChunker (custom)* | 6 | 530 | Tốt: mỗi chunk là một mục a)/b)/c), có tiêu đề Điều |
| `rmit-ai-acknowledgement-guide` (3,003) | FixedSizeChunker | 7 | 472 | Kém: cắt giữa câu |
| | SentenceChunker | 6 | 498 | Khá: văn tiếng Anh có dấu câu chuẩn |
| | RecursiveChunker | 7 | 427 | Khá |
| | *HeadingChunker* | 6 | 562 | Tốt: đúng 3 mục Acknowledging / Guidelines / Template |
| `tt49-2026-ung-dung-cong-nghe-ai` (12,643) | FixedSizeChunker | 28 | 500 | Kém |
| | SentenceChunker | 25 | 503 | Trung bình: điều khoản liệt kê a), b) không có dấu chấm nên gộp lung tung |
| | RecursiveChunker | 31 | 406 | Khá, nhưng mảnh con mất tên Điều |
| | *HeadingChunker* | 24 | 632 | Tốt: chunk mang "Điều 22. Điều khoản thi hành" ở đầu |

### Chiến lược của từng thành viên

Mỗi thành viên tự chạy chiến lược của mình trên máy riêng, với backend embedding mình có (xem bảng "Kết quả mỗi thành viên tự chạy" bên dưới). Vì ba backend khác nhau nên điểm tự chạy **không so trực tiếp được**. Để so sánh công bằng, nhóm chạy thêm một **bản đối chứng**: cả 3 chiến lược cùng chạy qua `bench.py --strategy all`, cùng embedding `gemini-embedding-001`, cùng LLM `gemini-2.5-flash`, cùng 5 query (log trong `ket_qua_benchmark.txt`). Kết luận về chiến lược dựa trên bản đối chứng này.

**Thành viên 1 — Đặng Quốc Hiệp (2A202602755)**
- **Loại chiến lược:** custom `HeadingChunker(max_chars=800)`, chunk theo Điều/mục (vai bắt buộc của L3A)
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản quy định đã được người soạn chia sẵn theo `## Điều n` và `### mục`, và mỗi mục là một đơn vị ngữ nghĩa trọn vẹn. Chunker tách trước mỗi heading và **gắn đường dẫn heading `H1 > H2 > H3` vào đầu mỗi chunk**, để một mảnh như "a) Khi bị phát hiện vi phạm lần đầu…" vẫn mang theo thông tin "UEH > Xử lý vi phạm đối với người học > Điều 3". Mục nào dài quá 800 ký tự thì hạ xuống `RecursiveChunker` và gắn lại tiêu đề vào từng mảnh con.
- **Code snippet:**
```python
class HeadingChunker:
    HEADING = re.compile(r"^(#{1,6})\s+(.*)$")

    def chunk(self, text: str) -> list[str]:
        sections, path, body = [], [], []
        for line in text.splitlines():
            match = self.HEADING.match(line)
            if match:
                if any(b.strip() for b in body):
                    sections.append((list(path), body))
                body = []
                level = len(match.group(1))
                path = path[: level - 1] + [match.group(2).strip()]   # H1 > H2 > H3
            else:
                body.append(line)
        if any(b.strip() for b in body):
            sections.append((list(path), body))

        chunks = []
        for heading_path, lines in sections:
            header = " > ".join(heading_path)
            content = "\n".join(lines).strip()
            budget = max(200, self.max_chars - len(header) - 2)
            pieces = [content] if len(content) <= budget else RecursiveChunker(chunk_size=budget).chunk(content)
            chunks.extend(f"{header}\n{piece}" if header else piece for piece in pieces)  # gắn lại tiêu đề
        return chunks
```

**Thành viên 2 — Nguyễn Thế Khang (2A202602964)**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=100)`
- **Mô tả & lý do chọn:** Đây là baseline không phụ thuộc cấu trúc. Overlap 100 (20%) giúp thông tin nằm ở ranh giới có hai cơ hội lọt top-k, và corpus crawl về không phải lúc nào cũng có heading sạch.
- **Tự chạy:** backend TF-IDF (lexical, offline); 162 chunk; agent là extractive baseline, không phải LLM; đủ top-3 từng câu và A/B filter.

**Thành viên 3 — Nguyễn Việt Dũng (2A202602812)**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=500)`
- **Mô tả & lý do chọn:** Cắt theo ranh giới tự nhiên `\n\n` → `\n` → `. ` → ` `, rồi gom lại tới sát 500 ký tự. Cách này tôn trọng đoạn văn mà không cần biết cú pháp Markdown.
- **Tự chạy:** embedding OpenAI `text-embedding-3-small`, LLM `gpt-4.1-mini`; 177 chunk, avg_len 359; đủ top-3 từng câu và A/B filter.

### Kết quả mỗi thành viên tự chạy

Output gốc của từng người nằm trong thư mục `ket_qua_thanh_vien/`.

**Nguyễn Thế Khang:** TF-IDF (word unigram, L2) + agent extractive, fixed_size(500, overlap 100), 162 chunk. Rubric do nhóm chấm thủ công:

| # | Top-1 (score) | Chunk chứa đáp án? | Agent (extractive) | Rubric |
|---|---|---|---|---|
| Q1 | `ueh-dao-van…:003` định nghĩa đạo văn (0.456) | Không: 3 chunk UEH về định nghĩa/Turnitin, không có "20%" | Trích định nghĩa, không có con số | 0 |
| Q2 | `ueh-xu-ly-vi-pham-nguoi-hoc:002` (0.401) | Có, hạng 1 | Trích đúng câu b) "…lập biên bản/thông báo chuyển về đơn vị quản lý…" ✅ | 2 |
| Q3 | `ueh-dao-van…:014` nguyên tắc Minh bạch (0.216) | Không, top-3 toàn UEH | Trích quy định UEH, sai nguồn | 0 |
| Q4 | `ueh-dao-van…:011` Điều 4 (0.273) | Không, top-3 toàn UEH | Trích quy định UEH, sai nguồn | 0 |
| Q5 | `tt49…:029` **Điều 22** (0.359) | Có, hạng 1: chứa cả "15 tháng 08 năm 2026" và "30/2023/TT-BGDĐT" | Trích đúng hiệu lực và 2 TT bị thay thế ✅ | 2 |
| | | naive 6/10 · evidence 4/10 | | **4/10** |

A/B Q2 (Khang): top-1 **không đổi** (`nguoi-hoc:002`, vì TF-IDF khớp đúng cụm "vẫn vi phạm lỗi đạo văn" chỉ có trong tài liệu người học). Nhưng khi không lọc, hạng 2 là `ueh-xu-ly-vi-pham-giang-vien:000` (faculty, 0.349); lọc `student` thì slot đó được thay bằng `nguoi-hoc:005`. Filter ở đây làm sạch top-3 chứ không cứu top-1.

Ở lần chạy khám phá trước (cấu hình chunk mặc định, Hit@3/MRR mức tài liệu), TF-IDF cho fixed_size 100%/1.000, heading 100%/1.000, recursive 80%/0.800, by_sentences 80%/0.700. Mock chỉ 20–40%, gần ngẫu nhiên, xác nhận mock không mang ngữ nghĩa.

**Nguyễn Việt Dũng:** OpenAI `text-embedding-3-small` + `gpt-4.1-mini`, recursive (177 chunk). Rubric do nhóm chấm thủ công:

| # | Top-1 (score) | Chunk chứa đáp án? | Agent | Rubric |
|---|---|---|---|---|
| Q1 | `ueh-dao-van…` Điều 3 Turnitin (0.690) | Không (chunk có "20%" không vào top-3) | "Không có tỷ lệ cụ thể" (có căn cứ, nhưng không trả lời được) | 0 |
| Q2 | `ueh-xu-ly-vi-pham-nguoi-hoc` (0.619) | Có, hạng 1 | "Giảng viên lập biên bản chuyển đơn vị quản lý…" ✅ | 2 |
| Q3 | `ueh-dao-van…` nguyên tắc Minh bạch (0.661) | Không, top-3 toàn UEH, không có RMIT | Trả lời theo mẫu khai báo của UEH, **không phải** đáp án RMIT | 0 |
| Q4 | `ueh-dao-van…` hành vi vi phạm (0.664) | Không, top-3 toàn UEH, không có UNA | Chỉ nêu "dữ liệu nhạy cảm" theo UEH | 0 |
| Q5 | `tt49…` Điều 22 khoản 2 (0.543) | Một phần: có TT thay thế, thiếu khoản 1 "hiệu lực 15/08/2026" | **Sai ngày:** nói hiệu lực 30/06/2026 (nhầm ngày ký); bỏ sót TT 15/2018 | 1 |
| | | naive 6/10 · evidence 2/10 | | **3/10** |

A/B Q2 (Dũng): không filter thì top-1 là `ueh-xu-ly-vi-pham-giang-vien` (0.684, faculty), evidence 1/2; có filter `student` thì top-1 là `ueh-xu-ly-vi-pham-nguoi-hoc` (0.619), evidence 2/2. Kết quả này khớp với bản đối chứng Gemini.

### So Sánh Giữa Các Thành Viên (bản đối chứng, cùng Gemini)

Có ba cách chấm (chi tiết ở mục 3):
- **naive:** chỉ kiểm tra `doc_id` gold có nằm trong top-3 không.
- **evidence:** chunk chứa chuỗi đáp án (ví dụ `"20% trở lên"`) phải thuộc tài liệu gold và nằm trong top-3.
- **rubric:** theo `SCORING.md`, tính cả việc agent có trả lời đúng hay không.

| Thành viên | Chiến lược (Strategy) | Chunks / avg_len | naive | evidence | **rubric (/10)** | Điểm mạnh | Điểm yếu |
|-----------|----------|---------|------|------|----------------------|-----------|----------|
| Đặng Quốc Hiệp | HeadingChunker(800) | 140 / 552 | 10 | 6 | **7** | Chunk mạch lạc, có tiêu đề Điều; thắng Q1, Q3, và Q2 sau khi lọc | Câu dẫn của một section dài bị tách khỏi danh sách (Q4 hụt) |
| Nguyễn Thế Khang | FixedSize(500, ov=100) | 162 / 487 | 10 | 5 | **5** | Overlap giữ được danh sách dài (thắng Q4) | Cắt giữa câu; Q1 không lấy được con số "20%" nên agent phải trả lời "không tìm thấy" |
| Nguyễn Việt Dũng | Recursive(500) | 161 / 393 | 10 | 2 | **5** | Chunk gọn, Q2 đứng top-1 | Mảnh con mất tên Điều; Q5 lấy đúng Điều 22 nhưng thiếu dòng "hiệu lực", agent trả lời thiếu |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **HeadingChunker** tốt nhất (rubric 7/10, evidence 6/10), vì văn bản quy định vốn được cấu trúc theo Điều/mục, và việc gắn tiêu đề Điều vào chunk vừa làm embedding "hiểu" chunk nói về điều gì, vừa cho LLM ngữ cảnh để trả lời đúng đối tượng. Tuy vậy, khác biệt thật nằm ở **mức nội dung**: chấm theo `doc_id` thì cả ba chiến lược đều 10/10 và không phân biệt được gì. Chỉ khi kiểm tra chunk có chứa đáp án hay không thì mới lộ ra rằng chunker "đúng tài liệu nhưng sai đoạn" thua rõ (recursive chỉ 2/10 evidence). Chưa có chiến lược nào thắng mọi câu: fixed có overlap thắng ở câu liệt kê dài (Q4). Kết quả khám phá của Khang (TF-IDF: heading và fixed cùng Hit@3 100%, recursive 80%) cũng xếp hạng giống bản đối chứng: recursive đứng cuối.

**Tổng hợp theo backend** (rubric /10, không so trực tiếp được vì khác cả chiến lược lẫn model):

| Người chạy | Chiến lược | Backend | naive | evidence | rubric |
|---|---|---|---|---|---|
| Hiệp | heading | Gemini + gemini-2.5-flash | 10 | 6 | 7 |
| Khang | fixed | TF-IDF + extractive | 6 | 4 | 4 |
| Dũng | recursive | OpenAI small + gpt-4.1-mini | 6 | 2 | 3 |

Cả TF-IDF lẫn OpenAI small đều **trượt Q3 và Q4**, hai câu hỏi tiếng Việt có đáp án nằm trong tài liệu tiếng Anh. Chỉ Gemini (đa ngữ mạnh) lấy được RMIT/UNA. Ngược lại, TF-IDF **thắng Gemini ở Q5**: Điều 22 lên top-1 nhờ khớp đúng chuỗi số hiệu và ngày, trong khi Gemini để Điều 22 ở hạng 2–3.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | *(tra số liệu)* Theo quy định của UEH, tỷ lệ tương đồng từ bao nhiêu phần trăm thì sản phẩm học thuật bị xem là có dấu hiệu đạo văn? | **Từ 20% trở lên**, không tính trích dẫn, danh mục TLTK, mô tả phương pháp phổ biến, thuật ngữ, văn bản pháp luật, tên riêng. Tỷ lệ này không phải căn cứ duy nhất. | `ueh-dao-van-ai-quy-dinh-chung`, Điều 2 > *Các dấu hiệu…* > a) Dấu hiệu định lượng |
| 2 | *(điều kiện, **cần filter** `audience=student`)* Sản phẩm học thuật đã chỉnh sửa nhưng vẫn vi phạm lỗi đạo văn thì xử lý ra sao? | Với bài thuộc học phần của người học: **giảng viên phụ trách học phần lập biên bản/thông báo chuyển về đơn vị quản lý** để xử lý tùy mức độ vi phạm (Phụ lục 3). Tài liệu giảng viên có đáp án khác ("sản phẩm không được công nhận/nghiệm thu"). | `ueh-xu-ly-vi-pham-nguoi-hoc`, Điều 3 > 2.3 |
| 3 | *(quy trình/format, câu hỏi Việt với tài liệu Anh)* Khi ghi nhận việc dùng công cụ AI trong bài làm, câu acknowledgement cần nêu những thông tin gì? | Cách đã dùng công cụ AI; **tên công cụ và đơn vị tạo ra nó**; năm tạo nội dung. Mẫu: "I used [tool] (Creator, year) to …". Không còn bắt buộc số phiên bản hay ngày dùng. | `rmit-ai-acknowledgement-guide`, *Template for acknowledging the use of AI tools* |
| 4 | *(liệt kê)* Những loại thông tin nào không được phép nhập vào công cụ AI tạo sinh? | Hồ sơ sinh viên (FERPA), hồ sơ tuyển sinh, **Social Security numbers**, thẻ tín dụng, bằng lái, dữ liệu y tế/bảo hiểm, dữ liệu người tham gia nghiên cứu, tài khoản ngân hàng, ngân sách, hồ sơ nhân sự, tư vấn pháp lý, danh bạ, thông tin NDA, IP bên thứ ba, donor, hộ chiếu/visa, tài liệu có bản quyền. | `una-genai-policy-general` / `una-genai-policy-faculty`, *Information that may NOT be input…* |
| 5 | *(mốc thời gian, pháp lý)* Thông tư 49/2026/TT-BGDĐT có hiệu lực từ ngày nào và thay thế những thông tư nào? | Hiệu lực **15/08/2026**; TT 15/2018/TT-BGDĐT và TT **30/2023/TT-BGDĐT** hết hiệu lực từ ngày đó. | `tt49-2026-ung-dung-cong-nghe-ai`, Điều 22. Điều khoản thi hành |

### Tổng hợp chất lượng truy xuất của nhóm

Điểm rubric theo từng chiến lược (Heading / Fixed / Recursive), trên bản đối chứng cùng Gemini:

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Tỷ lệ tương đồng | **Heading** (1 / 0 / 0) | Heading: có (hạng 3). Fixed/Recursive: **không**, chỉ có chunk định nghĩa, không có con số | Failure case chính, xem mục 4 |
| 2 | Vẫn vi phạm sau chỉnh sửa (filter student) | Heading = Recursive (2 / 1 / 2) | Có. Fixed để chunk đáp án ở hạng 2 | Filter đổi top-1 từ tài liệu *giảng viên* sang *người học* ở cả 3 chiến lược |
| 3 | Nội dung acknowledgement | **Heading** (2 / 1 / 1) | Heading hạng 1; Fixed hạng 2; Recursive có chunk mẫu "(Creator, year)" nhưng không có câu liệt kê | Recursive trộn thêm quy định UEH vào câu trả lời |
| 4 | Thông tin cấm nhập vào AI | **Fixed** (1 / 2 / 1) | Fixed hạng 1 chứa danh sách; Heading/Recursive chỉ có câu dẫn | Overlap có lợi cho danh sách dài |
| 5 | Hiệu lực TT49 | Heading = Fixed (1 / 1 / 1) | Có: Điều 22 ở hạng 2–3; top-1 luôn là phần mở đầu thông tư | Recursive: agent thiếu ngày hiệu lực vì chunk Điều 22 bị cắt |
| | **Tổng** | | | **Heading 7 · Fixed 5 · Recursive 5** |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, ở **Q2**. Câu hỏi không nói người hỏi là ai, và corpus có hai file UEH cùng từ vựng nhưng khác đối tượng. **Không lọc** thì top-1 ở cả ba chiến lược là `ueh-xu-ly-vi-pham-giang-vien` (0.807–0.849), với đáp án sai đối tượng: "sản phẩm không được công nhận, không được nghiệm thu". **Lọc** `audience=student` thì top-1 chuyển sang `ueh-xu-ly-vi-pham-nguoi-hoc`, điểm evidence của recursive tăng 1→2, heading tăng 1→2, fixed tăng 0→1. Đánh đổi là filter cứng loại luôn tài liệu `audience=all` (quy định chung UEH), nên câu hỏi nào có đáp án nằm trong phần quy định chung sẽ mất kết quả nếu áp filter `student`. Cách an toàn hơn là lọc `audience ∈ {student, all}`. Ở lần thử đầu, câu Q2 cũ ("vi phạm sử dụng AI lần đầu…") cho top-3 **giống nhau** dù có hay không có filter, nên nhóm đã viết lại câu hỏi theo đúng hướng dẫn CP6.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Chấm theo `doc_id` thổi phồng kết quả:** cả 3 chiến lược đều 10/10 theo cách này, nhưng theo nội dung chỉ còn 6 / 5 / 2. Top-3 toàn chunk của đúng tài liệu gold vẫn có thể không chunk nào chứa đáp án (Q1: ba chunk UEH về "tỷ lệ tương đồng", "Turnitin", "định nghĩa đạo văn", không chunk nào có "20%").
> 2. **Failure case Q1:** cosine đo độ giống **chủ đề**, không đo mật độ đáp án. Chunk định nghĩa "Tỷ lệ tương đồng học thuật là…" (0.892) thắng chunk chứa "từ 20% trở lên", vì câu hỏi lặp lại gần như nguyên văn cụm "tỷ lệ tương đồng … sản phẩm học thuật". Đề xuất sửa: gộp heading con vào chunk cha (định nghĩa và ngưỡng 20% nằm cùng Điều 2), thêm hybrid BM25 cho truy vấn có con số, hoặc tăng top-k lên 5 rồi rerank.
> 3. **Metadata phải khớp chiều lọc:** filter chỉ có tác dụng vì nhóm đã tách trang UEH/UNA thành nhiều file theo `audience`. Nếu để nguyên một file `audience: all` thì filter không lọc được gì.
> 4. **Embedding không hiểu phủ định:** "được phép" và "không được phép dùng AI để kiểm tra chính tả" cho cosine 0.924. Với văn bản quy định, LLM phải đọc kỹ ngữ cảnh, không thể tin score.
> 5. **Model embedding quan trọng ngang chiến lược chunking:** cùng chiến lược recursive, Gemini lấy đúng tài liệu gold ở cả 5 câu (naive 10/10), còn OpenAI `text-embedding-3-small` (bản của Dũng) chỉ đạt naive 6/10. TF-IDF (bản của Khang) cũng chỉ 6/10. Hai câu hỏi tiếng Việt nhắm vào tài liệu tiếng Anh (Q3 RMIT, Q4 UNA) bị kéo sang quy định UEH tiếng Việt: model chọn cùng ngôn ngữ thay vì cùng nghĩa. Với corpus song ngữ cần embedding đa ngữ mạnh, hoặc dịch/chuẩn hoá câu hỏi, hoặc lọc theo `language`/`issuer`.
> 5b. **Lexical và semantic bù nhau, nên dùng hybrid:** TF-IDF của Khang đưa Điều 22 lên top-1 ở Q5 (khớp chính xác "49/2026/TT-BGDĐT", "hiệu lực") trong khi Gemini để nó ở hạng 2–3. Ngược lại, Gemini thắng hẳn ở câu hỏi khác ngôn ngữ. Đây là bằng chứng thực nghiệm cho đề xuất hybrid BM25 + embedding ở failure case Q1.
> 6. **Agent vẫn có thể sai khi ngữ cảnh thiếu:** ở Q5 bản của Dũng, chunk top-1 có khoản "thay thế" nhưng thiếu khoản "hiệu lực 15/08/2026", và `gpt-4.1-mini` lấy nhầm ngày ký 30/06/2026 ở chunk mở đầu làm ngày hiệu lực. Lỗi grounding kiểu này không bắt được nếu chỉ chấm retrieval.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng tài liệu, cùng query, nhưng mỗi chiến lược hỏng ở một chỗ khác nhau. Heading giữ ngữ cảnh tốt nhất nhưng tách câu dẫn khỏi danh sách (Q4). Fixed có overlap cứu được danh sách dài nhưng cắt ngang câu (Q1). Recursive cho chunk gọn nhưng mảnh con mất tên Điều nên khó khớp câu hỏi về "hiệu lực" (Q5). Không chiến lược nào thắng mọi câu, và hướng kết hợp tự nhiên là heading + overlap. Một bài học khác đến từ việc mỗi người tự chạy trên backend khác nhau: nếu không cố định embedding và LLM thì không thể biết chênh lệch đến từ chunker hay từ model, nên phải có bản đối chứng cùng backend.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> (1) Loại bỏ nội dung trùng lặp: phần "Data Privacy and Security" của UNA bị lặp nguyên văn trong file `general` và `faculty`, nên hai chunk giống hệt nhau (cùng score 0.788/0.832) chiếm hai slot top-3. Nên chỉ giữ ở `general` (audience=all). (2) Làm sạch file RMIT VN (còn phần menu "What is academic integrity?" bị lặp). (3) Thêm trường `section`/`article` (ví dụ `Điều 22`) vào metadata của từng chunk để có thể lọc hoặc boost theo Điều khi câu hỏi nêu rõ.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **34 / 40** |
