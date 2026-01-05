# main.py
# Developer: Urban Egor
# Version: 3.5.46 b

import logging
import traceback

from WheelCounterApp import WheelCounterApp 


def show_menu():
    print("\n" + "="*50)
    print("  СИСТЕМА ОБНАРУЖЕНИЯ КОЛЁС")
    print("="*50)
    print("\nВыберите режим работы:")
    print("  1 - Обработка видеофайла")
    print("  2 - Обработка видео с камеры")
    print("  0 - Выход")
    print("="*50)
    
    while True:
        try:
            choice = input("\nВведите номер режима (0-2): ").strip()
            
            if choice in ['0', '1', '2']:
                return choice
            else:
                print("Ошибка: введите число 0, 1 или 2")
                
        except KeyboardInterrupt:
            print("\n\nПрограмма прервана пользователем")
            return '0'


def run_file_mode():
    print("\n--- РЕЖИМ: Обработка видеофайла ---")
    
    video_path = input("Введите путь к видеофайлу (Enter для 'assets/cars_passing_input.mp4'): ").strip()
    if not video_path:
        video_path = "assets/cars_passing_input.mp4"
    
    output_path = input("Введите путь для выходного файла (Enter для 'assets/outputcar.avi'): ").strip()
    if not output_path:
        output_path = "assets/outputcar.avi"
    
    print(f"\nЗапуск обработки файла: {video_path}")
    print(f"Результат будет сохранён в: {output_path}")
    print("Нажмите 'q' для остановки обработки\n")
    
    app = WheelCounterApp(video_path, output_path, mode='file')
    app.run()


def run_camera_mode():
    print("\n--- РЕЖИМ: Обработка видео с камеры ---")
    
    camera_id = input("Введите ID камеры (Enter для камеры по умолчанию 0): ").strip()
    if not camera_id:
        camera_id = 0
    else:
        try:
            camera_id = int(camera_id)
        except ValueError:
            print("Некорректный ID камеры, используется камера 0")
            camera_id = 0
    
    save_output = input("Сохранить видео? (y/n, Enter для 'n'): ").strip().lower()
    
    output_path = None
    if save_output == 'y':
        output_path = input("Введите путь для выходного файла (Enter для 'assets/camera_output.avi'): ").strip()
        if not output_path:
            output_path = "assets/camera_output.avi"
    
    print(f"\nЗапуск обработки с камеры ID: {camera_id}")
    if output_path:
        print(f"Результат будет сохранён в: {output_path}")
    print("Нажмите 'q' для остановки обработки\n")
    
    app = WheelCounterApp(camera_id, output_path, mode='camera')
    app.run()


if __name__ == "__main__":
    try:
        while True:
            choice = show_menu()
            
            if choice == '0':
                print("\nЗавершение работы программы...")
                break
                
            elif choice == '1':
                run_file_mode()
                
            elif choice == '2':
                run_camera_mode()
            
            continue_choice = input("\n\nВернуться в главное меню? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\nЗавершение работы программы...")
                break
        
    except Exception as e:
        logging.critical(f"Critical application error: {e}")
        logging.critical(traceback.format_exc())
    
    finally:
        print("\nПрограмма завершена.")