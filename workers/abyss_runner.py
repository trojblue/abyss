import random
import time
from threading import Thread
import sdtools.fileops as fops
import sdtools.txtops as txtops
import toml
from flask import Flask, request, redirect, request, jsonify
from queue import Queue
from typing import *
import base64
import datetime
import hashlib
import json, os
import requests as r
from tqdm import tqdm
from typing import *

"""
Original written by Galvin:
https://github.com/GalvinGao
"""


# gen_image takes a prompt and returns a generated PNG image in base64 format
def gen_image(payload: Dict) -> str:
    prompt = payload["prompt"]
    resp = r.post(f"{WEBUI_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
    if resp.status_code != 200:
        raise Exception(
            f"Failed to generate image for prompt {prompt}: Status code {resp.status_code}, {resp.text}"
        )

    json = resp.json()
    if json["images"]:
        images = json["images"]
        if len(images) == 0:
            raise Exception(
                f"Failed to generate image for prompt {prompt}: empty images array: {json}"
            )
        return images[0]

    raise Exception(f"Failed to generate image for prompt {prompt}: {json}")


def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()


def process_req(payload: Dict):  # prompt: string
    # Create the directory if it doesn't exist
    prompt = payload["prompt"]
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR, exist_ok=True)

    date_str = datetime.datetime.now().strftime("%y.%m.%d_%H%M%S")

    p = payload
    samplers_str = f"{p['sampler_name']}_step{p['steps']}_cfg{p['cfg_scale']}"
    filename = f"{date_str}_{samplers_str}"
    try:
        img = gen_image(payload)
        # save both the image and the prompt
        with open(f"{DIST_DIR}/{filename}.png", "wb") as f:
            f.write(base64.b64decode(img))
        with open(f"{DIST_DIR}/{filename}.txt", "w") as f:
            f.write(prompt)
    except Exception as e:
        print(f"Failed to generate image for prompt {prompt}: {e}")


def modify_request(request):
    # Parse the incoming request as a JSON object

    new_request = gen_template
    prompt = request["prompt"]
    shape = request["shape"]
    if shape == "horizontal":
        w, h = (768, 512)
    elif shape == "square":
        w, h = (640, 640)
    else:
        w, h = (512, 768)  # vertical

    # Modify the request by adding a new key-value pair
    new_request["prompt"] = prompt
    new_request["width"] = w
    new_request["height"] = h

    return new_request


SRC_DIR = (
    "D:\CSC3\\abyss"  # main app.py location; also there should be an config.toml there
)

app = Flask(__name__)
request_queue = Queue(maxsize=1000)

with open(os.path.join(SRC_DIR, "config.toml")) as f:
    runner_config = toml.load(f)
    runner_config["vital_tags"] = runner_config["vital_tags"][0].split(", ")

DIST_DIR = runner_config["queue_dst_dir"]
# WEBUI_URL = runner_config["webui_url"]
WEBUI_URL = runner_config["webui_url"]
TXT_DIR = runner_config["txt_dir"]

gen_template = {
    "denoising_strength": runner_config["denoising_strength"],
    "prompt": "1girl",
    "sampler_name": runner_config["sampler_name"],
    "steps": runner_config["steps"],
    "cfg_scale": runner_config["cfg_scale"],
    "width": 576,
    "height": 768,
    "negative_prompt": runner_config["neg"],  # neg_longer | neg_qiuyue
    "enable_hr": True,
    "hr_upscaler": runner_config["hr_upscaler"],
}

txt_files = fops.get_files_with_suffix(TXT_DIR, fops.TXT_FILE)
tags_dict, txt_lines = fops.read_txt_files(TXT_DIR)


def gen_prompt() -> str:
    """
    根据txt文件词频和toml配置生成随机tag
    :return:
    :rtype:
    """

    prompts = txtops.gen_prompt_by_config(tags_dict, config=runner_config)
    return_tags = ", ".join(prompts)
    # rcfg = runner_config
    # start, vital, end = rcfg['start_tags'], rcfg['vital_tags'][0].split(','), rcfg['end_tags']
    # return_tags = ", ".join(start + vital + end)
    return return_tags


def read_random_txt():
    curr_txt = random.choice(txt_files)
    with open(os.path.join(TXT_DIR, curr_txt)) as f:
        curr_prompt = "".join(f.readlines())
        return curr_prompt


def preprocess_txt(tag_str):
    tags = txtops.get_cleaned_tags_lite(tag_str)
    return ", ".join(tags)


def fetch_dummy_request() -> Dict:
    """
    从预先指定好的文件夹读取txt, 修改后放入request queue
    :return:
    :rtype:
    """
    shape = random.sample(runner_config["shapes"], 1)[0]
    random_text = gen_prompt()
    prompt = preprocess_txt(random_text)
    dummy_dict = {"prompt": prompt, "shape": shape}
    dummy_payload = modify_request(dummy_dict)
    return dummy_payload


def check_queue():
    """
    检查当前queue是否为空; 如果是, 生成dummy request放入队列
    :return:
    :rtype:
    """
    print("check_queue: running")
    while True:
        if request_queue.empty():
            dummy_request = fetch_dummy_request()
            request_queue.put(dummy_request)
            date_str = datetime.datetime.now().strftime("%H:%M:%S")
            p = dummy_request["prompt"]
            print(f"{date_str} [new request]: [{len(p.split(','))}] {p}")
            time.sleep(5)


def get_date_str():
    return datetime.datetime.now().strftime("%H:%M:%S")


def get_request_repr(req: Dict):
    # r_date, r_shape, r_len, r_prompt
    w, h = req["width"], req["height"]
    multiple = 2 if req["enable_hr"] else 1
    shape = f"{w}x{h}^{multiple}"
    res_tuple = get_date_str(), shape, len(req["prompt"].split(", ")), req["prompt"]
    return res_tuple


def run_queue():
    """
    持续运行queue
    :return:
    :rtype:
    """
    print("run_queue: running")
    while True:
        if not request_queue.empty():
            req = request_queue.get()
            # Send the request to port 7860
            process_req(req)

            r_date, r_shape, r_len, r_prompt = get_request_repr(req)
            print(
                f"{r_date} [processed]: [{r_shape} {r_len}] len {len(r_prompt.split(', '))}"
            )
        else:
            time.sleep(0.5)


@app.route("/", methods=["POST"])
def receive_request():
    """
    从网站收到生成request
    :return:
    :rtype:
    """
    # Get the incoming request and add it to the queue
    incoming_request = request.get_json()
    incoming_modified = modify_request(incoming_request)

    r_date, r_shape, r_len, r_prompt = get_request_repr(incoming_modified)
    print(f"{r_date} received: [{r_shape} {r_len}] {r_prompt}")
    request_queue.put(incoming_modified)
    return "request added to queue"


t1 = Thread(target=check_queue)
t2 = Thread(target=run_queue)
t1.start()
t2.start()

import signal
import sys
from threading import Thread
def sigint_handler(signal, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

if __name__ == "__main__":
    try:
        app.run(port=7861)
    except KeyboardInterrupt:
        print("Program terminated by keyboard interrupt (Ctrl+C).")
        sys.exit(0)