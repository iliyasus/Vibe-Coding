class TipCalculator:
	"""Рассчитывает чаевые и итоговую сумму ресторанного счёта."""

	def __init__(self, bill_amount, tip_percent, people=1):
		self.bill_amount = bill_amount
		self.tip_percent = tip_percent
		self.people = people
		self.validate()

	def validate(self):
		if self.bill_amount < 0:
			raise ValueError("Сумма счёта не может быть отрицательной")
		if not 0 <= self.tip_percent <= 100:
			raise ValueError("Процент чаевых должен быть от 0 до 100")
		if not isinstance(self.people, int) or self.people <= 0:
			raise ValueError("Количество гостей должно быть положительным целым числом")

	def calculate_tip(self):
		return self.bill_amount * self.tip_percent / 100

	def total_amount(self):
		return self.bill_amount + self.calculate_tip()

	def amount_per_person(self):
		return self.total_amount() / self.people


if __name__ == "__main__":
	calculator = TipCalculator(2400, 15, 4)

	assert calculator.calculate_tip() == 360
	assert calculator.total_amount() == 2760
	assert calculator.amount_per_person() == 690

	print(f"Чаевые: {calculator.calculate_tip():.2f} руб.")
	print(f"Итого: {calculator.total_amount():.2f} руб.")
	print(f"С каждого гостя: {calculator.amount_per_person():.2f} руб.")

	try:
		TipCalculator(-100, 15)
	except ValueError as error:
		print("Проверка ошибки суммы:", error)

	try:
		TipCalculator(1000, 150)
	except ValueError as error:
		print("Проверка ошибки процента:", error)
