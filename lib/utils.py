import os
import random
from typing import *
from pathlib import Path
import os

"""
Lightweight replacement for sdtools package
"""

__all_imgs_raw = (
    "jpg jpeg png bmp dds exif jp2 jpx pcx pnm ras gif tga tif tiff xbm xpm webp"
)
IMG_FILES = ["." + i.strip() for i in __all_imgs_raw.split(" ")]

TXT_FILE = [".txt"]
JSON_FILE = [".json"]


def get_files_with_suffix(
        src_dir: str, suffix_list: List[str], recursive: bool = False
):
    """
    :param src_dir:
    :param suffix_list: ['.png', '.jpg', '.jpeg']
    :param recursive: 是否读取子目录
    :return: ['img_filename.jpg', 'filename2.jpg']
    """
    if recursive:  # go through all subdirectories
        filtered_files = []
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith(tuple(suffix_list)):
                    filtered_files.append(os.path.join(root, file))

    else:  # current dir only
        files = os.listdir(src_dir)
        filtered_files = [f for f in files if f.endswith(tuple(suffix_list))]

    return filtered_files


def read_txt_files(src_dir: str) -> (Dict, List[str]):
    """
    :param tag_dir: 包含txt tag文件的目录
    :return: 训练集词频, 训练集原文
    """
    if not src_dir:
        return {}

    tags_dict, all_lines = {}, []
    # Iterate over all files in the directory

    txt_files = get_files_with_suffix(src_dir, TXT_FILE)
    for txt in txt_files:
        txt_file = os.path.join(src_dir, txt)
        with open(txt_file, "r") as fd:
            single_line_tags = ", ".join(fd.readlines()).split(",")
            single_line_cleaned = [i.strip() for i in single_line_tags]
            all_lines.append(single_line_cleaned)
            for key in single_line_cleaned:
                tags_dict[key] = tags_dict.get(key, 0) + 1  # 不存在则为0; count+1

    return tags_dict, all_lines


def random_select(weighted_dict):  # 02a
    """d = {'1girl': 5859, 'eyes': 61, 'fur': 53}
    按权重随机选择一个词条输出
    """
    total_weight = sum(weighted_dict.values())
    r = random.randint(1, total_weight)
    for char, weight in weighted_dict.items():
        r = r - weight
        if r <= 0:
            return char


def gen_prompt_by_config(word_freq_dict: Dict, config: Dict):
    """
    gen_prompt_by_config的阉割(青春版

    :param word_freq_dict:  tags_dict, txt_lines = fileops.read_txt_files(self.src_dir)
    :type word_freq_dict:  Dictionary
    :param config: loaded toml config file
    :type config: Dict-like
    :return:
    :rtype:
    """
    end_tags = config["end_tags"]  # 一定出现, 保证结尾
    start_tags = config["start_tags"]  # 一定出现, 保证开头
    tag_count = config["tag_count"]
    vital_tags = config["vital_tags"]  # 一定出现, 随机顺序
    taboo_tags = config["taboo_tags"]  # 一定不出现

    new_tags = vital_tags + [
        random_select(word_freq_dict) for i in range(tag_count - len(vital_tags))
    ]  # 添加vital_tags
    random.shuffle(new_tags)  # 打乱顺序

    new_tags = new_tags + [
        random_select(word_freq_dict) for i in range(tag_count)
    ]  # 总共随机生成2n个
    new_tags = list(dict.fromkeys(new_tags))  # 去重
    # new_tags = remove_occurence_if_exists(
    #     start_tags + end_tags, new_tags
    # )  # 去除已存在的开头结尾tag
    new_tags = [i for i in new_tags if i not in taboo_tags]  # 去除taboo tags
    # new_tags = get_cleaned_tags_lite(", ".join(new_tags))

    return start_tags + new_tags[: tag_count - len(end_tags)] + end_tags  # 返回前n个


def read_txt_lines(
        src_dir: str | Path, filename: str | Path, filepath: str | Path = None
):
    """
    读取txt文件, 返回List[lines]
    :param src_dir:
    :param filename:
    :param path:
    :return:
    """

    real_path = filepath if filepath else os.path.join(src_dir, filename)

    with open(real_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return lines


def get_generations(src_dir):
    """读取ai生成的图像"""
    image_files = get_files_with_suffix(src_dir, IMG_FILES)

    return_imgs = []
    for image in image_files:
        txt_path = Path(image).with_suffix(".txt")
        tags = read_txt_lines(src_dir, txt_path)
        img_path = os.path.join(src_dir, image)
        img_filename = Path(image).stem

        txt_full_path = os.path.join(src_dir, txt_path)

        return_imgs.append((img_path, img_filename, txt_full_path, ", ".join(tags)))

    return_imgs = sorted(return_imgs, key=lambda x: x[1], reverse=True)
    return return_imgs
