# -*- coding: utf-8 -*-

import re
import unittest
import statistic
# для статиски - статистика для слова "en_to_ru" йде в словарі під ключом "en_to_ru"
en_to_ru_write = "en_to_ru"
# для статиски - статистика для слова "ru_to_en" йде в словарі під ключом "ru_to_en"
ru_to_en_write = "ru_to_en"

# якщо в дужках немає | - то це коментарій
reg_comment = re.compile("\([^|]*?\)")
# регулярка для заміни виразу в {}
reg_no_curly_bracket_part = re.compile("\{.*?\}")
# регулярка для розбиття строки слова на підстроки (по комі)
reg_split = re.compile("((?:\(.*?\)|[^,])*)")

# те що в дужках із знаком | - остається - працює як (a|b) - a або b


class WordInfo:
    def __init__(self, word, transcription):
        self.word = word
        self.transcription = transcription

    def __eq__(self, other):
        return self.word == other.word and self.transcription == other.transcription


class Word:
    """ Хранение информации по одному слову:
        английский вариант, перевод, транскрипция + статистика и рейтинг
        Умеет:
        -парсить сырые данные (те, что сохранены в словаре) во внутренний формат
        -проверять правильность ответа и в зависимости от результата обновлять статистику
        -сериализовать/десериализовать статистику по слову
    """

    def __init__(self):
        # Английское слово, которое будет отображаться пользователю
        self.en_word = ""
        # Исходное английское слово, без преобразований
        self.en_source = ""
        # Распарсенное английское слово
        self.en_word_list = []
        # Транскрипция
        self.transcription = ""
        # Массив русских слов, без преобразований
        self.ru_source = []
        # Русское слово, которое будет отображаться пользователю
        self.ru_word = ""
        # Распарсенное русское слово
        self.ru_word_list = []
        # Рейтинг слова, влияет на вероятность появления его в упражнении
        self.rating = 0
        # Ссылка на статистику по слову
        self.stat = {en_to_ru_write: statistic.Statistic(), ru_to_en_write: statistic.Statistic()}
        # Название словаря в котором находиться слово
        self.dictionary_name = ""

    @staticmethod
    def _convert_spec_chars(s):
        return s.replace(u"ё", u"е")

    @staticmethod
    def _prepare_show_words(word_list):
        filtered_list = []
        norm_list = []
        for it in map(lambda x: x.replace("{", "").replace("}", ""), word_list):
            norm_word = Word._convert_spec_chars(it.lower())
            if norm_word not in norm_list:
                norm_list.append(norm_word)
                filtered_list.append(it)
        return ", ".join(filtered_list)

    def add_value(self, en_word, transcription, ru_word, dictionary_name):
        def prepare_word(w):
            # парситься слово при зчитуванні з словника
            # (замніяються круглі дужки на "", потім заміняються квадратні дужки на регулярку .*?)
            prepared = reg_no_curly_bracket_part.sub(".*?", reg_comment.sub("", w.lower()).strip())
            # print(prepared)
            return prepared

        # розділяє строку по шаблону на окремі слова
        def split(w):
            return [it.strip() for it in reg_split.split(w) if it.strip() not in (",", "")]

        if self.en_word == "":
            self.en_source = en_word
            en_split = split(en_word)
            self.en_word = Word._prepare_show_words(en_split)
            self.en_word_list = map(lambda x: prepare_word(x), en_split)
        if self.transcription == "" and transcription is not None and transcription.strip() != "":
            self.transcription = "[%s]" % transcription.strip()
        self.ru_source += split(ru_word)

        self.ru_word = Word._prepare_show_words(self.ru_source)
        self.ru_word_list = map(lambda x: Word._convert_spec_chars(prepare_word(x)), self.ru_source)

        self.dictionary_name = dictionary_name

    def rename(self, en_word, transcription, ru_word):
        "Переименовать слово, не касаясь статистики, рейтинга и др. служебных данных"
        self.en_word = ""
        self.en_word_list = []
        self.transcription = ""
        self.ru_source = []
        self.ru_word = ""
        self.ru_word_list = []
        self.add_value(en_word, transcription, ru_word)

    def set_rating(self, value):
        self.rating = value

    def get_rating(self):
        return self.rating

    def question_data(self, type_pr):
        "Получение отображаемых в вопросе данных по слову"
        if type_pr == en_to_ru_write:
            return WordInfo(self.en_word, self.transcription)

        return WordInfo(self.ru_word, "")

    def is_new(self, type_pr):
        "Возвращает True, если слово еще не изучалось"
        return self.stat[type_pr].is_new()

    def _check_ru(self, answer):
        answer = Word._convert_spec_chars(answer)
        for it in self.ru_word_list:
            # print(it, answer)
            # print(re.match(it + "\Z", answer))
            if re.match(it + "\Z", answer) is not None:
                return True
        return False

    def _check_en(self, answer):
        for it in self.en_word_list:
            # print(it, answer)
            # print(re.match(it + "\Z", answer))
            if re.match(it + "\Z", answer) is not None:
                return True
        return False

# перевірка результату вводу слова
    def check(self, answer, type_pr):
        answer = answer.strip().lower()
        if type_pr == en_to_ru_write:
            is_success = self._check_ru(answer)
            return is_success, WordInfo(self.ru_word, "")
        else:
            is_success = self._check_en(answer)
            return is_success, WordInfo(self.en_word, self.transcription)

    def update_stat(self, is_success, add_percent, type_pr):
        self.stat[type_pr].update(is_success, add_percent)

    def get_show_info(self):
        "Отображаемая информация в глобальной статистике по слову"
        return (self.en_word, self.transcription, self.ru_word)

    def get_source_info(self):
        "Исходные данные слова, наиболее приближенные к виду в словаре"
        s = set()
        s_add = s.add
        # убираем из self.ru_source неуникальные элементы, сохраняя порядок
        ru_source = ", ".join([x for x in self.ru_source if x not in s and not s_add(x)])
        return (self.en_source, self.transcription.strip("[]"), ru_source)

    def is_load(self):
        return self.en_word != ""

    def get_stat(self, type_pr):
        return self.stat[type_pr]

    def get_dictionary_name(self):
        return self.dictionary_name

# Скоригував - розпаковує статистику для даного слова
    def unpack(self, word_statistics, statistic_name):
        for word in word_statistics:
            if word not in self.stat.keys():
                self.stat[word] = statistic.Statistic()
            self.stat[word].unpack(word_statistics[word], statistic_name)

# запаковує статистику для даного слова
    def pack(self):
        data = {}
        for it in self.stat:
            data[it] = self.stat[it].pack()
        return data

