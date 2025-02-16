@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
echo 正在清理项目...

:: 清理Python缓存
del /s /q *.pyc >nul 2>&1
rd /s /q __pycache__ >nul 2>&1

:: 清理pip缓存
pip cache purge

:: 清理临时文件
del /s /q *.tmp >nul 2>&1
del /s /q *.bak >nul 2>&1

:: 清理日志文件（如果有）
del /s /q *.log >nul 2>&1

:: 清理测试缓存
rd /s /q .pytest_cache >nul 2>&1
rd /s /q .cache >nul 2>&1

echo 清理完成！
pause 