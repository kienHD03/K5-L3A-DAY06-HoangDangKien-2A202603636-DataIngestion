# Báo cáo cá nhân — Day 6

## Dữ liệu và pipeline
- Chủ đề, nguồn/quyền, số trang và quy tắc tính trang: Dữ liệu xoay quanh chủ đề Đạo đức Kinh doanh (Business Ethics). Nguồn văn bản được trích xuất từ tài liệu Business Ethics.pdf. Tổng cộng có 31 trang văn bản được nạp vào hệ thống.
- Chuẩn hóa, lỗi và giới hạn: Quá trình chuẩn hóa văn bản gặp giới hạn ở việc cắt xén ngẫu nhiên giữa câu đối với chiến lược kích thước cố định. Lỗi xung đột API Key (GOOGLE_API_KEY vs GEMINI_API_KEY) và lỗi xung đột cổng Docker (55433) đã được xử lý triệt để. Bảng database đã được xóa (DROP TABLE) để đồng bộ hóa số chiều vector.
- Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí:
  - Model: text-embedding-3-small.
  - Số chiều: 1536.
  - Vector store: PostgreSQL cài đặt extension pgvector chạy trên Docker.
  - Metric: Cosine Distance (<=>).
  - Lệnh chạy: python -m src.run.
  - Chi phí: Khoảng $0.02 / 1 triệu tokens.
- Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn: Metadata bắt buộc bao gồm document_id, source (tên file gốc), và page (trang xuất hiện). Các trường này được đóng gói thủ công vào dictionary và lưu dưới định dạng JSONB trong PostgreSQL để phục vụ quá trình truy vết (traceability) và lọc kết quả (metadata filtering) ở chiến lược C.

## Cấu hình và benchmark
- A / B / C (tham số cụ thể, khác biệt duy nhất B–C):
  - Chiến lược A: Chia văn bản theo kích thước cố định (Fixed-size chunking), tạo ra 265 chunks. Các ID có định dạng như A_doc_1_p15_f0_121.
  - Chiến lược B: Chia văn bản theo cụm đoạn văn (Paragraph-based chunking), tạo ra 239 chunks. Các ID có định dạng như B_doc_1_p15_para0_109.
  - Chiến lược C: Chia theo đoạn văn giống B (tạo 239 chunks), nhưng áp dụng thêm bộ lọc siêu dữ liệu (Metadata Filtering) vào câu truy vấn. Khác biệt duy nhất giữa B và C là C có sử dụng filter lúc tìm kiếm.
- ≥20 câu: phân chia ≥15 dev / ≥5 test, câu metadata filter và cách kiểm chứng evidence: Benchmark sử dụng tổng cộng 20 câu hỏi, chia thành 15 câu tập dev (q01-q15) và 5 câu tập test (q16-q20). Việc kiểm chứng evidence (bằng chứng) được thực hiện thủ công bằng cách đối chiếu top 3 chunks trả về trong file trace xem có chứa nội dung trả lời cho câu hỏi hay không.
- Tiêu chí chọn chiến lược đã chốt trước khi xem test: Ưu tiên chiến lược duy trì được sự nguyên vẹn của ngữ nghĩa (semantic coherence). Chiến lược chia theo đoạn văn (B) được kỳ vọng sẽ vượt trội hơn cắt cố định (A) vì không làm đứt gãy câu chữ giữa chừng.

## Kết quả
| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---|---|---|---|---|
|A|Dev|0/15|12/15|265|~3s|~$0.001|
|A|Test|0/5|4/5|265|~1s|~$0.0005|
|B|Dev|0/15|14/15|239|~2.5s|~$0.001|
|B|Test|0/5|5/5|239|~1s|~$0.0005|
|C|Dev|0/15|11/15|239|~2.5s|~$0.001|
|C|Test|0/5|2/5|239|~1s|~$0.0005|

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
|A|1.1/2 (10 mẫu)|20/20|N/A|[0: 2, 1: 2, 2: 1] - TB: 0.8/2|
|B|1.9/2 (10 mẫu)|20/20|N/A|[0: 0, 1: 1, 2: 4] - TB: 1.8/2|
|C|1.9/2 (10 mẫu)|20/20|16/20|[0: 3, 1: 1, 2: 1] - TB: 0.6/2|



Đường dẫn trace, nhãn thủ công và cách chọn mẫu:

## Phân tích và kết luận
- So sánh A–B và B–C; 2 ví dụ sai có ID câu và nguồn:
  - A so với B: Chiến lược B (Paragraph) bảo toàn ngữ nghĩa tốt hơn hẳn A (Fixed-size). Chiến lược A thường xuyên cắt ngang câu, làm mất đi ngữ cảnh quan trọng khiến LLM khó tổng hợp câu trả lời, trong khi B giữ trọn vẹn các đoạn văn logic.
  - B so với C: Mặc dù C có cùng cách cắt chunk như B, nhưng việc áp dụng filter metadata khắt khe khiến C bị "trượt" rất nhiều kết quả.
  - Ví dụ sai 1: Câu q16 ở tập test của chiến lược C trả về mảng hits trống []. Do filter loại bỏ toàn bộ dữ liệu hợp lệ.
  - Ví dụ sai 2: Câu q03 ở tập dev của chiến lược C cũng trả về [], không tìm thấy bất kỳ chunk nào khớp với bộ lọc siêu dữ liệu yêu cầu.
- Chiến lược chọn, đánh đổi, điều kiện áp dụng: Chiến lược B (Paragraph-based không có hard filter) là sự lựa chọn tối ưu nhất cho tập tài liệu này. Đánh đổi ở đây là B có thể mang lại một vài chunk nhiễu, nhưng đảm bảo không bị sót thông tin (Recall cao). Áp dụng chiến lược B cho các hệ thống RAG xử lý tài liệu học thuật, sách giáo khoa nơi các đoạn văn (\n\n) vốn đã được tác giả cấu trúc theo ý nghĩa.
- Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí: Tập test 5 câu là quá nhỏ để phản ánh chính xác độ ổn định của mô hình. Việc hàm đánh giá Hit@1/Hit@3 tự động không hoạt động (đều ra 0.0) buộc phải chấm thủ công, gây tốn thời gian. Thời gian và chi phí đo lường chỉ ở mức ước tính tương đối cho một tài liệu nhỏ (31 trang).
- Nếu làm lại hoặc mở rộng, cải tiến gì?
  1. Nâng cấp hàm search bằng SQL thô kết hợp <=> để tận dụng triệt để pgvector thay vì phụ thuộc code cũ.
  2. Áp dụng Semantic Chunking hoặc bổ sung Overlap hợp lý hơn thay vì chỉ bám vào Fixed-size hoặc Paragraph thuần túy.
  3. Sử dụng LLM-as-a-Judge để tự động chấm điểm Grounding và Coherence thay vì chấm tay thủ công.
