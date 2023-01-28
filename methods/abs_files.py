import sdtools.txtops as txtops
import sdtools.fileops as fileops
import sdtools.globals as globals
import os
from pathlib import Path


def get_generations(src_dir):
    """读取ai生成的图像"""
    image_files = fileops.get_files_with_suffix(src_dir, globals.IMG_FILES)

    return_imgs = []
    for image in image_files:
        txt_path = txtops.get_txt_filename(image)
        tags = txtops.read_txt_lines(src_dir, txt_path)
        img_path = os.path.join(src_dir, image)
        img_filename = Path(image).stem

        txt_full_path = os.path.join(src_dir, txt_path)

        return_imgs.append((img_path, img_filename, txt_full_path, ", ".join(tags)))

    return_imgs = sorted(return_imgs, key=lambda x: x[1], reverse=True)
    return return_imgs
