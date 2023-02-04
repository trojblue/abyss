from flask import Flask, render_template, request, send_file, jsonify
from flask_assets import Environment
from flask_ngrok2 import run_with_ngrok
from flask_compress import Compress
import sdtools.txtops
import toml
import requests
from webassets import Bundle
from methods.abs_files import *

app = Flask(__name__)
app.debug = True
# Compress(app)

# 读取设置
with open("config.toml") as f:
    config = toml.load(f)

# https://flask-assets.readthedocs.io/en/latest/#usage
assets = Environment(app)
assets.url = app.static_url_path

app.debug = True
# Scss files
scss = Bundle(
    "assets/process_req.scss",  # 1. will read this scss file and generate a css file based on it
    filters="libsass",  # using this filter: https://webassets.readthedocs.io/en/latest/builtin_filters.html#libsass
    output="css/scss-generated.css",  # 2. and output the generated .css file in the static/css folder
)
assets.register(
    "scss_all", scss
)  # 3. register the generated css file, to be used in Jinja templates (see base.html)


@app.route("/")
def frontpage():
    ai_src = config["aiimg_dir"]
    generations = get_generations(ai_src)
    return render_template("home.html", images=generations)


@app.route("/generate", methods=["POST"])
def generate():
    """
    queue_dst: micro service for load-balancing generation requests
    :return:
    :rtype:
    """
    queue_dst = config["queue_dst"]
    incoming_request = request.values.to_dict()
    response = requests.post(queue_dst, json=incoming_request)

    print(response)
    return


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
