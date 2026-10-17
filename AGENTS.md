# Engineering Discipline & Standards (Matt Pocock Skills)

This repository adheres to disciplined, production-grade software engineering principles inspired by Matt Pocock's skills (`mattpocock/skills`). All AI coding sessions in this project must abide by the following rules.

---

## 1. Anti-Bloat & Clean Code Principles

1. **No "Vibe Coding"**:
   - Do not make speculative edits, write temporary monkey-patches, or write code without understanding root causes.
   - Never add defensive wrapper functions, redundant `useEffect` hooks, or extra component state just to patch a symptom. Fix the root cause or eliminate the broken logic.

2. **The Deletion Test & Simplicity**:
   - Always prefer **deleting and consolidating** code over adding new layers.
   - If a function or hook already exists, reuse it. Do not reimplement similar logic under a new name.
   - Every file should aim to be under **250 lines of code**. Large files (e.g., `App.tsx`) must be sliced into cohesive, single-responsibility modules.

3. **Deep Modules (John Ousterhout)**:
   - A good module has a **small, clean interface** with a **deep implementation**.
   - Avoid shallow pass-through components or excessive wrapper abstractions that add indirection without value.

---

## 2. Core Workflows (Matt Pocock Skills)

### A. Diagnosing & Fixing Bugs (`diagnosing-bugs`)
- **Phase 1: Build a tight feedback loop**: Before editing code or hypothesizing, identify or create a fast, deterministic automated test (Playwright, unit test, or script) that reproduces the exact bug and goes **RED**.
- **Phase 2: Reproduce & Minimise**: Isolate the smallest reproduction case.
- **Phase 3: Fix at the root**: Eliminate the flaw with the cleanest, minimal diff.
- **Phase 4: Verify Green**: Run the test to confirm it turns **GREEN** without regressions.

### B. Development & Refactoring (`tdd` & `implement`)
- **Red-Green-Refactor**: Write or update tests at public seams first, implement only enough code to pass the test, then clean up.
- **Vertical Slices**: Deliver changes one small, testable tracer bullet at a time.
- **Code Review Check**: Review diffs against Fowler code smells (duplicate code, large classes, long parameter lists, feature envy).

---

## 3. Verification & Quality Gates

- Before finishing any task, run the automated verification command (e.g. `npx playwright test` and/or `npm run build`).
- Do not claim a task is complete if tests fail or if the build is broken.

---

## 4. Server Environment, Deployment & Operational Constraints

- **Server IP**: `123.30.233.101`, User: `duongnv`, Password: `duongvnn`, Base dir: `/home/duongnv`
- **Backend Deployment** (`FastAPI-boilerplate`):
  - Upload to `/home/duongnv/hhbackend`
  - Library `ai-agent-assistant`: Upload to `/home/duongnv/hhbackend/vendor/ai-agent-assistant`
  - Restart command: `cd /home/duongnv/hhbackend && docker compose restart web`
- **User Frontend Deployment** (`jobhunt-ai-agent_enduser`):
  - Upload to `/tmp/hh-user-frontend`
  - Rebuild script: `cd /home/duongnv && sudo ./rebuild-user-frontend.sh`
- **Admin Frontend Deployment** (`hh-admin-frontend`):
  - Upload to `/tmp/hh-admin-frontend`
  - Rebuild script: `cd /home/duongnv && sudo ./rebuild-admin-frontend.sh`
- **Local Port Forwarding**:
  - `ssh -L 3306:localhost:3306 -L 8108:localhost:8108 -L 6379:localhost:6379 duongnv@123.30.233.101` (forwards MySQL, TypeSense, Redis to local for live testing).
- **Mandatory Safety Rule**:
  - NEVER execute destructive commands (deleting records, dropping tables/databases, removing critical files) without explicit confirmation from the user.
- **Hiến Pháp Giao Thức Admin Nội Bộ (Strict HTTP For Admin Subdomain)**:
  - **Domain Admin Nội Bộ**: `http://admin.aihunter.com` (giao thức HTTP, **tuyệt đối KHÔNG có chữ S** - `https://`).
  - Domain này chỉ chạy nội bộ trên máy admin, KHÔNG có chứng chỉ SSL, KHÔNG public ra Internet.
  - Mọi cấu hình, base URL trong Extension, Frontend, Backend, tài liệu và môi trường nội bộ **BẮT BUỘC 100% PHẢI LÀ HTTP**: `http://admin.aihunter.com`. Nghiêm cấm tự ý thêm `s` thành `https://admin.aihunter.com`.
  - Đối với Chrome Extension khi chạy trên các trang HTTPS (như Facebook): BẮT BUỘC phải thực hiện network request qua Background Service Worker để tránh việc trình duyệt tự động nâng cấp mixed-content (`upgrade-insecure-requests`) thành HTTPS.
- **Detailed Reference**: See [DEPLOYMENT.md](file:///./DEPLOYMENT.md).

---

## 5. Hiến Pháp Ngôn Ngữ & Quản Lý Thực Thể (Language, UI & Entity Constitution)

1. **Chuẩn Mực Tiếng Việt Có Dấu Tuyệt Đối (Strict Diacritics For User-Facing Content)**:
   - Mọi thông điệp, văn bản, thông báo, thẻ hiển thị, nhãn, nút bấm và nội dung phản hồi trả về cho người dùng cuối (User-Facing) **BẮT BUỘC 100% PHẢI LÀ TIẾNG VIỆT CÓ DẤU**, chuẩn ngữ pháp, rõ nghĩa và chuyên nghiệp.
   - Tuyệt đối nghiêm cấm hiển thị tiếng Việt không dấu ra ngoài giao diện (ví dụ: không viết "Muc luong", "Dia diem", "Ban co muon xem tiep khong?", phải viết chính xác: "Mức lương:", "Địa điểm:", "Bạn có muốn xem tiếp không?").
   - Văn bản không dấu chỉ được phép tồn tại trong các thuật toán ngầm nội bộ (internal normalization, token search, regex parsing).

2. **Quản Lý Thực Thể & Ontology Tập Trung (Centralized Ontology & Anti-Literal Strings)**:
   - Nghiêm cấm phân tán, tự ý định nghĩa ad-hoc các Literal String rời rạc (danh sách ngành nghề, tỉnh thành, skills, topwords, cấp bậc, nhóm công ty...) rải rác ở nhiều file logic.
   - Toàn bộ thực thể, từ đồng nghĩa (synonyms), phân cấp chức danh (level/role taxonomy), nhóm tổ chức (Big4, FAANG, Top Tech...) phải có nguồn sự thật duy nhất (Single Source of Truth) từ hệ thống Ontology tập trung, đồng bộ với dữ liệu thực tế từ database (Typesense / MySQL).

3. **Chuẩn Mực Định Dạng Ngày Giờ & Múi Giờ Hà Nội (Hanoi UTC+7 Datetime Constitution)**:
   - Mọi mốc thời gian, ngày giờ hiển thị trên giao diện người dùng (User-Facing & Admin-Facing) **BẮT BUỘC theo múi giờ Hà Nội (UTC+7, `Asia/Ho_Chi_Minh`)**.
   - Định dạng ngày chuẩn: `dd/MM/yyyy` (nghiêm cấm hiển thị `MM/dd/yyyy` hay `yyyy-MM-dd` thô ra UI).
   - Định dạng giờ chuẩn: `HH:mm:ss` (hoặc `HH:mm`).
   - Định dạng ngày & giờ kết hợp: `HH:mm:ss dd/MM/yyyy`.
   - Phải sử dụng bộ hàm chuẩn hóa tập trung (ví dụ: `src/lib/datetime.ts`) thay vì tự ý gọi `toLocaleDateString()` / `toLocaleTimeString()` không cấu hình múi giờ khiến thời gian hiển thị sai lệch theo múi giờ máy khách.

4. **Nguyên Tắc Trực Quan & Toàn Vẹn Khung Nhìn (Layout & Overlay Integrity)**:
   - Mọi slide-over drawer, modal chi tiết nghiệp vụ (như Timeline hành trình phiên) phải sở hữu z-index cao cấp độ ưu tiên (`z-[9999]`), chiếm trọn khung nhìn theo chiều dọc.
   - Các thành phần khung sườn cố định không dùng đến (như `kt_app_header`) phải được ẩn dứt điểm (`d-none`, gỡ bỏ `data-kt-app-header-fixed`), tuyệt đối không để chèn ép hay che khuất thông tin thao tác của người dùng.

---

## 6. Tiêu Chuẩn Giám Sát, Debug & Profile Hiệu Năng (Observability & LangSmith Standard)

- **Ưu tiên LangSmith cho Debug & Profiling**:
  - Khi cần chẩn đoán lỗi (diagnose bugs), truy vết sự cố hội thoại, phân tích prompt/output của LLM, đo lường độ trễ (latency profiling), hoặc kiểm tra token usage/costs, **BẮT BUỘC ưu tiên truy cập LangSmith API** (sử dụng credentials cấu hình trong `.env`: `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_ENDPOINT`).
  - Lấy dữ liệu thực tế (real traces, child spans, tool arguments, errors, exceptions) từ LangSmith làm căn cứ chẩn đoán, tuyệt đối không suy đoán mù (no speculative debugging).

