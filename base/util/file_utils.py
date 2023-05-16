# -*- coding: utf-8 -*-

import os


def current_path() -> str:
    return os.getcwd()


def create_dir_if_not_exists(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(path)


def join_path_filename(path: str, filename: str) -> str:
    return os.path.join(path, filename)
