import os
import time
from pathlib import Path
import win32com.client
import pythoncom
import re

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def batch_plot_layouts(dwg_paths: list, settings: dict, progress_cb=None, status_cb=None, is_cancelled=None) -> dict:
    print(f"\n[AutoCAD Engine] Запуск. Файлов: {len(dwg_paths)}")
    generated_pdfs_by_dwg = {} 
    
    paper_size = settings.get("paper_size", "DEFAULT")
    orientation = settings.get("orientation", "DEFAULT")
    plot_style = settings.get("plot_style", "DEFAULT")

    try:
        pythoncom.CoInitialize()
        # Подключение ЕДИНОЖДЫ
        acad = win32com.client.dynamic.Dispatch("AutoCAD.Application")
        acad.Visible = True 
        time.sleep(2)
        
        total = len(dwg_paths)
        
        for idx, dwg in enumerate(dwg_paths):
            if is_cancelled and is_cancelled():
                print("  [!] Получена команда остановки. Прерываем печать...")
                break
            if status_cb: status_cb(f"Печать [{idx+1}/{total}]: {dwg.name}")
            print(f"  -> Открываем чертеж: {dwg.name}")
            doc = None
            successfully_printed_layouts = set()
            
            for attempt in range(10):
                current_dwg_pdfs = []
                try:
                    doc = acad.Documents.Open(str(dwg), False)
                    time.sleep(1) 
                    
                    # ГЛУШИМ ВСЕ ДИАЛОГОВЫЕ ОКНА (защита от зависаний)
                    try:
                        doc.SetVariable("FILEDIA", 0)
                        doc.SetVariable("CMDDIA", 0)
                        doc.SetVariable("BACKGROUNDPLOT", 0) 
                    except: pass
                    
                    base_path_prefix = str(dwg.parent / dwg.stem)
                    
                    valid_layouts = []
                    for i in range(doc.Layouts.Count):
                        lay = doc.Layouts.Item(i)
                        if lay.Name.upper() not in ["MODEL", "МОДЕЛЬ"]:
                            valid_layouts.append(lay)
                            
                    has_sp = any("СП" in lay.Name.upper() or "CP" in lay.Name.upper() for lay in valid_layouts)
                    is_single_layout = len(valid_layouts) == 1

                    for i, layout in enumerate(valid_layouts):
                        lay_name = layout.Name

                        if is_cancelled and is_cancelled():
                            print("     [!] Печать прервана пользователем. Останавливаем листы...")
                            break # Выходим из цикла печати листов
                        if has_sp:
                            safe_lay_name = sanitize_filename(lay_name)
                            pdf_path = f"{base_path_prefix}-{safe_lay_name}.pdf"
                        else:
                            if is_single_layout:
                                pdf_path = f"{base_path_prefix}.pdf"
                            else:
                                pdf_path = f"{base_path_prefix}_{i+1}.pdf"

                        if lay_name in successfully_printed_layouts:
                            if os.path.exists(pdf_path):
                                current_dwg_pdfs.append(Path(pdf_path))
                                continue 
                            else:
                                successfully_printed_layouts.remove(lay_name)

                        doc.ActiveLayout = layout
                        layout.RefreshPlotDeviceInfo()
                        layout.ConfigName = "DWG To PDF.pc3"
                        
                        if paper_size != "DEFAULT":
                            try: layout.CanonicalMediaName = paper_size.replace(" ", "_")
                            except: pass
                        if orientation != "DEFAULT":
                            layout.PlotRotation = 1 if orientation == "Landscape" else 0
                        if plot_style != "DEFAULT":
                            layout.PlotWithPlotStyles = True 
                            try: layout.StyleSheet = plot_style if plot_style not in [".", "Нет", ""] else ""
                            except: pass
                        layout.PlotType = 5        
                        layout.PaperUnits = 1      
                        layout.StandardScale = 16  
                        layout.PlotWithLineweights = True 
                        try: doc.SetVariable("PLOTTRANSPARENCYOVERRIDE", 2) 
                        except: pass
                        
                        if os.path.exists(pdf_path):
                            try: os.remove(pdf_path)
                            except: pass
                        
                        doc.Plot.PlotToFile(pdf_path, "DWG To PDF.pc3")
                        
                        if os.path.exists(pdf_path):
                            current_dwg_pdfs.append(Path(pdf_path))
                            successfully_printed_layouts.add(lay_name)
                    
                    break # Успех, выходим из цикла попыток
                                
                except Exception as e:
                    print(f"     [!] Сбой (AutoCAD занят). Ждем 3 сек... (Попытка {attempt+1}/10)")
                    time.sleep(3)
                finally:
                    if doc:
                        try: doc.Close(False) 
                        except: pass
            
            current_dwg_pdfs = list(dict.fromkeys(current_dwg_pdfs))
            if current_dwg_pdfs:
                generated_pdfs_by_dwg[dwg] = current_dwg_pdfs
                
            # Двигаем прогресс-бар после каждого чертежа
            if progress_cb: progress_cb()
                
    except Exception as e:
        print(f"[ФАТАЛЬНАЯ ОШИБКА] Не удалось подключиться к AutoCAD: {e}")
        
    return generated_pdfs_by_dwg
