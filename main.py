import os
import time
from pathlib import Path
from datetime import timedelta

from gui import AppWindow
from dwg_optimizer import optimize_dwgs
import autocad_engine
from pdf_merger import merge_pdfs
import acrobat_engine

def collect_all_dwgs(input_items):
    """Превращает список папок и файлов в плоский список уникальных .dwg, включая ПОДПАПКИ"""
    unique_dwgs = set()
    
    for item in input_items:
        path = Path(item)
        if path.is_file() and path.suffix.lower() == '.dwg':
            if not path.name.startswith("~$") and not path.name.startswith("temp_"):
                unique_dwgs.add(path)
        elif path.is_dir():
            # ИСПОЛЬЗУЕМ rglob ДЛЯ ПОИСКА ВО ВЛОЖЕННЫХ ПАПКАХ
            for f in path.rglob("*.dwg"):
                if not f.name.startswith("~$") and not f.name.startswith("temp_"):
                    unique_dwgs.add(f)
                    
    return list(unique_dwgs)

def main_pipeline(settings: dict):
    update_progress = settings.get("progress_callback")
    update_status = settings.get("status_callback")
    update_time = settings.get("time_callback")
    is_cancelled = settings.get("is_cancelled", lambda: False) # Получаем функцию проверки
    
    input_items = settings.get("input_items")
    do_opt_dwg = settings.get("do_opt_dwg")
    do_print = settings.get("do_print")
    do_merge = settings.get("do_merge")
    do_opt_pdf = settings.get("do_opt_pdf")
    
    update_status("Сканирование файлов (включая подпапки)...")
    dwg_files = collect_all_dwgs(input_items)
    
    if not dwg_files:
        update_status("Нет подходящих DWG файлов.")
        return

    total_files = len(dwg_files)
    update_status(f"Найдено чертежей: {total_files}")
    time.sleep(1)

    current_progress = 0
    start_time = time.time()

    def tick_progress(increment):
        nonlocal current_progress
        current_progress += increment
        update_progress(current_progress)
        
        elapsed = time.time() - start_time
        if current_progress > 0:
            estimated_total = elapsed / (current_progress / 100)
            remaining = estimated_total - elapsed
            rem_str = str(timedelta(seconds=int(remaining)))
            if remaining > 60:
                rem_str = f"{int(remaining//60)} мин {int(remaining%60)} сек"
            else:
                rem_str = f"{int(remaining)} сек"
            update_time(f"Осталось примерно: {rem_str}")
    
    # --- 1. ОПТИМИЗАЦИЯ DWG (20%) ---
    if do_opt_dwg and not is_cancelled():
        step_dwg = 20 / total_files
        update_status("Этап 1/4: Глубокая очистка исходников...")
        # Передаем is_cancelled внутрь движка
        optimize_dwgs(dwg_files, progress_cb=lambda: tick_progress(step_dwg), status_cb=update_status, is_cancelled=is_cancelled)
    else:
        current_progress += 20
        update_progress(current_progress)

    # --- 2. ПЕЧАТЬ (50%) ---
    dwg_to_pdfs = {}
    if do_print and not is_cancelled():
        step_print = 50 / total_files
        update_status("Этап 2/4: Печать в PDF (AutoCAD)... Это может занять время.")
        # Передаем is_cancelled внутрь движка
        dwg_to_pdfs = autocad_engine.batch_plot_layouts(dwg_files, settings, progress_cb=lambda: tick_progress(step_print), status_cb=update_status, is_cancelled=is_cancelled)
    else:
        current_progress += 50
        update_progress(current_progress)

    # --- 3. ОБЪЕДИНЕНИЕ (10%) ---
    files_to_optimize = []
    if do_merge and dwg_to_pdfs and not is_cancelled():
        update_status("Этап 3/4: Анализ и склейка листов...")
        merged = merge_pdfs(dwg_to_pdfs)
        files_to_optimize = merged
        current_progress += 10
        update_progress(current_progress)
    elif not do_merge and dwg_to_pdfs:
        for v in dwg_to_pdfs.values():
            files_to_optimize.extend(v)
        current_progress += 10
    else:
        current_progress += 10

    # --- 4. СЖАТИЕ PDF (20%) ---
    if do_opt_pdf and files_to_optimize and not is_cancelled():
        total_pdfs = len(files_to_optimize)
        step_pdf = 20 / total_pdfs if total_pdfs > 0 else 20
        update_status("Этап 4/4: Финальное сжатие PDF...")
        
        for i, pdf in enumerate(files_to_optimize):
            # ПРОВЕРКА ОТМЕНЫ В ЦИКЛЕ СЖАТИЯ:
            if is_cancelled():
                update_status("⚠️ Обработка прервана пользователем на этапе сжатия PDF.")
                break
                
            update_status(f"Сжатие PDF [{i+1}/{total_pdfs}]: {pdf.name}")
            acrobat_engine.optimize_pdfs([pdf])
            tick_progress(step_pdf)
    else:
        current_progress += 20
        update_progress(current_progress)

    # --- 5. УБОРКА ВРЕМЕННЫХ ФАЙЛОВ (Выполняется ВСЕГДА, даже при остановке!) ---
    update_status("Удаление временных файлов...")
    affected_dirs = set(f.parent for f in dwg_files)
    for d in affected_dirs:
        for ext in ["*.bak", "*.log", "temp_*"]: # Заодно подчищаем любой случайно оставшийся temp_
            for junk in d.glob(ext):
                try: junk.unlink()
                except: pass
    
    if is_cancelled():
        update_status("⚠️ Обработка была остановлена. Часть файлов могла остаться необработанной.")
        return "Остановлено пользователем"

    update_progress(100)
    update_time("")
    
    end_time = time.time()
    total_seconds = end_time - start_time
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    time_str = f"{minutes} мин. {seconds:.1f} сек."
    
    print(f"--- ГОТОВО ---")
    print(f"⏳ Общее время выполнения: {time_str}")
    return time_str

if __name__ == "__main__":
    app = AppWindow(on_start_callback=main_pipeline)
    app.run()
