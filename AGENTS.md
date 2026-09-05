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
- **Detailed Reference**: See [DEPLOYMENT.md](file:///./DEPLOYMENT.md).
