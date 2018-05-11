# encoding: utf-8
import json
import os
import os.path
import cv2
from PIL import Image

import logging
_logger = logging.getLogger(__name__)


def add_txt(data, path):
    """写入数据到path，支持字符，数组，字典"""
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(os.path.dirname(path))
    with open(path, "ab") as text_file:
        if isinstance(data, str):
            text_file.write(str(data))
        elif isinstance(data, list):
            for line in data:
                if isinstance(line, str):
                    text_file.write(str(line) + '\n')
        else:
            text_file.write(json.dumps(data))

def filter_images(image_dir, area):
    """
    过滤掉太小的图片
    Args:
        image_dir: 需要过滤的图片
        area:  过滤阈值面积
    """
    images = os.listdir(image_dir)
    for image in images:
        try:
            image_path = os.path.join(image_dir, image)
            # img = cv2.imread(image_path, 0)
            img = Image.open(image_path)
            height, width = img.size
            if height*width < area:
                os.remove(image_path) 
        except Exception as e:
            print(e)

def clear_dir(image_dir):
    if not os.path.exists(image_dir):
        _logger.error("File Error: no such file")
        raise IOError
    images = os.listdir(image_dir)
    count = len(images)
    for i, image in enumerate(images):
        sys.stdout.write("\r%d/%d" % (i, count))
        sys.stdout.flush()
        try:
            cv2.imread(image, 0)
        except Exception as e:
            print(image)
            print(" ")
            os.remove(image)
