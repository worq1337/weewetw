# AGENTS.md

## Repository and Branch
- Work only in repository `worq1337/weewetw`.
- Use branch `main` only.  
- Do not create new branches, do not open pull requests. Commit directly to `main`.

## Project Structure
- Backend: `backend/tbcparcer_api` (Python, Flask, SQLAlchemy).
- Frontend: `frontend/tbcparcer-frontend` (Node.js, PNPM).
- Database: `database/`.
- Telegram bot: `telegram_bot/`.
- Documentation: `docs/`.

## Tasks (step by step)
1. **Dependencies & Setup**  
   - Install backend deps (`pip install -r backend/tbcparcer_api/requirements.txt`, or create this file if missing).  
   - Install frontend deps (`cd frontend/tbcparcer-frontend && pnpm install`).  

2. **Integration**  
   - Remove mocks.  
   - Link `parser → API → DB → UI → export`.  

3. **Frontend fixes**  
   - Implement auto-resize of table columns.  
   - Display time everywhere as `HH:MM` (no seconds).  
   - Fix alignment panel (gear menu) with persistence of settings.  

4. **Manual check form**  
   - Rewrite "add check manually" as a dynamic form (based on schema of columns).  
   - Add validation and direct DB insert (without AI).  

5. **Operator Dictionary**  
   - Create `data/operators_dict.json` with base values.  
   - Implement hot-reload (`POST /dictionary/reload`).  
   - Integrate dictionary into parsing/normalization.  

6. **Excel Export**  
   - Standardize format: headers, widths, time as numeric type with `hh:mm` format.  

7. **Testing**  
   - Add smoke/E2E tests: `parser → UI → export`.  
   - Verify filters and navigation.  

8. **Documentation**  
   - Create `docs/INSTALL_WINDOWS.md` with full step-by-step install & run guide:  
     - prerequisites (Python, Node, DB),  
     - cloning repo,  
     - environment setup (`.env`),  
     - DB migrations,  
     - service startup,  
     - CORS check.  

9. **Final checks**  
   - Regression testing.  
   - Fix issues.  
   - Update CHANGELOG if present.

## Commit Policy
- Commit after **each step**, atomically.  
- Use **Conventional Commit** format:  
  - `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`.  
- Push directly to `main` after every commit.  
- After each commit, print a short report with commit SHA.
