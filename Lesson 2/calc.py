def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Деление на ноль невозможно")
    return a / b

def main():
    print("--- Консольный калькулятор ---")
    try:
        a = float(input("Введите первое число: "))
        op = input("Введите операцию (+, -, *, /): ")
        b = float(input("Введите второе число: "))
        
        if op == '+':
            print(f"Результат: {add(a, b)}")
        elif op == '-':
            print(f"Результат: {subtract(a, b)}")
        elif op == '*':
            print(f"Результат: {multiply(a, b)}")
        elif op == '/':
            print(f"Результат: {divide(a, b)}")
        else:
            print("Неверная операция!")
    except ZeroDivisionError as e:
        print(f"Ошибка: {e}")
    except ValueError:
        print("Ошибка: Введены некорректные числа")

if __name__ == "__main__":
    main()
