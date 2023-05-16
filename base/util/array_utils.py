# -*- coding: utf-8 -*-


def list_to_tree(dict_list: list, sub_field: str = "children", pid_field: str = "pid", id_field: str = "id", index: int = 0) -> list:
    sub = []
    for x in dict_list:
        if x[pid_field] == index:
            x[sub_field] = list_to_tree(dict_list, sub_field=sub_field, pid_field=pid_field, id_field=id_field, index=x[id_field])
            sub.append(x)
    return sub