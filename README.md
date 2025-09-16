# weewetw

## Dependency installation

To install both backend and frontend dependencies locally, run:

```bash
./scripts/install_dependencies.sh
```

The script installs the backend requirements from `backend/tbcparcer_api/requirements.txt`
and then runs `pnpm install` in `frontend/tbcparcer-frontend`.

You can execute the commands manually as well:

```bash
python3 -m pip install -r backend/tbcparcer_api/requirements.txt
cd frontend/tbcparcer-frontend && pnpm install
```
