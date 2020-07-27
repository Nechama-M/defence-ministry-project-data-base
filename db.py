import os
from typing import List, Dict, Any

from db_api import DB_ROOT
import json
import db_api
import operator

ops = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '%': operator.mod,
    '^': operator.xor,
    '&': operator.and_,
    '|': operator.or_,
    '=': operator.eq,
    '<=': operator.le,
    '>=': operator.ge,
    '!=': operator.ne,
    '>': operator.gt,
    '<': operator.lt
}

META_DATA = "meta_data"


class DBField(db_api.DBField):
    def __init__(self, name, type):
        self.name = name
        self.type = type


class SelectionCriteria(db_api.SelectionCriteria):
    def __init__(self, field_name, operator, value):
        self.field_name = field_name
        self.operator = operator
        self.value = value


def read_json_file(file_name):
    with open(f"{DB_ROOT}\\{file_name}.json", "r", encoding="utf8") as file:
        table = json.load(file)

    return table


def write_to_json_file(file_name, table):
    with open(f"{DB_ROOT}\\{file_name}.json", "w+", encoding="utf8") as file:
        json.dump(table, file, default=str)


def check_conditions(db_table, key, criteria, key_field_name):
    list_ = []
    for c in criteria:
        if c.field_name in db_table[str(key)].keys():
            if (ops[c.operator])(db_table[str(key)][c.field_name], c.value):
                list_.append(True)

        if c.field_name == key_field_name:
            if (ops[c.operator])(int(key), c.value):
                list_.append(True)

    if len(list_) == len(criteria):
        return True
    else:
        return False


class DBTable(db_api.DBTable):
    def __init__(self, name, fields, key_field_name):
        meta_data_table = read_json_file(META_DATA)
        self.name = name
        # self.fields = fields
        self.key_field_name = key_field_name
        meta_data_table[name] = key_field_name
        write_to_json_file(META_DATA, meta_data_table)

    def count(self):
        db_table = read_json_file(self.name)
        return len(db_table)

    def insert_record(self, values: Dict[str, Any]):
        if self.key_field_name in values.keys():
            db_table = read_json_file(self.name)
            value = values.pop(self.key_field_name)
            if db_table.get(str(value)) is None:
                db_table[value] = values
                write_to_json_file(self.name, db_table)
            else:
                raise ValueError("already exist")

    def delete_record(self, key: Any):
        db_table = read_json_file(self.name)
        if str(key) in db_table.keys():
            del db_table[str(key)]
        else:
            raise ValueError("key error")

        write_to_json_file(self.name, db_table)

    def delete_records(self, criteria: List[SelectionCriteria]):
        list_keys_to_del = set()
        db_table = read_json_file(self.name)

        for key in db_table.keys():
            if check_conditions(db_table, key, criteria, self.key_field_name):
                list_keys_to_del.add(str(key))

        for key in list_keys_to_del:
            del db_table[key]

        write_to_json_file(self.name, db_table)

    def get_record(self, key: Any) -> Dict[str, Any]:
        db_table = read_json_file(self.name)
        if str(key) in db_table.keys():
            return db_table[str(key)]
        else:
            raise ValueError("key error")

    def update_record(self, key: Any, values: Dict[str, Any]):
        db_table = read_json_file(self.name)
        db_table[key] = values
        write_to_json_file(self.name, db_table)

    def query_table(self, criteria: List[SelectionCriteria]):
        list_keys = []
        db_table = read_json_file(self.name)

        for key in db_table.keys():
            if check_conditions(db_table, key, criteria, self.key_field_name):
                list_keys.append(db_table[key])

        return list_keys

    def create_index(self, field_to_index: str) -> None:
        raise NotImplementedError


class DataBase(db_api.DataBase):

    def create_table(self, table_name: str, fields: List[DBField], key_field_name: str):
        flag = False
        for field in fields:
            if key_field_name == field.name:
                flag = True
                break
        if not flag:
                raise ValueError("bad Key")

        if not os.path.exists(f"{DB_ROOT}\\{META_DATA}.json"):
            write_to_json_file(META_DATA, {})
        meta_data_table = read_json_file(META_DATA)
        if table_name in meta_data_table.keys():
            raise ValueError("table name exists")
        else:
            new_dict = {}
            new_table = DBTable(table_name, fields, key_field_name)
            write_to_json_file(table_name, new_dict)

        return new_table

    def num_tables(self):
        if not os.path.exists(f"{DB_ROOT}\\{META_DATA}.json"):
            return 0
        else:
            meta_data_table = read_json_file(META_DATA)
            return len(meta_data_table)

    def get_table(self, table_name: str):
        meta_data_table = read_json_file(META_DATA)
        if table_name not in meta_data_table.keys():
            raise ValueError("table name does not exist")
        else:
            db_table = read_json_file(table_name)

            tmp = DBTable(table_name, list(db_table.keys()), meta_data_table[table_name])

            return tmp

    def delete_table(self, table_name: str) -> None:
        if os.path.exists(f"{DB_ROOT}\\{table_name}.json"):
            os.remove(f"{DB_ROOT}\\{table_name}.json")
            meta_data_table = read_json_file(META_DATA)
            del meta_data_table[table_name]
            write_to_json_file(META_DATA, meta_data_table)

        else:
            print("table does not exist")

    def get_tables_names(self):
        if not os.path.exists(f"{DB_ROOT}\\{META_DATA}.json"):
            return None
        else:
            meta_data_table = read_json_file(META_DATA)
            return list(meta_data_table.keys())

    def query_multiple_tables(self, tables: List[str], fields_and_values_list: List[List[SelectionCriteria]],
                              fields_to_join_by: List[str]):
        # TODO
        pass

