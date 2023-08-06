https://edaoud.com/blog/2022/02/07/flask-bootstrap-assets/

# Abyss

another stable-diffusion-webui, but made simple


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
```
安装sdtools: https://github.com/troph-team/sdtools

## 使用:
配置文件 → `config.toml`
1. 把webui已经生成的AI图片放到`./static/generated`目录
2. 在项目根目录启动worker: `python ./workers/abyss_runner.py`
   - 接收来自网页的请求, 并在没有请求的时候按照随机词roll图 
3. 启动server: `python app.py`

## Prompt:
生成参数见config.toml:

- `prompt_tag` = `start_tags + {shuffle(vital_tags) + random_tags + end_tags} - taboo_tags`
- tag总个数为`tag_count`
- 使用`txt_dir`作为`random_tags`的词频参考


## TODO:
- 对在库中却没有prompt的图片, 自动补齐prompt: Done
- 多个webui endpoint负载均衡
- 改掉凑数的navbar
- 很多按钮没用,暂时没加(
