@echo off
REM Script Windows pour crawler les sources canadiennes
REM Usage: run_firecrawl.bat [single|priority|all]

SET MODE=%1
IF "%MODE%"=="" SET MODE=priority

echo ========================================
echo  Zero Obstacle - Crawl Sources Canada
echo ========================================
echo.

IF "%MODE%"=="single" (
    IF "%2"=="" (
        echo Usage: run_firecrawl.bat single https://www.canada.ca/...
        exit /B 1
    )
    python agents/firecrawl_crawler.py %2
    exit /B 0
)

IF "%MODE%"=="priority" (
    echo Mode: Sources prioritaires
    python scripts/crawl_priority.py
    exit /B 0
)

IF "%MODE%"=="all" (
    echo Mode: Toutes les sources
    python scripts/crawl_all.py
    exit /B 0
)

echo Mode invalide. Usage: run_firecrawl.bat [single|priority|all]
exit /B 1
