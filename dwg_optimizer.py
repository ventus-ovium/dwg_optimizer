import os
import time
from pathlib import Path
import win32com.client
import pythoncom

def optimize_dwgs(dwg_paths: list, progress_cb=None, status_cb=None, is_cancelled=None):
    print(f"\n[DWG Optimizer] Начинаем глубокую очистку {len(dwg_paths)} чертежей...")
    
    try:
        pythoncom.CoInitialize()
        # Подключаемся один раз для всех файлов!
        acad = win32com.client.dynamic.Dispatch("AutoCAD.Application")
        acad.Visible = True 
        time.sleep(2)
        
        total = len(dwg_paths)
        
        for i, dwg in enumerate(dwg_paths):
            if is_cancelled and is_cancelled():
                print("  [!] Получена команда остановки. Прерываем цикл DWG Optimizer...")
                break
            if status_cb: status_cb(f"Очистка DWG [{i+1}/{total}]: {dwg.name}")
            print(f"  -> Очищаем DWG: {dwg.name}")
            
            temp_dwg = dwg.parent / f"temp_{dwg.name}"
            temp_path_str = str(temp_dwg).replace('\\', '/')
            
            if temp_dwg.exists():
                try: os.remove(temp_dwg)
                except Exception: continue

            doc = None
            try:
                doc = acad.Documents.Open(str(dwg), False)
                time.sleep(1)
                
                try:
                    doc.SetVariable("FILEDIA", 0)
                    doc.SetVariable("CMDDIA", 0)
                except: pass
                
                doc.SendCommand(f'_-WBLOCK\n"{temp_path_str}"\n*\n')
                
                wait_time = 0
                is_ready = False
                while wait_time < 60:
                    if temp_dwg.exists():
                        try:
                            os.rename(temp_dwg, temp_dwg) 
                            is_ready = True
                            break
                        except OSError: pass
                    time.sleep(1)
                    wait_time += 1
                
                doc.Close(False)
                doc = None
                time.sleep(1)
                
                if is_ready:
                    doc_temp = acad.Documents.Open(str(temp_dwg), False)
                    time.sleep(1)
                    
                    try:
                        doc_temp.SetVariable("FILEDIA", 0)
                        doc_temp.SetVariable("CMDDIA", 0)
                    except: pass

                    print("     Отключаем рамки (через командную строку)...")
                    
                    # Нижнее подчеркивание (_) обязательно для русской локализации AutoCAD!
                    frame_commands = [
                        "_FRAME\n0\n",
                        "_IMAGEFRAME\n0\n",
                        "_PDFFRAME\n0\n",
                        "_WIPEOUTFRAME\n0\n",
                        "_XCLIPFRAME\n0\n"
                    ]
                    
                    # Отправляем команды как если бы вы печатали их на клавиатуре
                    for cmd in frame_commands:
                        try:
                            doc_temp.SendCommand(cmd)
                            # Даем Автокаду треть секунды, чтобы графический движок "проглотил" команду
                            time.sleep(0.3) 
                        except Exception as e:
                            print(f"     [!] Ошибка команды: {e}")
                    
                    # Принудительная регенерация ВООБЩЕ ВСЕХ листов и видовых экранов
                    try:
                        doc_temp.SendCommand("_REGENALL\n")
                        time.sleep(1)
                    except Exception:
                        pass
                        
                    # Сохраняем файл
                    try:
                        doc_temp.Save()
                    except Exception as e:
                        print(f"     [!] Ошибка сохранения: {e}")
                    
                    # Закрываем файл
                    doc_temp.Close(False)
                    time.sleep(1)  
                    
                    try:
                        os.replace(temp_dwg, dwg)
                        print(f"     Успешно! Рамки отключены.")
                    except Exception as e:
                        print(f"     [!] Ошибка при замене файла: {e}")
                else:
                    if temp_dwg.exists(): os.remove(temp_dwg)
                        
            except Exception as e:
                print(f"     [!] Сбой: {e}")
            finally:
                if doc:
                    try: doc.Close(False)
                    except: pass
            
            # Двигаем прогресс-бар после каждого чертежа
            if progress_cb: progress_cb()
            
    except Exception as e:
        print(f"[ФАТАЛЬНАЯ ОШИБКА] {e}")

    print(f"[DWG Optimizer] Готово.\n")
