import random
import time
from threading import Thread
from sdtools.fileops import *
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

    try:
        img = gen_image(payload)
        # save both the image and the prompt
        with open(f"{DIST_DIR}/{date_str}.png", "wb") as f:
            f.write(base64.b64decode(img))
        with open(f"{DIST_DIR}/{date_str}.txt", "w") as f:
            f.write(prompt)
    except Exception as e:
        print(f"Failed to generate image for prompt {prompt}: {e}")


gen_template = {
    "denoising_strength": 0.7,
    "prompt": "",
    "sampler_name": "DPM++ 2M Karras",
    "steps": 30,
    "cfg_scale": 6.5,
    "width": 512,
    "height": 768,
    "negative_prompt": "text, error, signature, watermark, username, realistic,3d, multiple people, animals, bad anatomy, bad arms, lowres, cropped, worth quality ,low quality, normal quality, jpeg artifacts, blurry, bad anatomy, bad hands, bad arms, bad feet, bad anatomy, missing fingers, extra digits, fewer digits, long neck, missing legs, huge person, optical_illusion, bad legs, bad anatomy, text, error, signature, watermark, username, 3d, lowres, cropped, worst quality, low quality, normal quality, jpeg artifacts, blurry, bad anatomy, bad hands, bad arms, bad feet, bad anatomy, missing fingers, extra digits, fewer digits, long neck, missing legs",
    "sampler_index": "DPM++ 2M Karras",
    "enable_hr": True,
    "hr_upscaler": "Latent",
}


def modify_request(request):
    # Parse the incoming request as a JSON object

    new_request = gen_template
    prompt = request["prompt"]
    shape = request["shape"]
    if shape == "horizontal":
        w, h = (704, 512)
    elif shape == "squared":
        w, h = (608, 608)
    else:
        w, h = (512, 704)  # vertical

    # Modify the request by adding a new key-value pair
    new_request["prompt"] = prompt
    new_request["width"] = w
    new_request["height"] = h

    return new_request


SRC_DIR = "D:\CSC3\\abyss"    # main app.py location; also there should be an config.toml there

app = Flask(__name__)
request_queue = Queue(maxsize=1000)

with open(os.path.join(SRC_DIR, "config.toml")) as f:
    queue_config = toml.load(f)

DIST_DIR = queue_config["queue_dst_dir"]
WEBUI_URL = queue_config["webui_url"]
TXT_DIR = queue_config["txt_dir"]

txt_files = get_files_with_suffix(TXT_DIR, TXT_FILE)


def read_random_txt():
    curr_txt = random.choice(txt_files)
    with open (os.path.join(TXT_DIR, curr_txt)) as f:
        curr_prompt = ''.join(f.readlines())
        return curr_prompt
def preprocess_txt(tag_str):
    tags = txtops.get_cleaned_tags_lite(tag_str)
    if "best quality" not in tags:
        tags = ["best quality"] + tags
    if "absurdres" not in tags:
        tags = tags + ["absurdres"]
    return ", ".join(tags)


def fetch_dummy_request() -> Dict:
    """
    从预先指定好的文件夹读取txt, 修改后放入request queue
    :return:
    :rtype:
    """
    shape= random.choice(["horizontal", "vertical", "vertical", "square"])
    random_text = read_random_txt()
    prompt = preprocess_txt(random_text)
    dummy_dict = {
        "prompt": prompt,
        "shape": shape
    }
    dummy_payload = modify_request(dummy_dict)
    return dummy_payload

def check_queue():
    """
    检查当前queue是否为空; 如果是, 生成dummy request放入队列
    :return:
    :rtype:
    """
    mkdir_if_not_exist("TEST")
    print("check_queue: running")
    while True:
        if request_queue.empty():
            dummy_request = fetch_dummy_request()
            request_queue.put(dummy_request)
            date_str = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"{date_str} [new request]: {dummy_request['prompt']}")
            time.sleep(5)

def run_queue():
    """
    持续运行queue
    :return:
    :rtype:
    """
    mkdir_if_not_exist("TESTRUN")
    print("run_queue: running")
    while True:
        if not request_queue.empty():
            req = request_queue.get()
            # Send the request to port 7860
            process_req(req)
            date_str = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"{date_str} [processed]: {req['prompt']}")
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
    print(f"received: [{incoming_request['shape']}] {incoming_request['prompt']}")
    modified_request = modify_request(incoming_request)
    request_queue.put(modified_request)
    return "request added to queue"


t1 = Thread(target=check_queue)
t2 = Thread(target=run_queue)
t1.start()
t2.start()

if __name__ == "__main__":
    """
    2个thread + flask接收外部请求:
    - check_queue
    - run_queue
    """
    app.run(port=7861)
