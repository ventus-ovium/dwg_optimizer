@echo off
chcp 65001 > nul
setlocal

:: Впишите сюда желаемое имя программы (без .exe)
set APP_NAME=DWG_Optimizer_v3

echo ==========================================
echo      АВТОМАТИЧЕСКАЯ СБОРКА %APP_NAME%
echo ==========================================

:: 1. Очистка старых файлов сборки
echo [1/5] Очистка старых файлов...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec
if exist %APP_NAME%.exe del %APP_NAME%.exe

:: 2. Проверка и создание виртуального окружения
if exist venv (
    echo [2/5] Виртуальное окружение найдено.
) else (
    echo [2/5] Создание чистого виртуального окружения...
    python -m venv venv
)

:: 3. Активация и установка библиотек
echo [3/5] Установка зависимостей...
call venv\Scripts\activate
python -m pip install --upgrade pip
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo ОШИБКА: Файл requirements.txt не найден!
    pause
    exit /b
)

:: 4. Запуск сборки PyInstaller
echo [4/5] Сборка EXE файла...
if exist "icon.ico" (
    set "ICON_CMD=--icon=icon.ico --add-data icon.ico;."
    echo   --- Иконка найдена, собираем с ней ---
) else (
    set "ICON_CMD="
    echo   --- ВНИМАНИЕ: Файл icon.ico не найден в папке ---
)

pyinstaller --noconsole --onefile --clean %ICON_CMD% --collect-all tkinterdnd2 --hidden-import=win32com.client --hidden-import=pythoncom --name="%APP_NAME%" main.py

:: 5. Завершение
echo [5/5] Перемещение готового файла...
if exist dist\%APP_NAME%.exe (
    copy dist\%APP_NAME%.exe .
    rmdir /s /q build
    rmdir /s /q dist
    del %APP_NAME%.spec
    echo.
    echo ==========================================
    echo        УСПЕШНО! ФАЙЛ ГОТОВ К РАБОТЕ
    echo ==========================================
) else (
    echo.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo          ОШИБКА СБОРКИ
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
)

pause