@echo off
REM Run Forum Tutorial Pipeline from the correct directory
cd /d "%~dp0.."
set PYTHONPATH=.
pdm run --project ai_knowledge_service python ai_knowledge_service/examples/run_forum_tutorial_pipeline.py %*
