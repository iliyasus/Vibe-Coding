from pathlib import Path
from datetime import datetime

def rename_files(folder_path):
    # Преобразуем строку в объект Path
    target_dir = Path(folder_path)
    
    if not target_dir.is_dir():
        print(f"Ошибка: Папка '{folder_path}' не найдена.")
        return

    # Получаем текущую дату в нужном формате
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Собираем только файлы (игнорируем папки), пропускаем скрытые (начинающиеся с точки)
    # И сразу сортируем их по имени, чтобы нумерация была стабильной
    files = sorted([
        f for f in target_dir.iterdir() 
        if f.is_file() and not f.name.startswith('.')
    ])

    if not files:
        print("Подходящих файлов для переименования не найдено.")
        return

    print(f"Начинаю переименование в папке: {target_dir.resolve()}\n")
    print("-" * 50)

    # Проходим по файлам с индексом (начинаем с 1)
    for index, file_path in enumerate(files, start=1):
        # Формируем порядковый номер (001, 002, ...)
        seq_num = f"{index:03d}"
        
        # Формируем новое имя
        old_name = file_path.name
        new_name = f"{date_str}_{seq_num}_{old_name}"
        new_path = file_path.with_name(new_name)
        
        # Проверка на существование файла с таким именем (чтобы не перезаписать)
        if new_path.exists():
            print(f"[ПРОПУСК] Файл '{new_name}' уже существует. Пропускаю '{old_name}'.")
            continue

        try:
            # Переименовываем
            file_path.rename(new_path)
            # Выводим в формате "было -> стало"
            print(f"{old_name} -> {new_name}")
        except OSError as e:
            print(f"[ОШИБКА] Не удалось переименовать '{old_name}': {e}")

    print("-" * 50)
    print("Готово!")

if __name__ == "__main__":
    # Укажите путь к вашей тестовой папке
    # Например: "C:/Users/User/Desktop/test_folder" или "./test_folder"
    test_folder_path = input("Введите путь к папке для переименования: ").strip()
    if test_folder_path:
        rename_files(test_folder_path)
    else:
        print("Путь не введен.")