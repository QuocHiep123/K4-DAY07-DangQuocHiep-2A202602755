# Kết quả benchmark do từng thành viên tự chạy

Mỗi thành viên chạy 5 benchmark query chung của nhóm DKH trên máy riêng, bằng backend mình có. Các file dưới đây là output gốc thành viên gửi lại. Nhóm dùng chúng cho mục "Kết quả mỗi thành viên tự chạy" trong `report/REPORT_NHOM.md`.

| File | Thành viên | Chiến lược | Embedding | Agent |
|---|---|---|---|---|
| `../ket_qua_benchmark.txt` | Đặng Quốc Hiệp (2A202602755) | heading (+ bản đối chứng cả 3 chiến lược) | `gemini-embedding-001` | `gemini-2.5-flash` |
| `khang_fixed_tfidf.txt` | Nguyễn Thế Khang (2A202602964) | fixed_size (500, overlap 100) | TF-IDF word unigram L2 (offline) | extractive, không LLM |
| `dung_recursive_openai.txt` | Nguyễn Việt Dũng (2A202602812) | recursive (500) | OpenAI `text-embedding-3-small` | `gpt-4.1-mini` |

Vì ba backend khác nhau, điểm giữa các file **không so trực tiếp được**. Kết luận về chiến lược chunking dựa trên bản đối chứng cùng Gemini trong `../ket_qua_benchmark.txt`.
