import os
import fitz  # PyMuPDF
import re
from pathlib import Path

def merge_pdfs(dwg_to_pdfs: dict) -> list:
    print(f"\n[PDF Merger] Анализ и сборка листов...")
    
    final_pdf_paths = []
    # Ваш паттерн: ИмяБазы + НижнееПодчеркивание + Цифры
    pattern = re.compile(r'^(.*)_(\d+)$')
    
    for dwg_path, pdf_list in dwg_to_pdfs.items():
        # Если лист всего один - клеить не с чем
        if len(pdf_list) <= 1:
            final_pdf_paths.extend(pdf_list)
            continue
            
        groups = {}
        standalone_pdfs = []
        
        # 1. Группировка внутри одного DWG
        for pdf in pdf_list:
            match = pattern.match(pdf.stem)
            
            # Условие: файл должен подходить под паттерн И быть в той же папке
            if match:
                base_name = match.group(1) # То, что до _
                page_num = int(match.group(2)) # Номер страницы
                
                if base_name not in groups:
                    groups[base_name] = []
                groups[base_name].append((page_num, pdf))
            else:
                # Если файл не подходит под паттерн (например, "Файл-СП-1"), он не участвует в склейке
                standalone_pdfs.append(pdf)

        # 2. Склейка групп
        for base_name, files in groups.items():
            if len(files) > 1:
                # Сортируем по номеру страницы (группа 2 из regex)
                files.sort(key=lambda x: x[0])
                
                # Имя итогового файла = Базовое Имя (без _1) + .pdf
                # Фактически это возвращает имя к исходному имени DWG (если нейминг был стандартный)
                merged_path = files[0][1].parent / f"{base_name}.pdf"
                
                print(f"  -> Склейка {len(files)} частей в '{merged_path.name}'...")
                
                try:
                    merged_doc = fitz.open()
                    for _, pdf_file in files:
                        doc = fitz.open(str(pdf_file))
                        merged_doc.insert_pdf(doc)
                        doc.close()
                    
                    merged_doc.save(str(merged_path))
                    merged_doc.close()
                    
                    final_pdf_paths.append(merged_path)
                    
                    # Удаляем исходные куски (_1, _2...)
                    for _, pdf_file in files:
                        try:
                            os.remove(pdf_file)
                        except:
                            pass
                    print(f"     Успешно.")
                    
                except Exception as e:
                    print(f"     [!] Ошибка при склейке: {e}")
                    final_pdf_paths.extend([f[1] for f in files])
            else:
                # Если под паттерн попал только 1 файл (редкость, но бывает), не клеим
                final_pdf_paths.append(files[0][1])
        
        # Добавляем в финальный список те файлы, которые не подошли под шаблон (СП и т.д.)
        final_pdf_paths.extend(standalone_pdfs)
        
    print(f"[PDF Merger] Сборка завершена. Файлов на выходе: {len(final_pdf_paths)}\n")
    return final_pdf_paths
