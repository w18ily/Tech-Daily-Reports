#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信机器人推送测试
用法: python3 test_wework.py "你的webhook地址"
"""

import sys
import requests
import json

def test_wework(webhook_url):
    """测试企业微信机器人推送"""

    # 1. 发送文本消息测试
    text_msg = {
        "msgtype": "text",
        "text": {
            "content": "🚀 TechDaily 测试消息\n\n这是一条来自科技资讯日报的测试推送。\n如果收到此消息，说明 Webhook 配置成功！"
        }
    }

    print(f"正在测试: {webhook_url[:50]}...")
    print("=" * 50)

    try:
        resp = requests.post(webhook_url, json=text_msg, timeout=10)
        result = resp.json()

        if result.get("errcode") == 0:
            print("✅ 文本消息发送成功！")
        else:
            print(f"❌ 发送失败: {result}")
            return False

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

    # 2. 发送 Markdown 消息测试（TechDaily 实际使用的格式）
    md_msg = {
        "msgtype": "markdown",
        "markdown": {
            "content": (
                "**🤖 TechDaily - 科技资讯日报**\n"
                "> 2026-06-26 | 共 15 篇文章\n\n"
                "**今日热点:**\n"
                "- DeepSeek 发布新模型\n"
                "- 英伟达股价创新高\n"
                "- GitHub 开源新工具\n\n"
                "[查看完整报告](https://example.com)"
            )
        }
    }

    try:
        resp = requests.post(webhook_url, json=md_msg, timeout=10)
        result = resp.json()

        if result.get("errcode") == 0:
            print("✅ Markdown 消息发送成功！")
        else:
            print(f"❌ Markdown 发送失败: {result}")

    except Exception as e:
        print(f"❌ Markdown 请求异常: {e}")

    print("=" * 50)
    print("测试完成！")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 test_wework.py \"你的webhook地址\"")
        print("")
        print("示例:")
        print('  python3 test_wework.py "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abc123"')
        sys.exit(1)

    webhook = sys.argv[1]
    test_wework(webhook)
