# Hướng dẫn cho Codex — Lab 07 nhóm DKH (thành viên Khang / Dũng)

> **Cách dùng:** Thành viên copy file này vào gốc repo của mình, **đổi tên thành `AGENTS.md`** (Codex tự đọc file này), rồi bảo Codex: *"Làm theo AGENTS.md, tôi là <tên>"*.
> Codex: đọc hết file này trước khi làm. Mọi con số trong báo cáo phải lấy từ lệnh đã **chạy thật**, không được bịa hay ước lượng.

---

## 0. Thông tin đề tài (cố định, không đổi)

| Mục | Giá trị |
|---|---|
| Lab | K4-L3A — Lab 07: Nền tảng dữ liệu, Embedding & Vector Store |
| Nhóm | **DKH** |
| Tên đề tài / chủ đề | **Quy định sử dụng AI và liêm chính học thuật trong giáo dục đại học** (đạo văn, khai báo AI, xử lý vi phạm, bảo mật dữ liệu khi dùng AI) |
| Corpus | `data/ai-liem-chinh-hoc-thuat/`: 10 file `.md` + `sources.csv` (Thông tư 49/2026/TT-BGDĐT; UEH QĐ 4002; RMIT; University of North Alabama) |
| Embedding | `gemini-embedding-001` (qua `.env`, `EMBEDDING_PROVIDER=gemini`) |
| LLM cho agent | `gemini-2.5-flash` |
| Script đo | `bench.py` (dùng chung cả nhóm) |

### Thành viên và chiến lược (mỗi người MỘT chiến lược, không trùng)

| Thành viên | MSSV | Vai | Chiến lược | Giá trị `STRATEGY` trong `bench.py` |
|---|---|---|---|---|
| Đặng Quốc Hiệp | 2A202602755 | R3 · Strategy | `HeadingChunker(max_chars=800)`, theo Điều/mục | `"heading"` (đã xong) |
| **Nguyễn Thế Khang** | 2A202602964 | R1 · Data | `FixedSizeChunker(chunk_size=500, overlap=100)` | `"fixed"` |
| **Nguyễn Việt Dũng** | 2A202602812 | R2 · Benchmark | `RecursiveChunker(chunk_size=500)` | `"recursive"` |

---

## 1. Quy tắc bắt buộc (Codex phải tuân thủ)

1. **Code `src/` là bài cá nhân:** phải tự hoàn thiện các TODO trong `src/chunking.py`, `src/store.py`, `src/agent.py` của repo **mình**. KHÔNG copy `src/` của Hiệp.
2. **Dùng chung (không sửa):** `data/ai-liem-chinh-hoc-thuat/`, `data/urls.csv`, `bench.py`. Chỉ được đổi **một dòng** `STRATEGY = ...` trong `bench.py`.
3. **Không sửa 5 benchmark query** hay `evidence` trong `bench.py`, vì cả nhóm phải chạy cùng bộ câu hỏi.
4. Giữ nguyên mọi dòng `def ...` trong `src/` (test kiểm tra theo chữ ký hàm). Không sửa `tests/`.
5. **Không commit** `.env`, `.venv/`, `.cache/`. Không in API key ra log hay báo cáo.
6. Không bịa số liệu. Nếu lệnh lỗi thì ghi rõ lỗi vào báo cáo và báo lại cho người dùng.

---

## 2. Chuẩn bị repo

```bash
# 1. Fork repo gốc https://github.com/VinUni-AI20k/K4-L3A-Data-Foundations về tài khoản của mình,
#    đổi tên fork thành K4-DAY07-<HoVaTenKhongDau>-<MSSV>
#    (ví dụ: K4-DAY07-NguyenTheKhang-2A202602964, K4-DAY07-NguyenVietDung-2A202602812), rồi clone về.

# 2. Môi trường (Python 3.11)
py -3.11 -m venv .venv            # macOS/Linux: python3.11 -m venv .venv
.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install google-genai

# 3. Lấy phần dùng chung của nhóm từ repo của Hiệp (chỉ 3 thứ này, KHÔNG lấy src/):
#    data/ai-liem-chinh-hoc-thuat/   data/urls.csv   bench.py
#    Có thể copy tay, hoặc:
git remote add hiep https://github.com/QuocHiep123/K4-DAY07-DangQuocHiep-2A202602755.git
git fetch hiep
git checkout hiep/main -- data/ai-liem-chinh-hoc-thuat data/urls.csv bench.py

# 4. Tạo .env (KHÔNG commit), key Gemini lấy miễn phí tại https://aistudio.google.com/apikey
#    GEMINI_API_KEY=...
#    EMBEDDING_PROVIDER=gemini
#    GEMINI_EMBEDDING_MODEL=gemini-embedding-001

# 5. Thêm vào .gitignore
#    .cache/
```

Kiểm tra: `pytest tests/ -v` phải ra **31 failed, 11 passed** (baseline trước khi code).

---

## 3. Phần cá nhân: hoàn thiện `src/`

Làm theo `day7-lab-data-foundations.md` mục 4–5. Những điểm dễ sai:

- `SentenceChunker`: tách câu **sau** dấu `.`/`!`/`?` mà vẫn giữ dấu (dùng regex lookbehind). Text rỗng thì trả `[]`.
- `RecursiveChunker._split`: có hai chiều. Đệ quy xuống với các separator nhỏ hơn, **và** gom các mảnh nhỏ liền kề lại tới sát `chunk_size`. Phải xử lý `separators=[]` bằng cách cắt cứng theo `chunk_size`.
- `compute_similarity`: vector có norm = 0 thì trả `0.0`.
- `ChunkingStrategyComparator.compare`: key đúng tên `fixed_size`, `by_sentences`, `recursive`; mỗi key có `count`, `avg_length`, `chunks`. Chặn chia cho 0.
- `EmbeddingStore`: chỉ dùng in-memory, **bỏ nhánh Chroma** (đặt `_use_chroma = False`). `_make_record` copy metadata và `setdefault("doc_id", doc.id)`. `search` và `search_with_filter` phải đi chung qua `_search_records`. Filter phải chạy **trước** khi search.
- `KnowledgeBaseAgent.answer(question, top_k=3, metadata_filter=None)`: đánh số ngữ cảnh `[1] [2] [3]` kèm `doc_id`, yêu cầu model chỉ dùng ngữ cảnh và nói "không tìm thấy" khi thiếu. Store rỗng thì không gọi LLM. **Phải nhận tham số `metadata_filter`** vì `bench.py` truyền vào.

Xong phần này thì chạy:

```bash
pytest tests/ -v                  # phải 42 passed
python main.py "Chunking là gì?"  # chạy trọn vẹn
```

---

## 4. Chạy benchmark với chiến lược của mình

1. Mở `bench.py`, sửa **đúng một dòng**:
   - Khang: `STRATEGY = "fixed"`
   - Dũng: `STRATEGY = "recursive"`
2. Chạy:
   ```bash
   python bench.py
   ```
   Lệnh này tự ghi `ket_qua_benchmark.txt`. Free tier Gemini giới hạn 100 embedding/phút; script tự chờ 65 giây khi gặp 429, cứ để nó chạy.
3. Đọc `ket_qua_benchmark.txt`. Với mỗi query ghi lại: top-3 (`id`, `score`), `naive`, `content(evidence)`, `evidence_rank`, và câu trả lời của agent.
4. **A/B metadata filter (bắt buộc):** cuối file có mục `A/B METADATA FILTER` cho Q2. Ghi lại top-3 khi **không** filter và khi **có** filter `{"audience": "student"}`.

### 5 benchmark query của nhóm (để đối chiếu, KHÔNG sửa)

| # | Query | Gold answer (tóm tắt) | Tài liệu gold |
|---|---|---|---|
| Q1 | Theo quy định của UEH, tỷ lệ tương đồng từ bao nhiêu % thì sản phẩm học thuật bị xem là có dấu hiệu đạo văn? | Từ **20% trở lên** (không tính trích dẫn, TLTK, …) | `ueh-dao-van-ai-quy-dinh-chung` |
| Q2 | Sản phẩm học thuật đã chỉnh sửa nhưng vẫn vi phạm lỗi đạo văn thì xử lý ra sao? *(filter `audience=student`)* | Giảng viên phụ trách học phần **lập biên bản** chuyển đơn vị quản lý | `ueh-xu-ly-vi-pham-nguoi-hoc` |
| Q3 | Câu acknowledgement khi dùng công cụ AI cần nêu những thông tin gì? | Cách dùng; **tên công cụ + creator**; năm | `rmit-ai-acknowledgement-guide` |
| Q4 | Những loại thông tin nào không được phép nhập vào công cụ AI tạo sinh? | FERPA records, **Social Security numbers**, thẻ, y tế, … | `una-genai-policy-general` / `-faculty` |
| Q5 | Thông tư 49/2026/TT-BGDĐT có hiệu lực từ ngày nào, thay thế thông tư nào? | **15/08/2026**; thay TT 15/2018 và TT 30/2023 | `tt49-2026-ung-dung-cong-nghe-ai` |

### Cách chấm theo rubric (`docs/SCORING.md`), mỗi câu 2 điểm

- **2:** chunk chứa đáp án ở **top-1** **và** agent trả lời đúng
- **1:** chunk chứa đáp án ở top-2/3, **hoặc** có chunk liên quan nhưng agent trả lời thiếu
- **0:** không chunk nào trong top-3 chứa đáp án (agent phải nói "không tìm thấy")

Codex tự chấm từng câu bằng cách đối chiếu câu trả lời của agent với gold answer, và ghi lý do cho từng điểm.

---

## 5. Viết `report/REPORT_CANHAN.md` (của riêng mình)

Điền theo template có sẵn. Mọi số liệu phải lấy từ lệnh đã chạy:

| Mục | Nội dung | Lấy từ đâu |
|---|---|---|
| Header | Họ tên, MSSV, Nhóm **DKH**, vai, ngày | Bảng ở mục 0 |
| 1. Warm-up | Giải thích cosine; một cặp câu CAO (khác từ, cùng nghĩa) và một cặp THẤP; lý do cosine hợp hơn Euclid. Bài toán 10.000 ký tự / 500 / 50 → 23 chunk, overlap 100 → 25 | Kiểm lại bằng `FixedSizeChunker` |
| 2. Hướng tiếp cận | 2–3 câu cho mỗi phần: SentenceChunker, RecursiveChunker, store, filter/delete, agent. Nêu edge case chưa xử lý (viết tắt `TS.`, số thập phân, heading không có dấu chấm) | Code của chính mình |
| 3. Test | Dán **nguyên văn** output `pytest tests/ -v`, số test pass /42 | Chạy thật |
| 4. Dự đoán similarity | **5 cặp câu của riêng mình** (không dùng lại 5 cặp của Hiệp), liên quan chủ đề AI/liêm chính. Ghi dự đoán trước, rồi tính bằng Gemini embedding + `compute_similarity`. Nên có một cặp phủ định ("được"/"không được") và một cặp Việt–Anh | Script nhỏ, chạy thật |
| 5. Kết quả truy xuất | Bảng 5 query: top-1 chunk (tóm tắt), score, có liên quan không, câu trả lời agent. Ghi "…/5 có chunk liên quan trong top-3" và điểm rubric /10 | `ket_qua_benchmark.txt` |
| Tự đánh giá | Điểm /60 | Trung thực |

Script tính similarity gợi ý (chạy từ gốc repo):

```python
from dotenv import load_dotenv; load_dotenv(".env")
import bench
from src import compute_similarity
emb = bench.make_embedder()
pairs = [("câu A", "câu B"), ...]          # 5 cặp của riêng bạn
emb.prefetch([t for p in pairs for t in p])
for a, b in pairs:
    print(f"{compute_similarity(emb(a), emb(b)):.3f} | {a} || {b}")
```

---

## 6. Gửi kết quả cho Hiệp (để ghép vào `REPORT_NHOM.md`)

Codex in ra khối dưới đây, **điền bằng số thật**, để thành viên copy gửi cho Hiệp:

```text
Thành viên: <Họ tên> — <MSSV> — Chiến lược: <fixed | recursive>
chunks=<...>  avg_len=<...>
Điểm: naive=<.../10>  evidence=<.../10>  rubric=<.../10>

Q1: top-1=<id> (score=<...>) | evidence_rank=<...> | rubric=<0/1/2> | agent: <tóm tắt 1 dòng>
Q2: ...
Q3: ...
Q4: ...
Q5: ...

A/B Q2 — không filter top-1: <id> (audience=<...>) | có filter top-1: <id> | evidence: <x>/2 → <y>/2
Điểm mạnh (1 câu): ...
Điểm yếu (1 câu): ...
Failure case (câu nào, vì sao, đề xuất sửa): ...
```

---

## 7. Nộp bài (checklist CP7)

- [ ] `pytest tests/ -v` → **42 passed**, không còn `raise NotImplementedError` trong `src/`
- [ ] Có `data/ai-liem-chinh-hoc-thuat/` (10 file + `sources.csv`), `bench.py` (đã đổi `STRATEGY`), `ket_qua_benchmark.txt`
- [ ] `report/REPORT_CANHAN.md` đã điền đủ; `report/REPORT_NHOM.md` lấy bản chung của nhóm từ repo Hiệp khi Hiệp chốt xong
- [ ] `git status` không thấy `.env`, `.venv/`, `.cache/`
- [ ] Commit và push lên repo `K4-DAY07-<HoVaTen>-<MSSV>`, rồi nộp link lên vlearn

```bash
git add src/ data/ai-liem-chinh-hoc-thuat data/urls.csv bench.py ket_qua_benchmark.txt report/ .gitignore
git commit -m "Nộp bài Lab 07"
git push origin main
```
