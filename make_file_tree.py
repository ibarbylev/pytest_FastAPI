"""Скрипт сканирует указанную директорию и создаёт дерево вида:
project_root/
│
├── pytest.ini           ← глобальные настройки pytest
├── conftest.py          ← общие фикстуры (user, product_factory, make_order и т.д.)
│
├── users/
│   ├── models.py
│   ├── views.py
│   └── tests/
│       ├── test_user_profile.py
│       └── test_user_token.py
│
├── shop/
│   ├── models.py
│   ├── views.py
│   └── tests/
│       ├── test_product.py
│       ├── test_order.py
│       ├── test_payment.py
│       ├── test_review.py
│       └── test_signals_and_jobs.py
"""


import os

ALLOWED_EXTENSIONS = {".py", ".ini", ".txt"}   # ← Укажи нужные расширения


def is_allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS


def tree(path, prefix=""):
    entries = []

    # Фильтруем: скрытые папки и файлы не берём
    for entry in sorted(os.listdir(path)):
        if entry.startswith('.'):
            continue

        full_path = os.path.join(path, entry)

        if os.path.isdir(full_path):
            entries.append((entry, True, full_path))
        elif os.path.isfile(full_path) and is_allowed_file(entry):
            entries.append((entry, False, full_path))

    for index, (name, is_dir, full_path) in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "

        print(prefix + connector + name)

        if is_dir:
            new_prefix = prefix + ("    " if index == len(entries) - 1 else "│   ")
            tree(full_path, new_prefix)


if __name__ == "__main__":
    root = os.getcwd()
    print(os.path.basename(root) + "/")
    tree(root)
