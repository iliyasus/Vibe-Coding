import random
import tkinter as tk
from tkinter import messagebox


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Snake Game")
        self.root.resizable(False, False)

        self.cell_size = 28
        self.grid_size = 12
        self.level = 1
        self.score = 0
        self.speed = 220
        self.game_over = False
        self.wrap_around = True

        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.body = [(5, 5), (4, 5), (3, 5)]
        self.food = self.spawn_food()

        self.canvas = tk.Canvas(
            root,
            width=self.grid_size * self.cell_size,
            height=self.grid_size * self.cell_size,
            bg="#0f172a",
            highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=10)

        self.info = tk.Label(
            root,
            text=f"Level: {self.level}   Score: {self.score}",
            font=("Arial", 14, "bold"),
            fg="#e2e8f0",
            bg="#111827",
        )
        self.info.pack(pady=(0, 10))

        self.root.bind("<KeyPress>", self.change_direction)
        self.root.focus_set()
        self.tick()

    def spawn_food(self):
        while True:
            x = random.randint(0, self.grid_size - 1)
            y = random.randint(0, self.grid_size - 1)
            if (x, y) not in self.body:
                return (x, y)

    def change_direction(self, event):
        if self.game_over:
            return

        key = event.keysym.lower()
        mapping = {
            "right": (1, 0),
            "left": (-1, 0),
            "up": (0, -1),
            "down": (0, 1),
            "d": (1, 0),
            "a": (-1, 0),
            "w": (0, -1),
            "s": (0, 1),
        }

        if key in mapping:
            new_dir = mapping[key]
            if (new_dir[0], new_dir[1]) != (-self.direction[0], -self.direction[1]):
                self.next_direction = new_dir

    def level_up(self):
        self.level += 1
        self.speed = max(80, self.speed - 18)
        self.grid_size += 1
        self.canvas.config(width=self.grid_size * self.cell_size, height=self.grid_size * self.cell_size)

        # "смена местами с хвостом" — визуальный эффект уровня
        self.body = list(reversed(self.body))
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.wrap_around = True
        self.food = self.spawn_food()

        self.info.config(text=f"Level: {self.level}   Score: {self.score}")

    def tick(self):
        if self.game_over:
            return

        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if self.wrap_around:
            new_head = (
                new_head[0] % self.grid_size,
                new_head[1] % self.grid_size,
            )
        else:
            if not (0 <= new_head[0] < self.grid_size and 0 <= new_head[1] < self.grid_size):
                self.game_over = True
                self.show_game_over()
                return

        if new_head in self.body[:-1]:
            self.game_over = True
            self.show_game_over()
            return

        self.body.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.food = self.spawn_food()
            if self.score % 3 == 0:
                self.level_up()
        else:
            self.body.pop()

        self.info.config(text=f"Level: {self.level}   Score: {self.score}")
        self.draw()
        self.root.after(self.speed, self.tick)

    def draw(self):
        self.canvas.delete("all")

        for x in range(self.grid_size):
            for y in range(self.grid_size):
                self.canvas.create_rectangle(
                    x * self.cell_size,
                    y * self.cell_size,
                    (x + 1) * self.cell_size,
                    (y + 1) * self.cell_size,
                    fill="#111827",
                    outline="#1f2937",
                    width=1,
                )

        fx, fy = self.food
        self.canvas.create_rectangle(
            fx * self.cell_size + 5,
            fy * self.cell_size + 5,
            (fx + 1) * self.cell_size - 5,
            (fy + 1) * self.cell_size - 5,
            fill="#f87171",
            outline="#ef4444",
            width=2,
        )

        for index, (x, y) in enumerate(self.body):
            color = "#4ade80" if index == 0 else "#22c55e"
            self.canvas.create_rectangle(
                x * self.cell_size + 2,
                y * self.cell_size + 2,
                (x + 1) * self.cell_size - 2,
                (y + 1) * self.cell_size - 2,
                fill=color,
                outline="#14532d",
                width=1,
            )

    def show_game_over(self):
        messagebox.showinfo("Игра окончена", f"Итоговый счёт: {self.score}\nУровень: {self.level}")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()
