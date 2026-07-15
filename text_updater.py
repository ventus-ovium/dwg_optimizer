import os
import time
import win32com.client
import pythoncom

def update_text_in_dwgs(dwg_paths: list, old_text: str, new_text: str, progress_cb=None, status_cb=None, is_cancelled=None):
    print(f"\n[Text Updater] Запуск замены (на листах и в модели) '{old_text}' -> '{new_text}'...")
    
    try:
        pythoncom.CoInitialize()
        acad = win32com.client.dynamic.Dispatch("AutoCAD.Application")
        acad.Visible = True 
        time.sleep(2)
        
        total = len(dwg_paths)
        
        for i, dwg in enumerate(dwg_paths):
            if is_cancelled and is_cancelled():
                print("  [!] Получена команда остановки. Прерываем замену текста...")
                break
                
            if status_cb: status_cb(f"Замена текста [{i+1}/{total}]: {dwg.name}")
            print(f"  -> Ищем текст в: {dwg.name}")
            
            doc = None
            try:
                # Открываем чертеж
                doc = acad.Documents.Open(str(dwg), False)
                time.sleep(1)
                updated_count = 0

                #ПЕРЕБИРАЕМ МОДЕЛЬ И ЛИСТЫ
                for layout in doc.Layouts:
                    if is_cancelled and is_cancelled(): break
                    
                    block = layout.Block # Это контейнер объектов текущего листа/модели
                    for j in range(block.Count):
                        entity = block.Item(j)
                        
                        # Проверяем обычный Текст и МТекст
                        if entity.ObjectName in ["AcDbText", "AcDbMText"]:
                            # Получаем сырую строку (в МТексте могут быть скрытые теги)
                            raw_text = entity.TextString
                            
                            if old_text in raw_text:
                                try:
                                    # Меняем текст
                                    entity.TextString = raw_text.replace(old_text, new_text)
                                    entity.Update()
                                    updated_count += 1
                                except Exception as e:
                                    print(f"     [!] Не смог изменить текст: {e}")
                                    
                                
                if updated_count > 0:
                    print(f"     ✅ Заменено элементов: {updated_count} шт.")
                    # ЖЕСТКАЯ ПЕРЕРИСОВКА И СОХРАНЕНИЕ
                    doc.Regen(1)
                    doc.SendCommand("_QSAVE\n")
                    time.sleep(2) # Даем диску время на запись
                else:
                    print(f"     ➖ Совпадений не найдено.")
                    
            except Exception as e:
                print(f"     [!] Ошибка обработки {dwg.name}: {e}")
            finally:
                if doc:
                    try: doc.Close(False)
                    except: pass
            
            if progress_cb: progress_cb()
            
    except Exception as e:
        print(f"[ФАТАЛЬНАЯ ОШИБКА Text Updater] {e}")
