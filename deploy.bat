@echo off
REM ============================================
REM MathTasks 一键部署脚本 (Windows)
REM 用法：deploy.bat [dev|prod]
REM ============================================

setlocal enabledelayedexpansion

set ENV=%1
if "%ENV%"=="" set ENV=dev

echo ==================================================
echo    MathTasks 部署脚本 - %ENV% 环境
echo ==================================================

REM 检查环境变量文件
if not exist ".env.%ENV%" (
    echo [错误] 未找到 .env.%ENV% 文件
    echo 请先创建 .env.%ENV% 文件（可参考 .env.%ENV%.example）
    pause
    exit /b 1
)

REM 复制环境变量
copy /Y ".env.%ENV%" .env >nul
echo [成功] 已加载 %ENV% 环境配置

REM 检查 Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未运行，请启动 Docker Desktop
    pause
    exit /b 1
)

REM 停止旧容器
echo.
echo 停止旧容器...
docker compose down

REM 启动服务
echo.
echo 启动服务...
docker compose up -d --build

REM 等待数据库
echo.
echo 等待数据库启动...
timeout /t 10 /nobreak >nul

REM 检查数据库
docker compose exec -T postgres pg_isready -U mathtasks >nul 2>&1
if errorlevel 1 (
    echo [错误] 数据库启动失败
    docker compose logs postgres
    pause
    exit /b 1
)
echo [成功] 数据库已就绪

REM 备份数据库
echo.
echo 备份数据库...
if not exist "backups" mkdir backups
set BACKUP_FILE=backups\db_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
set BACKUP_FILE=%BACKUP_FILE: =0%
docker compose exec -T postgres pg_dump -U mathtasks mathtasks > "%BACKUP_FILE%" 2>nul
if exist "%BACKUP_FILE%" (
    echo [成功] 数据库已备份到: %BACKUP_FILE%
) else (
    echo [警告] 数据库备份失败（可能是新部署，数据库为空）
)

REM 初始化数据库
echo.
echo 初始化数据库...
docker compose exec -T api alembic upgrade head
docker compose exec -T api python scripts/init_users.py 2>nul
docker compose exec -T api python scripts/init_materials.py 2>nul

REM 读取端口（从 .env 文件）
for /f "tokens=1,2 delims==" %%a in ('type .env ^| findstr /b "API_PORT FRONTEND_PORT"') do (
    set %%a=%%b
)

echo.
echo ==================================================
echo 🎉 部署完成！
echo ==================================================
echo 前端：   http://localhost:%FRONTEND_PORT%
echo 后端：   http://localhost:%API_PORT%
echo API文档：http://localhost:%API_PORT%/docs
echo ==================================================
pause
