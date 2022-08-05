import re
import time


def count_time(func: callable) -> callable:
    def wrapper(*arg, **kwargs):
        start_time = time.time()
        result = func(*arg, **kwargs)
        print(f"下载耗时:{time.time() - start_time:.2f}s")
        return result

    return wrapper


def remove_str(content: str):
    res_compile = re.compile(u'[\U00010000-\U0010ffff\\uD800-\\uDBFF\\uDC00-\\uDFFF]')
    return res_compile.sub("", re.sub('[/:*?"<>|x08]', '#', content))


def rec_id(book_id: str):
    book_id = book_id if 'http' not in book_id else re.findall(r'/(\d+)/?', book_id)[0]
    return str(book_id) if book_id.isdigit() else f'输入信息 {book_id} 不是数字或链接！'


def index_title(division_index: int, image_name: str):
    return str(division_index).rjust(4, "0") + '-' + str(image_name)


def input_str(prompt, default=None):
    while True:
        ret = input(prompt)
        if ret != '':
            return ret
        elif default is not None:
            return default


def input_int(prompt: str, max_number: int = None):
    while True:
        ret = input(prompt)
        if ret.isdigit():
            if max_number is None:
                return int(ret)
            if max_number is not None and int(ret) < max_number:
                return int(ret)
            else:
                print(f"输入数字 {ret} 需要小于索引 {max_number} ")
                continue
        else:
            if ret.strip() != '':
                print(f"输入的内容 {ret} 不是数字，请重新输入")