import csv
import math
import re

from common import check_and_make_the_path
from special_characters import special_characters

def remove_special_characters(text):
    for c in special_characters:
        text = text.replace(c,'')
    return text

def remove_urls(text):
    # 正则表达式匹配URL
    url_pattern = re.compile(r'https?://[^\s]+', re.IGNORECASE)
    # 使用正则表达式替换URL为空字符串
    return url_pattern.sub('', text)

def remove_alpha_num(text):
    return re.sub(r'[a-zA-Z0-9]', '', text)

def cumulative_sum(lst):
    return [sum(lst[:i+1]) for i in range(len(lst))]

def find_last_index_less_than_k(lst, k):
    last_index = -1  # 初始化为-1，表示如果没有找到则返回-1
    for i, num in enumerate(lst):
        if num < k:
            last_index = i  # 更新最后一个小于k的索引
    return last_index

def page_buffer(input_str, last_page='', char_threshold = 510):
    output_sentence_list = []

    if (last_page != '') and len(last_page) != 0:
        input_str = last_page+input_str
    chars_num = len(input_str)

    if chars_num > char_threshold:  # 输入内容过长超出范围
        truncated_str = input_str[:char_threshold]  # 长度范围内的字符串
        overlong_str = input_str[char_threshold:]  # 超出范围的字符串
        output_sentence_list += page_buffer(input_str=truncated_str)[0]
        next_page_head_str = overlong_str
    else:  # 输入内容在范围内
        if chars_num == 0:
            return [], ''
        elif input_str[-1] == "。":  # 如果范围的最后一个字符是句号，则直接把内容放入到输出列表中
            output_sentence_list += [i+"。" for i in input_str.split('。') if (i != '') and (len(i) != 0)]
            next_page_head_str = ''
        else:  # 如果范围的最后一个字符不是句号，把最后一个句号内容放入到输出列表中，然后把其余内容作为下一页开头返回
            last_stop_symbol_index_in_truncated_str = input_str.rfind("。")  # 查看
            output_sentence_list += [i + "。" for i in input_str[:last_stop_symbol_index_in_truncated_str].split('。') if (i != '') and (len(i) != 0)]
            next_page_head_str = input_str[last_stop_symbol_index_in_truncated_str:]


    return output_sentence_list, next_page_head_str


def book_process(context_dict, minim_tuncate_threshold=10, head_skip_frac=0.05, tail_skip_frac=0.05):
    result_list = []

    context_list = list(context_dict.values())
    total_pages = len(context_list)
    if total_pages >= minim_tuncate_threshold:
        start_index = math.ceil(total_pages * head_skip_frac)
        end_index = total_pages - math.ceil(total_pages * tail_skip_frac)
        coarse_filtered_context = context_list[start_index: end_index]
    else:
        coarse_filtered_context = context_list

    last_truncated_context = ''
    for page in coarse_filtered_context:
        if len(page) == 0 or page == '':
            continue
        page = remove_alpha_num(remove_urls(page))
        page = page.replace('\n','')

        tmp_str_list, last_truncated_context = page_buffer(page, last_truncated_context)
        result_list +=  [i for i in tmp_str_list if i != '']

    return result_list


def filte_str_list_by_length_percentile(input_list, k):
    # 确保k是一个有效的百分比（0 < k < 1）
    if not (0 < k < 1):
        raise ValueError("k必须是一个介于0和1之间的数")

    # 计算需要保留的字符串数量
    num_to_keep = int(len(input_list) * (1 - k))

    # 按照字符串长度对列表进行排序（从长到短）
    sorted_list = sorted(input_list, key=len, reverse=True)

    # 返回前num_to_keep个字符串
    return sorted_list[:num_to_keep]

def read_csv_standard(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = list(csv.reader(file))
        for row in reader:
            if row != [] or len(row) != 0:
                # data.append(row[0].replace('\ufeff', ''))
                try:
                    data.append(row[0].replace('\ufeff',''))
                except IndexError:
                    print(f"file_path :{file_path}, row:{row}")
                    return data

    return data

if __name__ == '__main__':
    print("111")