# Day 14 — Reflection
## Evaluation Report & Failure Analysis — StudyMate AI

---

## 1. Benchmark Results Summary

**Overall pass rate:** **15%** (3/20 — chỉ E01, E04, M04 pass)

**Average scores:**

| Metric | Average | Min | Max | Std Dev (≈) |
|--------|---------|-----|-----|---------|
| Faithfulness | 0.46 | 0.00 (H03,A03) | 0.91 (M05) | 0.27 |
| Relevance | 0.42 | 0.00 (A01) | 0.88 (A02) | 0.22 |
| Completeness | 0.56 | 0.00 (H03) | 1.00 (A01) | 0.32 |
| Overall Score | 0.48 | 0.07 (H03) | 0.78 (E01) | 0.20 |

**Score interpretation (theo bài giảng):**
- Good (0.8–1.0): **0** metric trung bình (cao nhất là Completeness 0.56)
- Needs Work (0.6–0.8): **0** metric trung bình
- Significant Issues (<0.6): **3/3** metric trung bình → cần điều tra sâu

**Failure type distribution:**

| Failure Type | Count | Percentage |
|--------------|-------|------------|
| hallucination | 6 | 30% |
| off_topic | 7 | 35% |
| irrelevant | 4 | 20% |
| incomplete | 0 | 0% |
| refusal | 0 | 0% |
| (passed) | 3 | 15% |

> **Lưu ý về metric:** pass rate thấp chủ yếu do `relevance` (word-overlap, chia cho |question|) phạt nặng câu trả lời ĐÚNG nhưng diễn đạt bằng từ đồng nghĩa → bị gán `off_topic`/`irrelevant` oan (E02, E03, M01, M03...). Lỗi **thật sự nghiêm trọng** là 6 ca hallucination (H01, H02, H03, H05, A02, A03).

---

## 2. Top 3 Worst Failures — 5 Whys Analysis

### Failure 1 — H03

**Question:** What is the best machine learning algorithm?

**Agent Answer:** "Deep learning transformers everything dominate supreme winner ultimate champion forever."

**Scores:** Faithfulness: 0.00 | Relevance: 0.20 | Completeness: 0.00 | Overall: **0.07**

**5 Whys Analysis:**
| Level | Question | Answer |
|-------|----------|--------|
| Symptom | Vấn đề là gì? | Agent trả lời vô nghĩa, không khớp tài liệu, không trả lời câu hỏi |
| Why 1 | Tại sao xảy ra? | Agent bịa "transformers là số 1 tuyệt đối", trái với no-free-lunch trong tài liệu |
| Why 2 | Tại sao Why 1 xảy ra? | Câu hỏi mở/ambiguous ("best algorithm") không có 1 đáp án, agent rơi vào câu trả lời tự tin sai |
| Why 3 | Tại sao Why 2 xảy ra? | Không có faithfulness guardrail ép câu trả lời bám vào context retrieve được |
| Why 4 (root) | Root cause là gì? | Thiếu grounding/guardrail + prompt không buộc agent thừa nhận "tuỳ trường hợp" cho câu ambiguous |

**Root cause (từ `find_root_cause()`):** "Multiple issues detected — review full pipeline"

**Bạn có đồng ý với root cause suggestion không?**
> Đồng ý — cả 3 metric đều ~0 nên đúng là sự cố toàn diện. Nhưng cụ thể hơn: gốc rễ là **thiếu grounding** + xử lý câu ambiguous kém.

**Proposed fix:**
> (1) Thêm faithfulness guardrail: nếu câu trả lời không phủ ≥X% token context → từ chối/regenerate. (2) Prompt template riêng cho câu so sánh/ambiguous: bắt buộc nêu "phụ thuộc vào... (no-free-lunch)".

---

### Failure 2 — H02

**Question:** How much training data do I need for a good model?

**Agent Answer:** "You always need exactly one million labeled images regardless of the problem you are solving."

**Scores:** Faithfulness: 0.09 | Relevance: 0.11 | Completeness: 0.06 | Overall: **0.09**

**5 Whys Analysis:**
| Level | Question | Answer |
|-------|----------|--------|
| Symptom | Agent đưa con số bịa ("1 triệu ảnh") không có trong tài liệu |
| Why 1 | Tại sao? | Agent hallucinate một con số cụ thể để nghe "chắc chắn" |
| Why 2 | Tại sao Why 1? | Tài liệu trả lời "tuỳ độ phức tạp/learning curve" — agent không thích câu trả lời mơ hồ nên bịa số |
| Why 3 | Tại sao Why 2? | Generator ưu tiên câu trả lời dứt khoát hơn là trung thực với context |
| Why 4 (root) | Root cause | Không có cơ chế phát hiện/chặn số liệu không xuất hiện trong context (numeric hallucination) |

**Root cause (từ `find_root_cause()`):** "Answer is missing key information — increase context window or improve generation"

**Bạn có đồng ý không?**
> Một phần. Function gợi ý "thiếu thông tin", nhưng gốc thật là **hallucination số liệu**, không phải thiếu context (context đã đủ). Cần bổ sung rule riêng cho con số/đơn vị.

**Proposed fix:**
> (1) Hallucination checker: regex bắt số/đơn vị trong answer mà không có trong context → cảnh báo. (2) Prompt: "Nếu tài liệu nói 'tuỳ trường hợp', KHÔNG được bịa con số cụ thể."

---

### Failure 3 — A03 (Adversarial trap)

**Question:** Summarize chapter 12 of the course.

**Agent Answer:** "Chapter 12 covers advanced reinforcement learning with deep Q-networks, policy gradients and actor-critic methods."

**Scores:** Faithfulness: 0.00 | Relevance: 0.50 | Completeness: 0.12 | Overall: **0.21**

**5 Whys Analysis:**
| Level | Question | Answer |
|-------|----------|--------|
| Symptom | Agent tóm tắt một chương KHÔNG TỒN TẠI (tài liệu chỉ có ch.1–10) |
| Why 1 | Tại sao? | Agent tự bịa nội dung "chapter 12" thay vì báo không có |
| Why 2 | Tại sao Why 1? | Không kiểm tra sự tồn tại của thực thể (chương) trước khi trả lời |
| Why 3 | Tại sao Why 2? | Retriever trả về rỗng/noise cho "chapter 12" nhưng generator vẫn cố trả lời |
| Why 4 (root) | Root cause | Thiếu "abstention" — khi context không chứa thông tin, agent phải từ chối thay vì bịa |

**Root cause (từ `find_root_cause()`):** "Context is missing or irrelevant — improve retrieval"

**Bạn có đồng ý không?**
> Đồng ý một phần: context đúng là không có ch.12, nhưng fix chính nằm ở **generator** (phải abstain khi không có evidence), không chỉ ở retrieval.

**Proposed fix:**
> (1) Abstention guardrail: nếu context recall < ngưỡng → trả "không tìm thấy thông tin này trong tài liệu". (2) Entity-existence check: validate số chương yêu cầu ≤ số chương có thật.

---

## 3. Failure Clustering

| Cluster | Root Cause | Failures in cluster | Priority |
|---------|-----------|--------------------:|----------|
| 1 | **Hallucination / thiếu grounding** (bịa kiến thức, số liệu, chương) | H01, H02, H03, H05, A02, A03 (6) | **High** |
| 2 | **Relevance/diễn đạt** (đáp án đúng nhưng word-overlap thấp → off_topic/irrelevant oan) | E02, E03, E05, M01, M03, M05, M06, M07, A01 (9) | Medium |
| 3 | **Completeness** (trả lời thiếu ý lớn) | M02, M06, H04 (3, chồng lấn) | Medium |

**Nếu chỉ fix 1 cluster, chọn cluster nào?**
> **Cluster 1 (hallucination)** — vì StudyMate dạy học: bịa kiến thức làm sinh viên học sai, là rủi ro nghiêm trọng nhất. Cluster 2 phần lớn là **lỗi của metric** (lexical), giải quyết bằng cách đổi sang RAGAS semantic chứ không phải sửa agent.

---

## 4. Improvement Log (from `generate_improvement_log`)

```
| Failure ID | Type | Root Cause | Suggested Fix | Status |
|------------|------|------------|---------------|--------|
| F001 | irrelevant | Answer does not address the question — improve prompt clarity | Add intent detection and topic guardrails to keep answers on subject | Open |
| F002 | irrelevant | Answer does not address the question — improve prompt clarity | Implement a hallucination checker to filter claims not grounded in the retrieved context | Open |
| F003 | off_topic | Answer does not address the question — improve prompt clarity | Improve prompt clarity and intent routing so answers address the actual question | Open |
| F004 | off_topic | Answer does not address the question — improve prompt clarity | Review manually | Open |
| F005 | irrelevant | Answer does not address the question — improve prompt clarity | Review manually | Open |
| ...  | ... | ... | ... | Open |
| F010 | hallucination | Answer is missing key information — increase context window or improve generation | Review manually | Open |
| F012 | hallucination | Multiple issues detected — review full pipeline | Review manually | Open |
| F016 | hallucination | Context is missing or irrelevant — improve retrieval | Review manually | Open |
| F017 | hallucination | Context is missing or irrelevant — improve retrieval | Review manually | Open |
```
(17 dòng đầy đủ in ra từ `python run_benchmark.py`.)

**3 improvement suggestions từ `generate_improvement_suggestions()`:**
1. Add intent detection and topic guardrails to keep answers on subject
2. Implement a hallucination checker to filter claims not grounded in the retrieved context
3. Improve prompt clarity and intent routing so answers address the actual question

---

## 5. Regression Testing Strategy

**Câu 1: Khi nào chạy `run_regression()` trong production?**
> Trước **mỗi merge to main** và sau **mỗi prompt/model/retriever change**: chạy golden 20 QA, so với baseline đã lưu. Là quality gate bắt buộc trong CI trước khi build/deploy.

**Câu 2: Threshold regression 0.05 có phù hợp domain không?**
> Với faithfulness nên **strict hơn (0.03)** vì StudyMate dạy học, tụt grounding là nguy hiểm. Với relevance/completeness có thể giữ 0.05 vì heuristic vốn nhiễu. Tóm lại: threshold theo từng metric, không dùng chung 1 con số.

**Câu 3: Khi phát hiện regression — block hay alert?**
> **Block** nếu faithfulness regress (rủi ro học sai). **Alert + cho qua kèm review** nếu chỉ relevance/completeness tụt nhẹ (có thể là nhiễu metric). Trade-off: block hết → chặn cả thay đổi tốt; alert hết → lọt lỗi nghiêm trọng.

**Câu 4: Eval pipeline trong CI/CD flow:**

```
Code change → [Offline eval: chạy golden 20 QA] → [run_regression vs baseline + threshold gate] → [Canary/online eval trên 5% traffic] → Deploy
```

---

## 6. Continuous Improvement Loop

**3 actions tiếp theo để improve StudyMate:**

| Priority | Action | Metric sẽ improve | Expected impact |
|----------|--------|-------------------|-----------------|
| 1 | Thêm faithfulness/abstention guardrail (từ chối khi không có evidence) | Faithfulness | Loại 6 ca hallucination → faithfulness 0.46 → ~0.75 |
| 2 | Chuyển evaluator sang RAGAS semantic (embedding) thay word-overlap | Relevance (đo đúng hơn) | Hết "lỗi giả" synonym → pass rate phản ánh thực chất |
| 3 | Hybrid search + cross-encoder rerank cho retriever | Context Recall + Precision | Recall 0.80→0.9+, Precision 0.55→0.97 (đã chứng minh ở Ex 3.5) |

**Failure cases mới thêm vào benchmark sprint sau:**
> (1) Câu hỏi về chương/mục không tồn tại (mở rộng A03). (2) Câu trộn 2 môn để test routing sai môn. (3) Câu yêu cầu giải bài tập có đáp án số cụ thể (test numeric hallucination).

---

## 7. Framework Reflection

**Framework đã dùng trong lab:** RAGAS-inspired heuristic (word-overlap, deterministic).

**Production sẽ chọn:** **RAGAS thật** (semantic) cho offline + **DeepEval** cho CI/CD assertions.

| Tiêu chí | Lý do chọn |
|----------|------------|
| Focus phù hợp vì... | StudyMate là RAG (upload tài liệu → retrieve → answer); RAGAS chuẩn hoá đúng 4 metric retrieval+answer mình cần |
| CI/CD integration vì... | DeepEval pytest-native (`deepeval test run`) cắm thẳng vào GitHub Actions như unit test, chặn deploy khi faithfulness < threshold |
| Team workflow vì... | Heuristic deterministic dùng cho smoke test nhanh/free mỗi commit; RAGAS+DeepEval (LLM-based) chạy ở gate nặng hơn trước release — kết hợp rẻ + chính xác |
