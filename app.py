from flask import Flask, render_template, request, send_file, jsonify
from flask_assets import Environment
from flask_ngrok2 import run_with_ngrok

from flask_compress import Compress
import sdtools.txtops
import json
import toml
import os.path

from webassets import Bundle

from methods.abs_files import *

app = Flask(__name__)
app.debug = True
# Compress(app)
# run_with_ngrok(app, auth_token="2JFGyPXcQVNpd0wnkl9iAmZBHZR_7Vw7fXvwTTRvvzjzFeTx2")


# 读取设置
with open("config.toml") as f:
    config = toml.load(f)

# https://flask-assets.readthedocs.io/en/latest/#usage
assets = Environment(app)
assets.url = app.static_url_path

app.debug = True
# Scss files
scss = Bundle(
    "assets/main.scss",  # 1. will read this scss file and generate a css file based on it
    filters="libsass",   # using this filter: https://webassets.readthedocs.io/en/latest/builtin_filters.html#libsass
    output="css/scss-generated.css"  # 2. and output the generated .css file in the static/css folder
)
assets.register("scss_all", scss)  # 3. register the generated css file, to be used in Jinja templates (see base.html)

@app.route("/")
def frontpage():
    # image, score, json_path, tag_str
    img1 = ("./static/imgs/img1.jpg", 10, "./static/img1.json", "1girl")
    img2 = ("./static/imgs/img2.jpg", 9, "./static/img2.json", "1girl, best quality")
    images = [
        img1, img2
    ]
    cfg = config
    ai_src = config["aiimg_dir"]
    generations = get_generations(ai_src)

    return render_template("home.html", images=generations)





if __name__ == "__main__":
    app.run(host="0.0.0.0",  port=3000,debug=True)
