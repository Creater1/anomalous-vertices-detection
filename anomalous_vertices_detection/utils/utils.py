import bz2
import cPickle as pickle
import csv
import datetime
import functools
import glob
import json
import os
from functools import wraps


class memoize(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        fn = functools.partial(self.__call__, obj)
        fn.reset = self._reset

        return fn

    def _reset(self):
        self.cache = {}


def memoize2(f):
    cache = {}

    @wraps(f)
    def inner(obj, arg1, arg2):
        memo_key = str(arg1) + str(arg2)
        if memo_key not in cache:
            cache[memo_key] = f(obj, arg1, arg2)
        return cache[memo_key]

    return inner


def extract_graph_from_csv(f, labels=False):
    elems = csv.reader(open(f, 'r'))

    elem = next(elems)
    for elem in elems:
        if labels:
            yield elem[0], elem[1], elem[2]  # empty page will yield None print
        else:
            yield elem[0], elem[1]  # empty page will yield None print


def read_file_by_lines(path):
    with open(path, "rb") as f:
        line_list = f.read().splitlines()
    return line_list


def read_set_from_file(set_path):
    return set(read_file_by_lines(set_path))


def read_file(path):
    with open(path, "rb") as f:
        for line in f:
            yield line


def read_bz2(path):
    with bz2.BZ2File(path, "rb") as f:
        for line in f:
            yield line


# def read_file(path):
#     curr_line = 0
#     with open(path, "rb") as f:
#         for line in f:
#             yield curr_line, line
#             curr_line += 1

def append_to_file(data, path):
    with open(path, 'a') as f:
        f.write(data)
        f.close()


def unique(a):
    """ return the list with duplicate elements removed """
    return list(set(a))


def union(*args):
    """ return the union of two lists """
    # return list(set(a) | set(b))
    return set().union(*args)


def intersect(a, b):
    """ return the intersection of two lists """
    return set(a) & set(b)


def extract_items_from_line(line, delimiter=","):
    return line.rstrip('\r\n').replace('"', '').split(delimiter)


def write_to_file(path, data):
    with open(path, 'w') as f:
        f.write(data)
        f.close()


# Convert List to string
def list_to_string(str_list, delimiter=","):
    return delimiter.join(map(str, str_list))


def two_dimensional_list_to_string(list):
    str_list = []
    for row in list:
        str_list.append(list_to_string(row))
    return list_to_string(str_list, "\n")


def append_list_to_csv(output_path, my_list):
    result = list_to_string(my_list) + "\n"
    append_to_file(result, output_path)


def serilize_list(output_path, selfref_list):
    with open(output_path, 'wb') as output_path:
        # Pickle the list using the highest protocol available.
        pickle.dump(selfref_list, output_path, -1)


def deserilize_list(output_path):
    with open(output_path, 'rb') as output:
        # Pickle the list using the highest protocol available.
        data1 = pickle.load(output)
    return data1


def to_iterable(item):
    if item is None:  # include all nodes via iterator
        item = []
    elif not hasattr(item, "__iter__"):  # if vertices is a single node
        item = [item]  # ?iter()
    return item


def is_json(myjson):
    if not isinstance(myjson, str):
        return False
    try:
        json_object = json.loads(myjson)
    except ValueError, e:
        return False
    return json_object


def dict_writer(mydict, output_path, mode='wb'):
    is_new_file = False
    if not is_valid_path(output_path):
        open(output_path, "w").close()
        is_new_file = True
    with open(output_path, mode) as f:  # Just use 'w' mode in 3.x
        writer = csv.DictWriter(f, mydict[0].keys(), lineterminator='\n')
        if is_new_file:
            writer.writeheader()
        writer.writerows(mydict)


def is_valid_path(path):
    if isinstance(path, str) and os.path.exists(path):
        return True
    return False


def write_hash_table(hash_table, output_path, header=None):
    # csv_list = [[key, value] for key, value in hash_table.iteritems()]
    csv_list = list(hash_table.iteritems())
    if header is not None:
        csv_list = [header] + csv_list
    write_to_file(output_path, two_dimensional_list_to_string(csv_list))


def to_create_new_file(file_name="", qtext="To extract new features "):
    overwrite = False
    while overwrite not in ["Y", "N"]:
        overwrite = raw_input(qtext + file_name + " Y/N?").upper()
    return overwrite == "Y"


def generate_file_name(output_path):
    output = output_path.split(".")
    output.insert(len(output) - 1, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    return ".".join(output)


def get_newest_files(directory, starts_with="", ext="csv"):
    return max(glob.iglob(os.path.join(directory, starts_with + '*.' + ext)), key=os.path.getctime)


def delete_file_content(file_path):
    if is_valid_path(file_path):
        os.remove(file_path)


def get_number(s):
    try:
        num = int(s)
        return num
    except ValueError:
        return False


def graph_anonymizer(graph_path, output_path, header=False, delimiter=","):
    def map_vertex(vertex, vertex_count):
        if vertex not in vertecies_map:
            vertecies_map[vertex] = str(vertex_count)
            vertex_count += 1
        return vertecies_map[vertex], vertex_count

    vertecies_map, anonymized_data, vertex_count = {}, [], 1
    f = read_file(graph_path)
    if type(header) is list:
        anonymized_data.append(header)
    elif header:
        anonymized_data.append(extract_items_from_line(next(f), delimiter))
    for line in f:
        try:
            edge = extract_items_from_line(line, delimiter)
            edge[0], vertex_count = map_vertex(edge[0], vertex_count)
            edge[1], vertex_count = map_vertex(edge[1], vertex_count)
            anonymized_data.append(edge)
        except:
            pass
    write_to_file(output_path, two_dimensional_list_to_string(anonymized_data))
    return vertecies_map


def anonymizer(input_path, output_path, alias_map, header=False, delimiter=","):
    anonymized_data = []
    f = read_file(input_path)
    if type(header) is list:
        anonymized_data.append(header)
    elif header:
        anonymized_data.append(extract_items_from_line(next(f), delimiter))
    for line in f:
        try:
            line = extract_items_from_line(line, delimiter)
            line[0] = alias_map[line[0]]
            anonymized_data.append(line)
        except:
            pass
    write_to_file(output_path, two_dimensional_list_to_string(anonymized_data))
    return alias_map
