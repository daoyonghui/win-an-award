@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   PrintMind 比赛演示启动 (Competition Demo)
echo ============================================
echo.

set MISSING=0
if not exist "backend\.venv\Scripts\python.exe" (
  echo [缺少] backend 虚拟环境，请先运行 setup_for_teammate.bat
  set MISSING=1
)
if not exist "frontend\node_modules" (
  echo [缺少] frontend 依赖，请先运行 setup_for_teammate.bat
  set MISSING=1
)
if "%MISSING%"=="1" (
  echo.
  echo 启动已取消：请先补齐依赖后重试。
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

echo 打开主页： http://127.0.0.1:5173
start "" "http://127.0.0.1:5173"

echo 离线演示（不依赖网络）： http://127.0.0.1:5173/demo-offline
echo.
echo 提示：若现场网络异常，可直接使用 /demo-offline 离线演示。
echo 关闭两个命令行窗口即可停止服务。
echo.
pause
endlocal
