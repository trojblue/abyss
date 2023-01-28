"""
Original written by Galvin:
https://github.com/GalvinGao
"""

from flask import Flask, request, redirect, request, jsonify
from queue import Queue
import json
import requests

import base64
import datetime
import hashlib
import os
import random
import json, os
import requests as r
from tqdm import tqdm
from typing import *


# gen_image takes a prompt and returns a generated PNG image in base64 format
def gen_image(payload: Dict) -> str:
    prompt = payload['prompt']
    resp = r.post(f"{BASE_URL}/sdapi/v1/txt2img", json=payload, timeout=600)
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


app = Flask(__name__)
request_queue = Queue(maxsize=1000)

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
    prompt = request['prompt']
    shape = request['shape']
    if shape == "horizontal":
        w, h = (704, 512)
    elif shape == "squared":
        w, h = (608, 608)
    else:
        w, h = (512, 704)  # vertical

    # Modify the request by adding a new key-value pair
    new_request['prompt'] = prompt
    new_request['width'] = w
    new_request['height'] = h

    return new_request


SRC_DIR = "D:\CSC3\\abyss"
DIST_DIR = "./static/generated"
BASE_URL = "http://127.0.0.1:7860"


@app.route('/', methods=['POST'])
def handle_request():
    # Get the incoming request and add it to the queue
    incoming_request = request.get_json()
    print(f"received: [{incoming_request['shape']}] {incoming_request['prompt']}")

    modified_request = modify_request(incoming_request)
    request_queue.put(modified_request)

    # Send the request from the queue to port 7860
    while not request_queue.empty():
        req = request_queue.get()
        process_req(req)
        return "processed"


if __name__ == '__main__':
    app.run(port=7861)
