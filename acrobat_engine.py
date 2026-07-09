import os
import fitz  # Это и есть библиотека PyMuPDF
from pathlib import Path

def optimize_pdfs(pdf_paths: list):
    print(f"\n[Optimization Engine] Начинаем сжатие {len(pdf_paths)} файлов (без участия Adobe!)...")
    
    for pdf_path in pdf_paths:
        print(f"  -> Сжимаем: {pdf_path.name}...")
        
        # Создаем временное имя файла
        temp_path = pdf_path.with_name(f"temp_{pdf_path.name}")
        
        try:
            # Открываем оригинальный PDF
            doc = fitz.open(str(pdf_path))
            
            # Сохраняем с максимальной оптимизацией
            doc.save(
                str(temp_path),
                garbage=4,        # Максимальное удаление неиспользуемых объектов (слои, дубли)
                deflate=True,     # Сжатие потоков данных
                clean=True        # Очистка синтаксиса файла
            )
            doc.close()
            
            # Считаем разницу в весе для красивого отчета
            orig_size = os.path.getsize(pdf_path) / (1024 * 1024)
            new_size = os.path.getsize(temp_path) / (1024 * 1024)
            
            # Безопасно заменяем старый тяжелый файл новым легким
            os.replace(temp_path, pdf_path)
            
            print(f"     Готово! Размер: {orig_size:.2f} МБ -> {new_size:.2f} МБ")
            
        except Exception as e:
            print(f"     [!] Ошибка при сжатии {pdf_path.name}: {e}")
            # Убираем за собой временный файл в случае сбоя
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except:
                    pass
            
    print(f"[Optimization Engine] Оптимизация завершена!\n")
