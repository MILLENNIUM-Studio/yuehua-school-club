@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: 检查 Python 是否可用
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [Python未安装] 请确保已安装Python 3.8或更高版本
    pause
    exit /b 1
)

:: 检查现有虚拟环境
if exist "Scripts\activate.bat" (
    echo [信息] 正在激活虚拟环境...
    call Scripts\activate.bat
    
    :: 验证虚拟环境
    python -c "import flask" 2>nul
    if !errorlevel! equ 0 (
        echo [信息] 环境检查通过，启动应用...
        echo [信息] 清理缓存文件...
        del /s /q *.pyc >nul 2>&1
        rd /s /q __pycache__ >nul 2>&1
        pip cache purge
        python app.py
        if !errorlevel! neq 0 (
            echo [错误] 应用异常退出
            pause
        )
        exit /b 0
    ) else (
        echo [警告] 环境缺少必要依赖
        set /p choice="是否安装依赖？(y/n): "
        if /i "!choice!"=="y" (
            echo [信息] 正在安装依赖...
            pip install --no-cache-dir flask==3.0.0 flask-sqlalchemy==3.1.1 flask-login==0.6.3 flask-wtf==1.2.1 werkzeug==3.0.1 flask-migrate==4.0.5 email-validator==2.1.0.post1 flask-limiter==3.5.0 alembic==1.13.1
            if !errorlevel! equ 0 (
                echo [信息] 依赖安装完成，启动应用...
                echo [信息] 清理缓存文件...
                del /s /q *.pyc >nul 2>&1
                rd /s /q __pycache__ >nul 2>&1
                pip cache purge
                python app.py
            ) else (
                echo [错误] 依赖安装失败
                pause
                exit /b 1
            )
        ) else (
            echo [信息] 已取消操作
            pause
            exit /b 1
        )
    )
) else (
    echo [警告] 未检测到虚拟环境
    echo.
    echo 可能原因：
    echo 1. 首次在此计算机运行
    echo 2. 虚拟环境文件已损坏
    echo.
    set /p choice="是否创建新的虚拟环境？(y/n): "
    if /i "!choice!"=="y" (
        echo [警告] 即将创建新环境
        set /p confirm="确认继续？(y/n): "
        if /i "!confirm!"=="y" (
            echo [信息] 创建虚拟环境...
            python -m venv .
            call Scripts\activate.bat
            echo [信息] 安装依赖...
            pip install --no-cache-dir -r requirements.txt
            if !errorlevel! equ 0 (
                echo [信息] 配置完成，启动应用...
                echo [信息] 清理缓存文件...
                del /s /q *.pyc >nul 2>&1
                rd /s /q __pycache__ >nul 2>&1
                pip cache purge
                python app.py
            ) else (
                echo [错误] 依赖安装失败
                pause
                exit /b 1
            )
        ) else (
            echo [信息] 已取消操作
            pause
            exit /b 0
        )
    ) else (
        echo [信息] 已取消操作
        pause
        exit /b 0
    )
)

:: 清理缓存
echo [信息] 清理缓存文件...
del /s /q *.pyc >nul 2>&1
rd /s /q __pycache__ >nul 2>&1
pip cache purge

endlocal 