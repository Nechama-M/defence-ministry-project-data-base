import os
from typing import List, Dict, Any

import hashedindex as hashedindex

from db_api import DB_ROOT
import json
import db_api
import operator

OPERATORS = {
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

# for meta data table which holds all table names and their primary key
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


# reads a table from disk (dict from json file)
def read_json_file(file_name):
    with open(f"{DB_ROOT}\\{file_name}.json", "r", encoding="utf8") as file:
        table = json.load(file)

    return table


# writes a table to disk (dict to json file)
def write_to_json_file(file_name, table):
    with open(f"{DB_ROOT}\\{file_name}.json", "w+", encoding="utf8") as file:
        json.dump(table, file, default=str)


# checks if a record satisfies a criteria
def check_conditions(db_table, key, criteria, key_field_name):
    list_ = []
    for c in criteria:
        if c.field_name in db_table[str(key)].keys():
            if (OPERATORS[c.operator])(db_table[str(key)][c.field_name], c.value):
                list_.append(True)

        if c.field_name == key_field_name:
            if (OPERATORS[c.operator])(int(key), c.value):
                list_.append(True)

    if len(list_) == len(criteria):
        return True
    else:
        return False


# checks if an index exists already on a field
def exists_table_index_on_field(table_name, field_to_index):
    if os.path.exists(f"{table_name}_{field_to_index}_index.json"):
        return True

    return False


class DBTable(db_api.DBTable):
    def __init__(self, name, fields, key_field_name):
        meta_data_table = read_json_file(META_DATA)
        self.name = name
        # no need for: self.fields = fields. this is a non-relational database...
        self.key_field_name = key_field_name
        meta_data_table[name] = key_field_name
        write_to_json_file(META_DATA, meta_data_table)

    def count(self):
        db_table = read_json_file(self.name)
        return len(db_table)

    def insert_record(self, values: Dict[str, Any]):
        # check if record has primary key
        if self.key_field_name in values.keys():
            db_table = read_json_file(self.name)

            # get primary key from list of values
            value = values.pop(self.key_field_name)
            # insert record
            if db_table.get(str(value)) is None:
                db_table[value] = values
                # update table on disk
                write_to_json_file(self.name, db_table)

            else:
                # key must be unique. cannot insert a record with a key that exists already
                raise ValueError("key must be unique")

            # must update indexes if they exist on the insertion
            for key in values.keys():
                if exists_table_index_on_field(self.name, key):
                    index = read_json_file(f"{self.name}_{key}_index")
                    index.add_term_occurrence(key, value)

        else:
            # no key was given for record
            raise ValueError("record must have primary key")

    def delete_record(self, key: Any):
        db_table = read_json_file(self.name)
        if str(key) in db_table.keys():
            for key_ in db_table[str(key)].keys():

                # must update all indexes that exist for table on the deletion of a record
                if exists_table_index_on_field(self.name, key_):
                    index = read_json_file(f"{self.name}_{key_}_index")
                    # if there is more than one record per index
                    if len(index[db_table[str(key)][key_]]) > 1:
                        del index[db_table[str(key)][key_][str(key)]]
                    # only one  record per index - so we can reomve it
                    else:
                        del index[db_table[str(key)][key_]]
                    write_to_json_file(f"{self.name}_{key_}_index", index)

            del db_table[str(key)]

        else:
            # trying to delete record that does not exist
            raise ValueError("key error")

        write_to_json_file(self.name, db_table)

    def delete_records(self, criteria: List[SelectionCriteria]):
        list_keys_to_del = set()
        db_table = read_json_file(self.name)

        for key in db_table.keys():
            if check_conditions(db_table, key, criteria, self.key_field_name):
                list_keys_to_del.add(str(key))

                # must update all indexes that exist for table on the deletion of records
                for key_ in db_table[key].keys():
                    if exists_table_index_on_field(self.name, key_):
                        index = read_json_file(f"{self.name}_{key_}_index")
                        if len(index[db_table[str(key)][key_]]) > 1:
                            del index[db_table[str(key)][key_][str(key)]]
                        else:
                            del index[db_table[str(key)][key_]]
                        write_to_json_file(f"{self.name}_{key_}_index", index)

        for key in list_keys_to_del:
            del db_table[key]

        write_to_json_file(self.name, db_table)

    def get_record(self, key: Any):
        db_table = read_json_file(self.name)
        if str(key) in db_table.keys():
            temp_dict = db_table[str(key)].copy()
            temp_dict.update({self.key_field_name: str(key)})
            return temp_dict

        else:
            raise ValueError("key error")

    def update_record(self, key: Any, values: Dict[str, Any]):
        db_table = read_json_file(self.name)
        for key_ in values.keys():
            # must update all indexes that exist for table on the update of a record
            if exists_table_index_on_field(self.name, key_):
                index = read_json_file(f"{self.name}_{key_}_index")
                if len(index[db_table[str(key)][key_]]) > 1:
                    del index[db_table[str(key)][key_][str(key)]]
                else:
                    del index[db_table[str(key)][key_]]
                index.add_term_occurrence(key_, key)
                write_to_json_file(f"{self.name}_{key_}_index", index)

        db_table[str(key)] = values
        write_to_json_file(self.name, db_table)

    def query_table(self, criteria: List[SelectionCriteria]):
        list_keys = []
        db_table = read_json_file(self.name)

        # check every record if satisfies conditions
        for key in db_table.keys():
            if check_conditions(db_table, key, criteria, self.key_field_name):
                list_keys.append(db_table[key])

        return list_keys

    def create_index(self, field_to_index: str):
        # an index already exists on field - no need to create again
        if exists_table_index_on_field(self.name, field_to_index):
            pass
        else:
            # hash-map index is created
            index = hashedindex.HashedIndex()
            db_table = read_json_file(self.name)
            for key in db_table.keys():
                if field_to_index in db_table[key].keys():
                    index.add_term_occurrence(db_table[key][field_to_index], key)

            write_to_json_file(f"{self.name}_{field_to_index}_index", index.items())


class DataBase(db_api.DataBase):

    def create_table(self, table_name: str, fields: List[DBField], key_field_name: str):
        flag = False
        for field in fields:
            if key_field_name == field.name:
                flag = True
                break
        if not flag:
            raise ValueError("bad Key")

        # if it's first table to be created we must create a meta data table
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
        # if meta data table does not exist - it means that no tables were created
        if not os.path.exists(f"{DB_ROOT}\\{META_DATA}.json"):
            return 0

        else:
            # return number of tables in meta data table
            meta_data_table = read_json_file(META_DATA)
            return len(meta_data_table)

    def get_table(self, table_name: str):
        meta_data_table = read_json_file(META_DATA)

        # if name of table does not exist in meta data table, than table does not exist...
        if table_name not in meta_data_table.keys():
            raise ValueError("table name does not exist")
        else:
            # DBTable to be returned
            db_table = read_json_file(table_name)
            tmp = DBTable(table_name, list(db_table.keys()), meta_data_table[table_name])

            return tmp

    def delete_table(self, table_name: str):
        if os.path.exists(f"{DB_ROOT}\\{table_name}.json"):
            os.remove(f"{DB_ROOT}\\{table_name}.json")
            for root, dirs, files in os.walk(DB_ROOT):
                for file in files:
                    # we don't allow using underscores in table name
                    # must delete all indexes of table
                    if file[:len(table_name) + 1] == table_name + "_" and file[-10:] == "_index.json":
                        os.remove(f"{DB_ROOT}\\{file}")

            meta_data_table = read_json_file(META_DATA)
            del meta_data_table[table_name]
            write_to_json_file(META_DATA, meta_data_table)

        else:
            print("table does not exist")

    def get_tables_names(self):
        # if meta data table does not exist - it means that no tables were created
        if not os.path.exists(f"{DB_ROOT}\\{META_DATA}.json"):
            return []
        else:
            # return names of tables in meta data table
            meta_data_table = read_json_file(META_DATA)
            return list(meta_data_table.keys())

    def join_two_tables(self, table_name_1, table_name_2, fields_to_join_by):
        # get both tables
        table_1 = read_json_file(table_name_1)
        table_2 = read_json_file(table_name_2)
        joined_tables = []

        # go over all keys and check if can join
        for key_1 in table_1.keys():
            for key_2 in table_2.keys():
                flag = True
                for field in fields_to_join_by:
                    if table_1[key_1][field] != table_2[key_2][field]:
                        flag = False
                if flag:
                    joined_dict = self.get_table(table_name_1).get_record(key_1)
                    joined_tables.append(joined_dict.update(self.get_table(table_name_2).get_record(key_2)))

        return joined_tables

    def query_multiple_tables(self, tables: List[str], fields_and_values_list: List[List[SelectionCriteria]],
                              fields_to_join_by: List[str]):
        table_with_only_records_satisfying_conditions = []
        # keep only records of tables that satisfy condition
        for i in range(len(tables)):
            table_with_only_records_satisfying_conditions.append(self.get_table(tables[i]).query_table(fields_and_values_list[i]))

        # join all records of all tables
        queried_multiple_tables = [table_with_only_records_satisfying_conditions[0]]
        for table in table_with_only_records_satisfying_conditions[1:]:
            queried_multiple_tables += self.join_two_tables(queried_multiple_tables, table, fields_to_join_by)

        return queried_multiple_tables
