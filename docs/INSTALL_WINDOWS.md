# Установка TBCparcer на Windows (черновик)

> Документ находится в разработке. Шаги будут дополняться по мере выполнения задач.

## Предварительные требования

- Windows 10/11 с установленными обновлениями
- Git для Windows
- Python 3.11.x
- Node.js 20.x и pnpm 10.16.x

## Базовые шаги установки

1. Клонируйте репозиторий:
   ```powershell
   git clone https://github.com/worq1337/weewetw.git
   cd weewetw
   ```
2. Установите Python-зависимости для backend:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r backend\tbcparcer_api\requirements.txt
   ```
3. Установите зависимости frontend:
   ```powershell
   corepack enable
   corepack prepare pnpm@10.16.1 --activate
   cd frontend\tbcparcer-frontend
   pnpm install
   ```

_Дальнейшие шаги будут описаны позже._
