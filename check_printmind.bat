@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set FAIL=0
set WARN=0

echo ============================================
echo   PrintMind 比赛环境检查 (V1.4 Demo Ready)
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (echo [FAIL] Python & set /a FAIL+=1) else (echo [OK] Python)

where node >nul 2>&1
if errorlevel 1 (echo [FAIL] Node & set /a FAIL+=1) else (echo [OK] Node)

if exist "backend" (echo [OK] backend) else (echo [FAIL] backend & set /a FAIL+=1)
if exist "frontend" (echo [OK] frontend) else (echo [FAIL] frontend & set /a FAIL+=1)
if exist "backend\.env" (echo [OK] backend\.env) else (echo [FAIL] backend\.env & set /a FAIL+=1)
if exist "data\printmind.db" (echo [OK] data\printmind.db) else (echo [FAIL] data\printmind.db & set /a FAIL+=1)
if exist "frontend\src\assets\showcase\showcase-hero.webp" (echo [OK] showcase-hero.webp) else (echo [FAIL] showcase-hero.webp & set /a FAIL+=1)

if exist "backend\.venv\Scripts\python.exe" (echo [OK] backend venv) else (echo [WARN] backend venv missing - run setup_for_teammate.bat & set /a WARN+=1)
if exist "frontend\node_modules" (echo [OK] frontend node_modules) else (echo [WARN] frontend node_modules missing - run setup_for_teammate.bat & set /a WARN+=1)

set "PY=backend\.venv\Scripts\python.exe"
if exist "%PY%" (
  "%PY%" -c "import base64;exec(base64.b64decode('aW1wb3J0IG9zCmltcG9ydCByZQppbXBvcnQgc3FsaXRlMwppbXBvcnQgc3lzCgpkYl9wYXRoID0gc3lzLmFyZ3ZbMV0gaWYgbGVuKHN5cy5hcmd2KSA+IDEgZWxzZSByIkY6XFByaW50TWluZFxkYXRhXHByaW50bWluZC5kYiIKZmFpbHMgPSAwCgpjb25uID0gTm9uZQp0cnk6CiAgICBjb25uID0gc3FsaXRlMy5jb25uZWN0KGRiX3BhdGgpCiAgICBjb25uLmV4ZWN1dGUoInNlbGVjdCAxIikKICAgIHByaW50KCJbT0tdIERhdGFiYXNlIHJlYWRhYmxlIikKZXhjZXB0IEV4Y2VwdGlvbjoKICAgIHByaW50KCJbRkFJTF0gRGF0YWJhc2UgcmVhZGFibGUiKQogICAgZmFpbHMgKz0gMQoKaWYgY29ubiBpcyBub3QgTm9uZToKICAgIHRyeToKICAgICAgICBpZHMgPSBzZXQoclswXSBmb3IgciBpbiBjb25uLmV4ZWN1dGUoInNlbGVjdCBleHBlcmltZW50X2lkIGZyb20gZXhwZXJpbWVudF9yZWNvcmRzIikpCiAgICAgICAgZm9yIHJvdyBpbiBjb25uLmV4ZWN1dGUoCiAgICAgICAgICAgICJzZWxlY3Qgbm90ZXMgZnJvbSBkaWFnbm9zaXNfcmVjb3JkcyB3aGVyZSB2ZXJpZmllZD0xIGFuZCBkYXRhX3NvdXJjZT0/IiwKICAgICAgICAgICAgKCJyZWFsIiwpLAogICAgICAgICk6CiAgICAgICAgICAgIG1hdGNoID0gcmUuc2VhcmNoKHIiUkVBTC1cZCsiLCByb3dbMF0gb3IgIiIpCiAgICAgICAgICAgIGlmIG1hdGNoOgogICAgICAgICAgICAgICAgaWRzLmFkZChtYXRjaC5ncm91cCgwKSkKCiAgICAgICAgZm9yIHJpZCBpbiAoIlJFQUwtMDAxIiwgIlJFQUwtMDA2Iik6CiAgICAgICAgICAgIGlmIHJpZCBpbiBpZHM6CiAgICAgICAgICAgICAgICBwcmludCgiW09LXSAlcyBwcmVzZW50IiAlIHJpZCkKICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIHByaW50KCJbRkFJTF0gJXMgbWlzc2luZyIgJSByaWQpCiAgICAgICAgICAgICAgICBmYWlscyArPSAxCgogICAgICAgIHZlcmlmaWVkID0gY29ubi5leGVjdXRlKAogICAgICAgICAgICAic2VsZWN0IGNvdW50KCopIGZyb20gZGlhZ25vc2lzX3JlY29yZHMgd2hlcmUgdmVyaWZpZWQ9MSBhbmQgZGF0YV9zb3VyY2U9PyIsCiAgICAgICAgICAgICgicmVhbCIsKSwKICAgICAgICApLmZldGNob25lKClbMF0KICAgICAgICBpZiB2ZXJpZmllZCA+PSAxOgogICAgICAgICAgICBwcmludCgiW09LXSB2ZXJpZmllZF9jYXNlcyA9ICVkIiAlIHZlcmlmaWVkKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHByaW50KCJbRkFJTF0gdmVyaWZpZWRfY2FzZXMgPj0gMSAoZ290ICVkKSIgJSB2ZXJpZmllZCkKICAgICAgICAgICAgZmFpbHMgKz0gMQogICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICBwcmludCgiW0ZBSUxdIERhdGFiYXNlIHF1ZXJ5IikKICAgICAgICBmYWlscyArPSAxCiAgICBmaW5hbGx5OgogICAgICAgIGNvbm4uY2xvc2UoKQoKc3lzLmV4aXQoZmFpbHMpCg==').decode())" "%~dp0data\printmind.db"
  set /a FAIL+=!errorlevel!
) else (
  echo [WARN] skip database checks - backend venv missing
  set /a WARN+=1
)

echo.
echo ============================================
if %FAIL%==0 (
  echo [OK] Demo essentials ready
) else (
  echo [FAIL] PrintMind 存在 %FAIL% 项问题，请修复后再演示
)
if %WARN% GTR 0 echo [WARN] 有 %WARN% 项提示（缺少依赖时请先运行 setup_for_teammate.bat）
echo ============================================
endlocal
pause
