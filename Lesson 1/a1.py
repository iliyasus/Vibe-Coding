import re


def get_email_validation_errors(email: str) -> list[str]:
    """
    Проверяет email и возвращает список причин, почему он невалиден.
    Если список пустой [], значит email корректен.
    """
    errors = []

    if not isinstance(email, str):
        return ["Входные данные должны быть строкой"]
    
    email_clean = email.strip()
    
    if not email_clean:
        return ["Email-адрес не может быть пустым"]

    if " " in email_clean:
        errors.append("Email не должен содержать пробелов внутри")

    if "@" not in email_clean:
        errors.append("Отсутствует символ '@'")
    elif email_clean.count("@") > 1:
        errors.append("Символ '@' должен быть только один")
    else:
        local_part, domain_part = email_clean.split("@", 1)

        # Проверка локальной части (до @)
        if not local_part:
            errors.append("Отсутствует имя пользователя перед знаком '@'")
        elif not re.match(r"^[a-zA-Z0-9_.+-]+$", local_part):
            errors.append("Имя пользователя содержит недопустимые символы (разрешены латиница, цифры и . _ - +)")

        # Проверка доменной части (после @)
        if not domain_part:
            errors.append("Отсутствует домен после знака '@'")
        else:
            if "." not in domain_part:
                errors.append("В домене отсутствует точка (например, должно быть .com, .ru)")
            elif domain_part.startswith(".") or domain_part.endswith("."):
                errors.append("Домен не может начинаться или заканчиваться на точку")
            elif ".." in domain_part:
                errors.append("Домен не может содержать две точки подряд")
            
            if not re.match(r"^[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", domain_part):
                errors.append("Домен содержит недопустимые символы или неверный формат")

    return errors

# --- ЭТОТ БЛОК ВЫПОЛНИТСЯ ПРИ ЗАПУСКЕ ФАЙЛА ---
if __name__ == "__main__":
    # Список тестовых адресов для демонстрации работы
    test_emails = [
        "valid.user@example.com",
        "  ",
        "no_at_symbol.com",
        "user@no_dot_domain",
        "double@@gmail.com",
        "bad_user name@domain.ru",
        "alex@domain..com",
        "ivan@кириллица.рф"
    ]
    
    print("=" * 60)
    print(" РЕЗУЛЬТАТЫ ВАЛИДАЦИИ EMAIL: ")
    print("=" * 60)
    
    for email in test_emails:
        errors = get_email_validation_errors(email)
        # Отображаем пробелы в выводе, чтобы было видно пустые строки
        display_name = f"'{email}'" if email.strip() else f"'{email}' (пустая строка/пробелы)"
        
        if not errors:
            print(f"✅ {display_name:<35} -> Валиден")
        else:
            print(f"❌ {display_name:<35} -> Невалиден. Причины:")
            for error in errors:
                print(f"    • {error}")
        print("-" * 60)
