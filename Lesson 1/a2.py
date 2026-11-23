import tkinter as tk
from tkinter import messagebox


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Мой Список Задач")
        self.root.geometry("450x500")
        self.root.configure(bg="#f4f4f6")  # Светлый нейтральный фон

        # Настройка шрифтов
        self.title_font = ("Helvetica", 18, "bold")
        self.item_font = ("Helvetica", 12)

        # 1. Заголовок
        self.title_label = tk.Label(
            root, 
            text="Планы на сегодня 🚀", 
            font=self.title_font, 
            bg="#f4f4f6", 
            fg="#2c3e50"
        )
        self.title_label.pack(pady=20)

        # 2. Фрейм для ввода новой задачи
        self.input_frame = tk.Frame(root, bg="#f4f4f6")
        self.input_frame.pack(pady=10, padx=20, fill="x")

        self.task_entry = tk.Entry(
            self.input_frame, 
            font=self.item_font, 
            bg="white", 
            fg="#333333", 
            relief="flat", 
            bd=5
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.task_entry.bind("<Return>", lambda event: self.add_task())

        self.add_button = tk.Button(
            self.input_frame, 
            text="Добавить", 
            font=("Helvetica", 11, "bold"),
            bg="#3498db", 
            fg="white", 
            relief="flat", 
            activebackground="#2980b9", 
            activeforeground="white",
            padx=15, 
            pady=5,
            command=self.add_task
        )
        self.add_button.pack(side="right")

        # 3. Список задач с прокруткой (Listbox + Scrollbar)
        self.tasks_frame = tk.Frame(root, bg="#f4f4f6")
        self.tasks_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.tasks_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.tasks_listbox = tk.Listbox(
            self.tasks_frame, 
            font=self.item_font, 
            bg="white", 
            fg="#2c3e50", 
            selectbackground="#e0e0e0", 
            selectforeground="#2c3e50",
            relief="flat", 
            bd=5,
            yscrollcommand=self.scrollbar.set
        )
        self.tasks_listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.tasks_listbox.yview)

        # 4. Кнопка удаления выделенной задачи
        self.delete_button = tk.Button(
            root, 
            text="Удалить выбранную задачу ✕", 
            font=("Helvetica", 11),
            bg="#e74c3c", 
            fg="white", 
            relief="flat", 
            activebackground="#c0392b", 
            activeforeground="white",
            pady=8,
            command=self.delete_task
        )
        self.delete_button.pack(pady=20, padx=20, fill="x")

    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text:
            # Добавляем задачу в конец списка (форматируем в красивую строчку)
            self.tasks_listbox.insert(tk.END, f" 📋  {task_text}")
            self.task_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Внимание", "Нельзя добавить пустую задачу!")

    def delete_task(self):
        try:
            # Получаем индекс выбранного элемента
            selected_index = self.tasks_listbox.curselection()[0]
            # Удаляем его
            self.tasks_listbox.delete(selected_index)
        except IndexError:
            # Если пользователь ничего не выбрал перед нажатием кнопки
            messagebox.showwarning("Внимание", "Сначала выберите задачу для удаления!")

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
