@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   PrintMind V1.0 Competition Release
echo   一键启动脚本
echo ============================================
echo.

set MISSING=0

if not exist "backend\.venv\Scripts\python.exe" (
  echo [缺少] backend\.venv\Scripts\python.exe
  echo        请先在 backend 目录创建虚拟环境并安装依赖：
  echo          python -m venv .venv
  echo          .venv\Scripts\python.exe -m pip install -r requirements.txt
  set MISSING=1
)

if not exist "frontend\node_modules" (
  echo [缺少] frontend\node_modules
  echo        请在 frontend 目录执行：npm install
  set MISSING=1
)

if not exist "backend\.env" (
  echo [缺少] backend\.env
  echo        请复制 backend\.env.example 为 backend\.env
  echo        （DEEPSEEK_API_KEY 可留空，视觉不可用时自动回退规则诊断）
  set MISSING=1
)

if not exist "data\printmind.db" (
  echo [缺少] data\printmind.db
  echo        数据库文件缺失，请确认 data 目录完整。
  set MISSING=1
)

if "%MISSING%"=="1" (
  echo.
  echo 启动已取消：请先补齐上述缺失项后重试。
  echo.
  pause
  exit /b 1
)

echo 正在启动后端 FastAPI (127.0.0.1:8000) ...
start "PrintMind Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo 正在启动前端 Vite (127.0.0.1:5173) ...
start "PrintMind Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo 等待服务启动（约 6 秒）...
timeout /t 6 /nobreak >nul

echo 正在打开浏览器： http://127.0.0.1:5173
start "" "http://127.0.0.1:5173"

echo.
echo 启动完成。关闭两个新打开的命令行窗口即可停止前后端服务。
echo.
pause
endlocal
