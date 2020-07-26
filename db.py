import os
from typing import List, Dict, Any

from db_api import DataBase, DBTable, DBField, SelectionCriteria, DB_ROOT
import json

from db_api import DB_ROOT
from test_db import STUDENT_FIELDS


class DBField(DBField):
    def __init__(self, name, type):
        self.name = name
        self.type = type


class SelectionCriteria(SelectionCriteria):
    def __init__(self, field_name, operator, value):
        self.field_name = field_name
        self.operator = operator
        self.value = value


class DBTable(DBTable):
    def __init__(self, name, fields, key_field_name):
        self.name = name
        # self.fields = fields
        self.key_field_name = key_field_name

    def count(self):
        with open(f"{DB_ROOT}\\{self.name}.json", "r", encoding="utf8") as file:
            table = json.load(file)

        return len(table)

    def insert_record(self, values: Dict[str, Any]):
        with open(f"{DB_ROOT}\\{self.name}.json", "r", encoding="utf8") as file:
            table = json.load(file)
        if list(values.keys())[0] not in table[self].keys():
            # table[self][list(values.keys())[0]] = values
            pass

    def delete_record(self, key: Any):
        with open(f"{DB_ROOT}\\{self.name}.json", "r", encoding="utf8") as file:
            table = json.load(file)

        del table[key]

    def delete_records(self, criteria: List[SelectionCriteria]):
       pass

    def get_record(self, key: Any) -> Dict[str, Any]:
        with open(f"{DB_ROOT}\\{self.name}.json", "r", encoding="utf8") as file:
            table = json.load(file)

        return table[key]

    def update_record(self, key: Any, values: Dict[str, Any]):
        with open(f"{DB_ROOT}\\{self.name}.json", "r", encoding="utf8") as file:
            table = json.load(file)

        table[key] = values

        with open(f"{DB_ROOT}\\{self.name}.json", "w", encoding="utf8") as file:
            json.dump(table, file)

    def query_table(self, criteria: List[SelectionCriteria]):
        raise NotImplementedError

    def create_index(self, field_to_index: str) -> None:
        raise NotImplementedError


class DataBase(DataBase):

    def create_table(self, table_name: str, fields: List[DBField], key_field_name: str):
        new_dict = {}
        new_table = DBTable(table_name, fields, key_field_name)
        with open(f"{DB_ROOT}\\{table_name}.json", "w", encoding="utf8") as file:
            json.dump(new_dict, file)

        return new_table

    def num_tables(self):
        return len([name for name in os.listdir(DB_ROOT) if os.path.isfile(os.path.join(DB_ROOT, name))])

    def get_table(self, table_name: str):
        with open(f"{DB_ROOT}\\{table_name}.json", "r", encoding="utf8") as file:
            db_table = json.load(file)

        return db_table

    def delete_table(self, table_name: str) -> None:
        if os.path.exists(f"{DB_ROOT}\\{table_name}.json"):
            os.remove(f"{DB_ROOT}\\{table_name}.json")
        else:
            print("The table does not exist")

    def get_tables_names(self):
        table_names = []
        for root, dirs, files in os.walk(DB_ROOT):
            for file in files:
                table_names.append(file[:-5])

        return table_names

    def query_multiple_tables(self, tables: List[str], fields_and_values_list: List[List[SelectionCriteria]], fields_to_join_by: List[str]):
        # TODO
        pass
