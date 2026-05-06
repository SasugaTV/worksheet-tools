@echo off
echo Starting Worksheet Tools Script Runner
echo =====================================
echo.

REM Run each Python script in sequence
echo Running crossword_generator.py...
python crossword_generator.py
if errorlevel 1 (
    echo Error running crossword_generator.py
    pause
    exit /b 1
)
echo crossword_generator.py completed successfully
echo.

echo Running missing_letters_generator.py...
python missing_letters_generator.py
if errorlevel 1 (
    echo Error running missing_letters_generator.py
    pause
    exit /b 1
)
echo missing_letters_generator.py completed successfully
echo.

echo Running word_scrambler.py...
python word_scrambler.py
if errorlevel 1 (
    echo Error running word_scrambler.py
    pause
    exit /b 1
)
echo word_scrambler.py completed successfully
echo.

echo Running word_search_generator.py...
python word_search_generator.py
if errorlevel 1 (
    echo Error running word_search_generator.py
    pause
    exit /b 1
)
echo word_search_generator.py completed successfully
echo.

echo Running word_search_intersecting.py...
python word_search_intersecting.py
if errorlevel 1 (
    echo Error running word_search_intersecting.py
    pause
    exit /b 1
)
echo word_search_intersecting.py completed successfully
echo.

echo Running word_splitter.py...
python word_splitter.py
if errorlevel 1 (
    echo Error running word_splitter.py
    pause
    exit /b 1
)
echo word_splitter.py completed successfully
echo.

echo =====================================
echo All scripts completed successfully!
echo.
pause
