@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Setup required. Follow docs\local-demo.md to create .venv and install dependencies.
  pause
  exit /b 1
)
ollama list >nul 2>&1
if errorlevel 1 (
  echo Start Ollama and make sure qwen2.5:7b is installed. See docs\local-demo.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" make_demo_contract.py input_files\synthetic-contract.pdf
if errorlevel 1 goto failed
".venv\Scripts\python.exe" local_demo.py input_files\synthetic-contract.pdf --output output_results\local-demo
if errorlevel 1 goto failed
start "" "%~dp0output_results\local-demo\report.html"
exit /b 0
:failed
echo Demo failed. Review the error above. Previous report files may be stale.
pause
exit /b 1
