class Quest:
    """Квест по поиску древнего кристалла в заброшенном храме."""

    def __init__(self, title, objectives, reward):
        self.title = title
        self.objectives = list(objectives)
        self.reward = reward
        self.completed_objectives = []
        self.state = "not_started"
        self.reward_received = False

    def start_quest(self):
        if self.state != "not_started":
            raise RuntimeError("Квест уже был начат")

        self.state = "in_progress"

    def complete_objective(self, objective):
        if self.state != "in_progress":
            raise RuntimeError("Сначала нужно начать квест")
        if objective not in self.objectives:
            raise ValueError("Такой цели нет в квесте")
        if objective in self.completed_objectives:
            raise ValueError("Эта цель уже выполнена")

        self.completed_objectives.append(objective)
        if len(self.completed_objectives) == len(self.objectives):
            self.state = "completed"

    def reward_player(self):
        if self.state != "completed":
            raise RuntimeError("Нельзя получить награду до завершения квеста")
        if self.reward_received:
            raise RuntimeError("Награда уже получена")

        self.reward_received = True
        self.state = "rewarded"
        return self.reward

    def get_status(self):
        return {
            "title": self.title,
            "state": self.state,
            "completed": len(self.completed_objectives),
            "total": len(self.objectives),
        }

class WordleGame:
    """Мини-игра Wordle: угадать слово по цветным подсказкам."""

    def __init__(self, answer):
        if not answer.isalpha():
            raise ValueError("Загаданное слово должно состоять только из букв")

        self.answer = answer.upper()
        self.attempts = []

    def guess(self, word):
        word = word.upper()
        if len(word) != len(self.answer):
            raise ValueError("Попытка должна быть такой же длины, как загаданное слово")
        if not word.isalpha():
            raise ValueError("Попытка должна состоять только из букв")

        feedback = self.get_feedback(word)
        self.attempts.append((word, feedback))
        return feedback

    def get_feedback(self, word):
        word = word.upper()
        feedback = ["gray"] * len(self.answer)
        remaining_letters = {}

        for index, letter in enumerate(self.answer):
            if letter != word[index]:
                remaining_letters[letter] = remaining_letters.get(letter, 0) + 1

        for index, letter in enumerate(word):
            if letter == self.answer[index]:
                feedback[index] = "green"

        for index, letter in enumerate(word):
            if feedback[index] == "green":
                continue
            if remaining_letters.get(letter, 0) > 0:
                feedback[index] = "yellow"
                remaining_letters[letter] -= 1

        return feedback

    def is_won(self):
        return bool(self.attempts) and self.attempts[-1][0] == self.answer


if __name__ == "__main__":
    quest = Quest(
        "Кристалл заброшенного храма",
        ["найти карту", "открыть тайную дверь", "забрать кристалл"],
        "100 золотых и редкий амулет",
    )

    assert quest.state == "not_started"
    print("1. До начала:", quest.get_status())

    quest.start_quest()
    assert quest.state == "in_progress"
    print("2. После старта:", quest.get_status())

    for objective in quest.objectives:
        quest.complete_objective(objective)
        print(f"3. Выполнена цель '{objective}':", quest.get_status())

    assert quest.state == "completed"
    received_reward = quest.reward_player()
    assert quest.state == "rewarded"
    print("4. После выдачи награды:", quest.get_status())
    print("Награда:", received_reward)

    wordle = WordleGame("APPLE")
    first_feedback = wordle.guess("ALLEY")
    assert first_feedback == ["green", "yellow", "gray", "yellow", "gray"]
    assert not wordle.is_won()
    print("Wordle, ALLEY:", first_feedback)

    second_feedback = wordle.guess("APPLE")
    assert second_feedback == ["green"] * 5
    assert wordle.is_won()
    print("Wordle, APPLE:", second_feedback)
    print("Партия завершена победой!")
