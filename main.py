import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod

from typing import List


# Абстрактный класс для расчёта графика платежей
class PaymentCalculator(ABC):
    @abstractmethod
    def calculate_schedule(self, amount: float, months: int, rate: float) -> List[dict]:
        pass

# Реализация для дифференцированного платежа
class DifferentiatedPaymentCalculator(PaymentCalculator):
    def calculate_schedule(self, amount: float, months: int, rate: float) -> List[dict]:
        schedule = []
        remaining = amount
        for month in range(1, months + 1):
            principal_payment = amount / months
            interest_payment = remaining * rate
            total_payment = principal_payment + interest_payment
            remaining -= principal_payment
            schedule.append({
                'month': month,
                'principal': round(principal_payment, 2),
                'interest': round(interest_payment, 2),
                'total': round(total_payment, 2),
                'remaining': round(remaining, 2)
            })
        return schedule

# Класс для работы с базой данных (инкапсуляция)
class RateDatabase:
    def __init__(self, db_name: str = 'credit.db'):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rates (
                    id INTEGER PRIMARY KEY,
                    rate REAL NOT NULL
                )
            ''')
            cursor.execute('SELECT COUNT(*) FROM rates')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO rates (rate) VALUES (0.02)')

    def get_rate(self) -> float:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT rate FROM rates ORDER BY id DESC LIMIT 1')
            return cursor.fetchone()[0]

# Класс Аннуитетного платежа (Полиморфизм)
class AnnuityPaymentCalculator(PaymentCalculator):
    def calculate_schedule(self, amount: float, months: int, rate: float) -> List[dict]:
        schedule = []
        remaining = amount
        monthly_rate = rate
        annuity_payment = amount * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)

        for month in range(1, months + 1):
            interest_payment = remaining * monthly_rate
            principal_payment = annuity_payment - interest_payment
            remaining -= principal_payment
            schedule.append({
                'month': month,
                'principal': round(principal_payment, 2),
                'interest': round(interest_payment, 2),
                'total': round(annuity_payment, 2),
                'remaining': round(remaining, 2)
            })
        return schedule

# Класс для GUI (наследование от tk.Tk)
class CreditCalculatorApp(tk.Tk):
    def __init__(self, rate_db: RateDatabase):
        super().__init__()
        self.title("Калькулятор кредита")
        self.rate_db = rate_db
        self.calculator = DifferentiatedPaymentCalculator()  # по умолчанию
        self._create_widgets()

    def _create_widgets(self):
        # Переключатель типа платежа
        self.payment_type = tk.StringVar(value="differentiated")
        tk.Radiobutton(self, text="Дифференцированный", variable=self.payment_type, value="differentiated", command=self._update_calculator).grid(row=0, column=0, padx=5, pady=5)
        tk.Radiobutton(self, text="Аннуитетный", variable=self.payment_type, value="annuity", command=self._update_calculator).grid(row=0, column=1, padx=5, pady=5)

        # Поля ввода
        tk.Label(self, text="Сумма кредита:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_amount = tk.Entry(self)
        self.entry_amount.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self, text="Срок (месяцев):").grid(row=2, column=0, padx=5, pady=5)
        self.entry_months = tk.Entry(self)
        self.entry_months.grid(row=2, column=1, padx=5, pady=5)

        # Кнопка расчета
        btn_calculate = tk.Button(self, text="Рассчитать", command=self.show_schedule)
        btn_calculate.grid(row=3, column=0, columnspan=2, pady=10)

        # Таблица с графиком
        columns = ('month', 'principal', 'interest', 'total', 'remaining')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
        self.tree.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

    def _update_calculator(self):
        if self.payment_type.get() == "annuity":
            self.calculator = AnnuityPaymentCalculator()
        else:
            self.calculator = DifferentiatedPaymentCalculator()

    def show_schedule(self):
        try:
            amount = float(self.entry_amount.get())
            months = int(self.entry_months.get())
            rate = self.rate_db.get_rate()
            schedule = self.calculator.calculate_schedule(amount, months, rate)

            # Очищаем таблицу
            for row in self.tree.get_children():
                self.tree.delete(row)
            # Заполняем таблицу
            for item in schedule:
                self.tree.insert('', 'end', values=(
                    item['month'],
                    item['principal'],
                    item['interest'],
                    item['total'],
                    item['remaining']
                ))
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректные данные")

#Запуск приложения
if __name__ == "__main__":
    rate_db = RateDatabase()
    app = CreditCalculatorApp(rate_db)
    app.mainloop()
