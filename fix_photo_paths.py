#!/usr/bin/env python3
"""
Скрипт для исправления путей к фотографиям в базе данных.
Заменяет абсолютные пути на имена файлов.
"""

import sqlite3
import os

def fix_photo_paths():
    db_path = "instance/app.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Получаем все фотографии
        cursor.execute("SELECT id, file_path FROM photo")
        photos = cursor.fetchall()
        
        print(f"Найдено {len(photos)} фотографий для обновления")
        
        for photo_id, file_path in photos:
            print(f"ID {photo_id}: {file_path}")
            
            # Если путь абсолютный, извлекаем только имя файла
            if os.path.isabs(file_path):
                filename = os.path.basename(file_path)
                print(f"  → Обновляем на: {filename}")
                
                # Обновляем запись
                cursor.execute("UPDATE photo SET file_path = ? WHERE id = ?", (filename, photo_id))
            else:
                print(f"  → Уже корректный: {file_path}")
        
        # Сохраняем изменения
        conn.commit()
        print("✅ Пути к фотографиям успешно исправлены!")
        
        # Проверяем результат
        cursor.execute("SELECT id, file_path FROM photo")
        updated_photos = cursor.fetchall()
        
        print("\nОбновленные пути:")
        for photo_id, file_path in updated_photos:
            print(f"ID {photo_id}: {file_path}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_photo_paths()