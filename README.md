https://edaoud.com/blog/2022/02/07/flask-bootstrap-assets/

# Abyss

another stable-diffusion-webui, but made simple
- demo: https://abyss.noos.ca/


## 功能:
- 查看本地图片的prompts
- 使用本地prompt一键生成图片
- 生成请求的消息队列
- 在queue空闲时随机生成图片
- 移动端PWA适配


## 安装:
```bash
git clone https://github.com/trojblue/abyss && cd abyss
pip install -r requirements.txt
python app.py
# 在另一个窗口: 运行queue服务
cd workers
python gen_redirect.py
```

## 使用:
配置文件 → `config.toml`

gen_redirect.py的配置: 目前hard-coded

把需要识别的图片放到`./static/generated`目录


## TODO:
- 对在库中却没有prompt的图片, 自动补齐prompt
- 多个webui endpoint负载均衡
