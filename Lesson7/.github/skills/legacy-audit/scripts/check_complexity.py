import ast
import sys
from pathlib import Path


def audit_file(filepath: str) -> None:
    path = Path(filepath)
    if not path.exists():
        print(f"[ERROR] Файл не найден: {filepath}")
        sys.exit(1)

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=filepath)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > 25:
                print(
                    f"[LENGTH] Строка {node.lineno}: функция '{node.name}' "
                    f"занимает {length} строк (макс. 25)"
                )
            if node.returns is None:
                print(
                    f"[TYPING] Строка {node.lineno}: у функции "
                    f"'{node.name}' нет аннотации возвращаемого типа"
                )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "print":
                print(f"[PRINT] Строка {node.lineno}: обнаружен вызов print()")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python check_complexity.py <путь_к_файлу>")
        sys.exit(1)
    audit_file(sys.argv[1])
