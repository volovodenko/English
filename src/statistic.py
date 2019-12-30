# -*- coding: utf-8 -*-

import math
import datetime
import unittest


class Statistic:
    """ Хранение статистики по одному типу упражнения у слова
        Умеет:
        -расчитывать рейтинг слова
        -сериализовать/десериализовать свои данные
    """

    def __init__(self):
        self.success_answer = 0  # Кол-во правильных ответов
        self.error_answer = 0  # Кол-во ошибочных ответов
        self.last_lesson_date = None  # Дата последнего ответа
        self.last_lesson_result = None  # Результат последнего ответа
        self.study_percent = 0  # Процент изучения [0; 100]

    def __repr__(self):
        return ("Statistic(success_answer = {0}; "
                + "error_answer = {1}; "
                + "last_lesson_date = {2}; "
                + "last_lesson_result = {3}; "
                + "study_percent={4})").format(self.success_answer,
                                               self.error_answer,
                                               self.last_lesson_date,
                                               self.last_lesson_result,
                                               self.study_percent)

    def __eq__(self, other):
        return (self.success_answer == other.success_answer and
                self.error_answer == other.error_answer and
                self.last_lesson_date == other.last_lesson_date and
                self.last_lesson_result == other.last_lesson_result and
                self.study_percent == other.study_percent)

    def get_total_answer(self):
        return self.success_answer + self.error_answer

    def get_success_answer(self):
        return self.success_answer

    def get_success_percent(self):
        total = self.get_total_answer()
        if total > 0:
            return float(self.success_answer) / total * 100.0
        else:
            return 0.0

    def get_study_percent(self):
        return self.study_percent

    def is_new(self):
        return self.get_total_answer() == 0

    def get_last_lesson_date(self):
        return self.last_lesson_date

    def calc_rating(self):
        perc = self.get_success_percent()

        # Базовый рейтинг от 1 до 101
        rating = 101.0 - self.get_study_percent()
        # чем больше процент не правильных ответов, тем выше рейтинг
        rating *= (1.01 - min(max(perc / 100.0, 0.0), 1.0))
        # чем чаще слово повторяли, тем меньше рейтинг
        rating *= math.exp(-self.get_total_answer() * 0.07)
        # если последний ответ был неправильным увеличиваем рейтинг
        if not self.last_lesson_result:
            rating *= 1.5
        # чем дольше слово не повторяли, тем выше рейтинг
        days = 0
        if self.last_lesson_date is not None:
            days = (datetime.date.today() - datetime.datetime.strptime(self.last_lesson_date, "%Y.%m.%d").date()).days
        rating *= math.log10(days + 1.0) + 1.0

        return max(rating, 0.1)

    def update(self, is_success, add_percent):
        self.last_lesson_date = datetime.date.today().strftime("%Y.%m.%d")
        self.last_lesson_result = is_success
        self.study_percent = max(min(self.study_percent + add_percent, 100), 0)
        if is_success:
            self.success_answer += 1
        else:
            self.error_answer += 1

    # розпаковка даних статистики для даного слова,  даного напрямку перекладу
    def unpack(self, statistic):
        # лямбда для деструктуризації словаря
        pluck = lambda dict, *args: (dict[arg] for arg in args)

        (self.success_answer,
         self.error_answer,
         self.last_lesson_date,
         self.last_lesson_result,
         self.study_percent) = statistic
        # в statistic список(массив) статистики для слова
        # pluck(statistic, 'success_answer', 'error_answer', 'last_lesson_date', 'last_lesson_result', 'study_percent')

    # упаковка даних статистики в список(масив) для даного слова,  даного напрямку перекладу
    def pack(self):
        return [
            self.success_answer,
            self.error_answer,
            self.last_lesson_date,
            self.last_lesson_result,
            self.study_percent
            ]

        # {
        #     'success_answer': self.success_answer,
        #     'error_answer': self.error_answer,
        #     'last_lesson_date': self.last_lesson_date,
        #     'last_lesson_result': self.last_lesson_result,
        #     'study_percent': self.study_percent
        # }
