# -*- coding: utf-8 -*-

import os
import os.path
import json
# import json.encoder
import word
import global_stat
import unittest
import codecs
import re
import datetime

reg_comments = re.compile(r"/\*.*?\*/", re.DOTALL)


class ErrDict(Exception):
    def __init__(self, value, loc_res_msg):
        self.value = value
        self.loc_res_msg = loc_res_msg

    def __str__(self):
        return repr(self.value)


def statistic_v1_to_v2(data, min_percent, min_success_cnt):
    def calc_percent(success_answer, error_answer):
        if success_answer == 0:
            return 0.0
        else:
            multiplier = 1.0 if success_answer >= min_success_cnt else 0.9
            cnt = (success_answer if success_answer >= min_success_cnt else min_success_cnt) + error_answer
            abs_percent = float(success_answer) / float(cnt) * 100.0
            percent = abs_percent / min_percent if min_percent > 0 else 1.0
            return min(percent, multiplier) * 100.0

    min_success_cnt = max(min_success_cnt, 10)
    for it_word in data.values():
        for stat_key in it_word:
            success_answer = it_word[stat_key][0]
            error_answer = it_word[stat_key][1]
            it_word[stat_key].append(calc_percent(success_answer, error_answer))
    return data


class DictJSONEncoder(json.JSONEncoder):

    def __init__(self, skipkeys, ensure_ascii, check_circular, allow_nan, indent, separators, encoding, default):
        json.JSONEncoder.__init__(self, skipkeys=False, ensure_ascii=False, check_circular=False,
                                  allow_nan=True,
                                  sort_keys=False, indent=4, separators=(", ", ": "), encoding="utf-8",
                                  default=None)

    def _iterencode_list_lvl2(self, lst, max_len_lst):
        if len(lst) not in (2, 3):
            return "[]"

        if len(lst) == 2:
            sp_len0 = max_len_lst[0] + max_len_lst[1] - len(lst[0]) + 3
            arr = [lst[0], " " * sp_len0 + lst[1]]
        else:
            sp_len0 = max_len_lst[0] - len(lst[0]) + 1
            sp_len1 = max_len_lst[1] - len(lst[1]) + 1
            arr = [lst[0],
                   " " * sp_len0 + lst[1],
                   " " * sp_len1 + lst[2]]

        return "[%s]" % ",".join(arr)

    def iterencode(self, lst):
        if not lst:
            yield "[]"
            return

        self.current_indent_level = 1
        newline_indent = "\n    "
        separator = "," + newline_indent

        max_len_lst = [0, 0]
        str_lst = map(lambda row: [json.encoder.encode_basestring(it) for it in row if it.strip() != ""], lst)
        for row in str_lst:
            max_len_lst[0] = max(max_len_lst[0], len(row[0]))
            if len(row) == 3:
                max_len_lst[1] = max(max_len_lst[1], len(row[1]))

        yield "[" + newline_indent

        first = True
        for value in str_lst:
            if first:
                first = False
            else:
                yield separator
            yield self._iterencode_list_lvl2(value, max_len_lst)

        yield "\n]"


class Dict:
    def __init__(self, cfg):
        self.words = {}
        self.type_pr = None
        self.cfg = cfg
        self.dictionary_file_names = []

    def get_word_by_key(self, en):
        w = self.words.get(en)

        if not w:
            w = self.words[en] = word.Word()

        return w

    # Fixed
    def reload_dict_from_json(self, dictionary_data, dictionary_name):
        for current_word in dictionary_data:
            if len(current_word) == 3:
                en, tr, ru = current_word
            else:
                en, ru = current_word
                tr = ""
            self.get_word_by_key(en).add_value(en, tr, ru, dictionary_name)

    # Fixed
    def load_dictionary_as_json(self, path):
        txt = open(path).read()
        txt = reg_comments.sub("", txt)  # remove comments

        try:
            return json.loads(txt)
        except ValueError as e:
            print("error at", e)
            return None

    # Fixed
    def reload_dict(self, path_to_dictionaries_folder):
        self.words = {}
        self.dictionary_file_names = self.get_files_from_folder(path_to_dictionaries_folder)

        for file_name in self.dictionary_file_names:
            self.reload_dict_from_json(
                self.load_dictionary_as_json(os.path.join(path_to_dictionaries_folder, file_name)),
                file_name
            )

    def save_dict(self, path, json_dict):
        json.dump(json_dict, codecs.open(path, "w", "utf-8"), cls=DictJSONEncoder)

    def make_json_from_dict(self, keys):
        if keys is None:
            keys = self.words.keys()
        words = [self.words.get(key, None) for key in keys]
        return [list(w.get_source_info()) for w in words if w]

    # Fixed
    # обробка даних файла статистики
    def _reload_stat_from_json(self, json_stat, statistic_name):
        self.type_pr = json_stat["type"]
        statistics = json_stat["data"]

        for en_word_key in statistics:
            self.get_word_by_key(en_word_key).unpack(statistics[en_word_key], statistic_name)

    # Fixed
    # загрузка даних з файла статистики
    def reload_stat(self, path_to_statistics_folder):
        for file_name in self.dictionary_file_names:
            file_path = os.path.join(path_to_statistics_folder, file_name)

            if not os.path.isfile(file_path):
                self.create_empty_statistics_file(file_path)

            self._reload_stat_from_json(
                self.load_dictionary_as_json(file_path),
                file_name
            )

    def can_include_file(self, file_name):
        current_dictionaries = self.cfg["current_learning_dictionaries"]

        return (len(current_dictionaries) and file_name in current_dictionaries) or not len(current_dictionaries)

    def get_files_from_folder(self, folder_name):
        return [
            f for f in os.listdir(folder_name)
            if (os.path.isfile(os.path.join(folder_name, f)) and f.endswith('.json5')) and self.can_include_file(f)
        ]

    # збереження статистики в файл
    def save_stat(self, path):
        data = {}
        for en_word in self.words:
            dictionary_name = self.words[en_word].get_dictionary_name()

            if dictionary_name not in data:
                data[dictionary_name] = {}

            data[dictionary_name][en_word] = self.words[en_word].pack()

        # кожно разу міняю тип вивчення (en-ru, ru-en) на протилежний
        # раніше було рандомно - так погано працює - багато разів може вибрати одне й те саме
        if self.type_pr == word.en_to_ru_write:
            type_pr = word.ru_to_en_write
        else:
            type_pr = word.en_to_ru_write

        for dictionary_name in data:
            stat_json = {"data": data[dictionary_name], "type": type_pr}
            # indent=2 - 2 символа відступів в файлі
            json.dump(stat_json, open(os.path.join(self.cfg["path_to_statistics_folder"], dictionary_name), "wb"),
                      indent=2, sort_keys=True)

    @staticmethod
    def create_empty_statistics_file(file_path):
        stat_json = {"data": {}, "type": word.ru_to_en_write}
        json.dump(stat_json, open(file_path, "wb"), indent=2, sort_keys=True)

    def global_statistic(self):
        stat = global_stat.GlobalStatistic()
        for it in self.words.values():
            if it.is_load():
                stat.add_word(it, it.get_stat(word.en_to_ru_write), it.get_stat(word.ru_to_en_write))
        return stat

    def _rename_check(self, old_en, new_en, new_ru):
        if len(new_en) == 0:
            raise ErrDict("Error word is empty", "err_en_word_empty")

        if len(new_ru) == 0:
            raise ErrDict("Error word is empty", "err_ru_word_empty")

        if old_en not in self.words.keys():
            raise ErrDict("Error find word", "err_find_en_word")

        new_en = new_en.lower()
        if old_en.strip().lower() != new_en:
            if new_en in map(lambda x: x.strip().lower(), self.words.keys()):
                raise ErrDict("Dublicate in load dict", "err_dublicate_en_word")

    def _rename_in_json_dict(self, old_en, new_en, new_tr, new_ru, json_dict):
        is_find = False
        old_en = old_en.strip().lower()
        lower_en = new_en.lower()
        for it in json_dict:
            en = it[0].strip().lower()
            if en == old_en:
                if len(it) == 2:
                    it.append("")
                it[0], it[1], it[2] = new_en, new_tr, new_ru
                is_find = True
            elif en == lower_en:
                raise ErrDict("Dublicate in file dict", "err_dublicate_en_word")
        if not is_find:
            json_dict.append([new_en, new_tr, new_ru])
        return json_dict

    def _rename_in_dict(self, old_en, new_en, new_tr, new_ru):
        w = self.words.pop(old_en)
        w.rename(new_en, new_tr, new_ru)
        self.words[new_en] = w

    def rename_word(self, old_en, new_en, new_tr, new_ru):
        new_en = new_en.strip()
        new_tr = new_tr.strip()
        new_ru = new_ru.strip()
        self._rename_check(old_en, new_en, new_ru)

        self.cfg.reload()

        json_dict = json.load(codecs.open(self.cfg["path_to_statistics_folder"], "r", "utf-8"))
        json_dict = self._rename_in_json_dict(old_en, new_en, new_tr, new_ru, json_dict)
        self.reload_stat(self.cfg["path_to_statistics_folder"])
        self._rename_in_dict(old_en, new_en, new_tr, new_ru)
        self.save_dict(self.cfg["path_to_dictionaries_folder"], json_dict)
        self.save_stat(self.cfg["path_to_statistics_folder"])

    def _loaded_words(self, type_pr):
        return [(it, it.get_stat(type_pr)) for it in self.words.values() if it.is_load()]

    def words_for_lesson(self, cnt_study_words, words_per_lesson, type_pr):
        all_learned_words = []
        studied_words = []
        count_learned_words = int(round(words_per_lesson * 0.1))
        # today = datetime.date.today()

        for wrd, stat in self._loaded_words(type_pr):
            if stat.get_total_answer() > 0:
                # Прасинг дати із строки
                # last_lesson_date = datetime.datetime.strptime(stat.get_last_lesson_date(), "%Y.%m.%d").date()

                if stat.get_study_percent() >= 100.0:
                    all_learned_words.append(wrd)
                else:
                    studied_words.append(wrd)

        # сортую по даті, по збільшенню дати, - перші самі давніші
        all_learned_words.sort(key=lambda it: it.get_stat(type_pr).get_last_lesson_date())

        # беру лише необхідну к-сть перших слів (не більше 10% від слів на урок)
        learned_words = all_learned_words[:count_learned_words]

        # дополняем изучаемыми/изученными словами из другого направления перевода
        # я закоментував - мені це не потрібно
        # if len(studied_words) < cnt_study_words:
        #     inv_type_pr = word.ru_to_en_write if type_pr == word.en_to_ru_write else word.en_to_ru_write
        #     for wrd, stat in self._loaded_words(inv_type_pr):
        #         if stat.get_total_answer() > 0 and wrd not in (learned_words + studied_words):
        #             studied_words.append(wrd)
        #             if len(studied_words) == cnt_study_words:
        #                 break

        # дополняем ни разу не изучаемыми словами
        if len(learned_words + studied_words) < cnt_study_words:
            for wrd, stat in self._loaded_words(type_pr):
                if stat.get_total_answer() == 0 and wrd not in (learned_words + studied_words):
                    studied_words.append(wrd)
                    if len(studied_words) == cnt_study_words - len(studied_words):
                        break

        # дополняем изучеными словами
        if len(learned_words + studied_words) < cnt_study_words:
            lw = self._loaded_words(self.type_pr)
            lw.sort(key=lambda (it, stat): stat.get_last_lesson_date())

            for (wrd, stat) in lw:
                if stat.get_study_percent() >= 100 and wrd not in (learned_words + studied_words):
                    studied_words.append(wrd)
                    if len(learned_words + studied_words) == cnt_study_words:
                        break

        # сортую по success_percent
        studied_words.sort(key=lambda it: it.get_stat(type_pr).get_success_percent())
        # обрізаю
        studied_words = studied_words[:cnt_study_words - count_learned_words]

        lesson_words = learned_words + studied_words[:cnt_study_words - len(learned_words)]

        # - убрати
        # print(len(lesson_words), len(learned_words), len(studied_words))
        # exit(1)

        for it in lesson_words:
            rating = it.get_stat(type_pr).calc_rating()
            it.set_rating(rating)

        return lesson_words
