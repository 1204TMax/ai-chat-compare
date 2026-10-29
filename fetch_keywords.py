#!/usr/bin/env python3
"""抓百度下拉词（真实搜索意图，免费且无需 token）

为什么用下拉词而不是"我觉得"：下拉词来自真实搜索框补全，代表有人真的在搜。
谷歌那条接口在本地网络下超时（curl 28），所以用百度这条先跑通。

输出: keywords/baidu-suggest.json  —— 原始结果，保留证据链
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import date

SEEDS = [
    "ai聊天软件", "ai聊天", "ai软件排行榜", "ai软件哪个好用",
    "chatgpt", "claude", "kimi", "deepseek", "豆包", "通义千问", "腾讯元宝",
    "deepseek和", "kimi和", "豆包和", "ai写作",
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def suggest(seed):
    url = "https://suggestion.baidu.com/su?" + urllib.parse.urlencode({"wd": seed})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=10).read().decode("gbk", "ignore")
    # 返回体是 JS 对象（window.baidu.sug({q:"..",p:true,s:[..]})），键名没引号，
    # 所以只把 s:[...] 那段抠出来单独按 JSON 解析，避免整段容错解析
    start = raw.find("s:[")
    if start < 0:
        return []
    arr = raw[start + 2: raw.rfind("]") + 1]
    return json.loads(arr)


def main():
    os.makedirs(OUT, exist_ok=True)
    result = {"fetched_at": date.today().isoformat(), "source": "suggestion.baidu.com/su", "seeds": {}}
    for seed in SEEDS:
        try:
            result["seeds"][seed] = suggest(seed)
            print(f"{seed}: {len(result['seeds'][seed])} 条")
        except Exception as exc:  # 单条失败不影响整体
            result["seeds"][seed] = []
            print(f"{seed}: 失败 {exc}")
    with open(os.path.join(OUT, "baidu-suggest.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
