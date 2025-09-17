# Установка и запуск TBCparcer на Windows

Этот документ описывает полный цикл подготовки окружения на Windows 10/11: от клонирования репозитория до запуска smoke/E2E тестов. Все команды приведены для PowerShell 7.x, запускать их следует из окна с правами пользователя (администратор не требуется).

## 1. Предварительные требования

1. **Операционная система:** Windows 10/11 (x64) с последними обновлениями.
2. **Git for Windows:** [https://git-scm.com/download/win](https://git-scm.com/download/win).
3. **Python 3.11 (64-bit):** при установке отметить опцию «Add python.exe to PATH».
4. **Node.js 20 LTS** (в комплекте с Corepack) — [https://nodejs.org/](https://nodejs.org/).
5. **pnpm 10.16.x:** будет активирован через Corepack.
6. **SQLite CLI (опционально):** пригодится для ручного применения миграций. Можно установить из [https://www.sqlite.org/download.html](https://www.sqlite.org/download.html).
7. **PowerShell 7.x:** рекомендуется для удобной работы с длинными командами и UTF-8.

## 2. Клонирование репозитория

```powershell
cd $env:USERPROFILE\source
git clone https://github.com/worq1337/weewetw.git
cd weewetw
```

> При первом запуске рекомендуется выполнить `git pull` для синхронизации с `main`.

## 3. Настройка Python-окружения и зависимостей backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\tbcparcer_api\requirements.txt
```

> Все последующие команды, связанные с backend и тестами, выполняйте в активированном виртуальном окружении.

## 4. Установка зависимостей frontend

```powershell
corepack enable
corepack prepare pnpm@10.16.1 --activate
cd frontend\tbcparcer-frontend
pnpm install
cd ..\..
```

## 5. Настройка файлов `.env`

1. **Backend:**
   ```powershell
   Copy-Item backend\.env.example backend\.env -Force
   ```
   В файле `backend\.env` при необходимости заполните:
   - `OPENAI_API_KEY` / `OPENAI_API_BASE` (если используется облачный парсер),
   - `DATABASE_PATH` — путь к SQLite-файлу. По умолчанию используется `backend/tbcparcer_api/src/database/app.db`.

2. **Frontend:**
   ```powershell
   Copy-Item frontend\.env.example frontend\.env -Force
   ```
   Проверьте значения:
   - `VITE_API_BASE_URL=http://localhost:5000`
   - `VITE_DEFAULT_TELEGRAM_ID=123456789` (можно изменить на ваш Telegram ID).

## 6. Инициализация базы данных (миграции)

Backend автоматически создаст таблицы при первом запуске. Для явного применения схемы и загрузки справочников используйте скрипты:

1. Примените структуру схемы через Python (SQLite доступен «из коробки»):
   ```powershell
   python - <<'PY'
import pathlib, sqlite3
base_dir = pathlib.Path(__file__).resolve().parent
schema_path = base_dir / 'database' / 'schema.sql'
db_path = base_dir / 'backend' / 'tbcparcer_api' / 'src' / 'database' / 'app.db'
db_path.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(db_path) as conn:
    conn.executescript(schema_path.read_text(encoding='utf-8'))
print(f"Schema applied to {db_path}")
PY
   ```
2. (Опционально) Загрузите базовые операторы:
   ```powershell
   if (Get-Command sqlite3 -ErrorAction SilentlyContinue) {
       sqlite3 backend\tbcparcer_api\src\database\app.db ".read database/operators_dictionary.sql"
   }
   ```
3. Для заполнения тестовыми данными можно запустить скрипт:
   ```powershell
   python backend\tbcparcer_api\init_test_data.py
   ```

## 7. Запуск backend-сервиса

Оставьте активированным виртуальное окружение и выполните:

```powershell
python backend\tbcparcer_api\src\main.py
```

Сервис поднимется на `http://localhost:5000`. Первые строки логов сообщат о загрузке словаря операторов и создании базы.

## 8. Запуск frontend (Vite)

Откройте новое окно PowerShell, перейдите в проект и запустите дев-сервер:

```powershell
cd <путь_к_репозиторию>\weewetw
corepack enable
cd frontend\tbcparcer-frontend
pnpm dev
```

По умолчанию UI доступен на `http://localhost:5173`. Для работы с backend убедитесь, что переменная `VITE_API_BASE_URL` указывает на `http://localhost:5000`.

## 9. Проверка CORS

В отдельном окне PowerShell выполните preflight-запрос и убедитесь, что backend отвечает заголовком `Access-Control-Allow-Origin`:

```powershell
$headers = @{
  Origin = 'http://localhost:5173'
  'Access-Control-Request-Method' = 'GET'
}
$response = Invoke-WebRequest -Uri 'http://localhost:5000/api/transactions?telegram_id=123456789' -Method Options -Headers $headers
$response.Headers['Access-Control-Allow-Origin']
```

Ожидаемое значение — `*` или `http://localhost:5173`.

## 10. Smoke/E2E тесты

Smoke-сценарий, закрывающий цепочку parser → API/DB → UI → export и проверки фильтров/навигации, реализован в `tests\e2e\test_end_to_end.py`.

```powershell
cd <путь_к_репозиторию>\weewetw
.\.venv\Scripts\Activate.ps1
pytest tests\e2e\test_end_to_end.py
```

Тест создает изолированную SQLite-базу, вызывает `AIParsingService`, сохраняет транзакции через `/api/ai/parse-and-save`, проверяет пагинацию `/api/transactions` и валидирует Excel-выгрузку (`/api/export/excel`) на корректные заголовки, ширины и числовой формат времени `hh:mm`.

## 11. Дополнительные рекомендации

- Для повторного запуска frontend/backend используйте отдельные окна PowerShell, оставляя виртуальное окружение активным для backend.
- После завершения работы деактивируйте окружение: `deactivate`.
- Регулярно обновляйте зависимости (`pip install -r ... --upgrade`, `pnpm update`) и синхронизируйте ветку `main` (`git pull`).
