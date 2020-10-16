# -*- coding: utf-8 -*-

import os
import re
import json
import os.path
import unittest

reg_cmnt = re.compile(r"/\*.*?\*/", re.DOTALL)


class Config:
    "Работа с конфигурационным файлом"

    def __init__(self, main_config_path = None, user_config_path = None):
        self._main_config_path = main_config_path
        self._user_config_path = user_config_path

        if main_config_path is None:
            self._main_config_path = "config.json5"

        if user_config_path is None:
            self._user_config_path = "config_user.json5"

        self._config_dictionary = {}

    def __getitem__(self, key):
        return self._config_dictionary[key]

    def __len__(self):
        return len(self._config_dictionary)

    def _load_config_file(self, path):
        data = {}
        if os.path.exists(path):
            txt = open(path).read()
            txt = reg_cmnt.sub("", txt)  # remove comments
            data = json.loads(txt)
        return data

    def _set_default_config(self, cfg):
        cfg["path_to_dictionaries_folder"] = cfg.get("path_to_dictionaries_folder", "dictionaries")
        cfg["path_to_dictionaries_folder"] = cfg.get("path_to_dictionaries_folder", "statistics")
        cfg["words_per_lesson"] = int(cfg.get("words_per_lesson", 5))
        cfg["CntStudyWords"] = int(cfg.get("CntStudyWords", 50))
        cfg["MinPercent"] = float(cfg.get("MinPercent", 97.0))
        cfg["MinSuccessCnt"] = int(cfg.get("MinSuccessCnt", 10))
        cfg["retry_time"] = int(cfg.get("retry_time", 1800))
        cfg["hide_transcription"] = cfg.get("hide_transcription", "no")
        cfg["start_time_delay"] = int(cfg.get("start_time_delay", 1))
        cfg["stat_count_row"] = int(cfg.get("stat_count_row", 200))
        cfg["right_answer_percent"] = float(cfg.get("right_answer_percent", 10.0))
        cfg["wrong_answer_percent"] = float(cfg.get("wrong_answer_percent", 40.0))
        cfg["empty_answer_is_error"] = cfg.get("empty_answer_is_error", "no")
        cfg["internet_dictionary_url"] = cfg.get("internet_dictionary_url",
                                                 {
                                                     "EN_RU": "http://slovari.yandex.ru/{word}/en-ru/#lingvo/",
                                                     "RU_EN": "http://slovari.yandex.ru/{word}/en/#lingvo/"
                                                     })

    def create_default_user_config(self):
        if not os.path.isfile(self._user_config_path):
            txt = "{\n    /*\n        User config\n    */\n\n}"
            open(self._user_config_path, "wt").write(txt)

    def reload(self):
        self._config_dictionary = {}
        self._config_dictionary.update(self._load_config_file(self._main_config_path))
        self._config_dictionary.update(self._load_config_file(self._user_config_path))

        self._set_default_config(self._config_dictionary)

        return self._config_dictionary
