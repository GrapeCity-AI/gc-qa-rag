@echo off
REM Run Generic Pipeline from the correct directory
cd /d "%~dp0.."
set PYTHONPATH=.
pdm run --project ai_knowledge_service python ai_knowledge_service/examples/run_generic_pipeline.py %*
