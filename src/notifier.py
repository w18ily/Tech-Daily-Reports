#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知推送模块 - 支持钉钉/飞书/企业微信
优化：支持本地服务器链接、报告内容直发、离线模式
"""

import requests
import json
import re
from pathlib import Path


class Notifier:
    def __init__(self, config=None):
        self.config = config or {}

    def _get_local_ip(self):
        """获取本机局域网IP"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _build_report_url(self, report_path=None):
        """
        构建报告访问URL
        优先级: 1.配置中的report_base_url 2.本地HTTP服务器 3.本地文件路径
        """
        # 1. 检查配置中的外部URL（GitHub Pages/云存储）
        base_url = self.config.get('report_base_url', '').rstrip('/')
        if base_url:
            return f"{base_url}/latest.html"

        # 2. 尝试本地HTTP服务器
        local_ip = self._get_local_ip()
        port = self.config.get('local_server_port', 8080)

        # 测试本地服务器是否运行
        try:
            resp = requests.get(f"http://{local_ip}:{port}/latest.html", timeout=2)
            if resp.status_code == 200:
                return f"http://{local_ip}:{port}/latest.html"
        except:
            pass

        # 3. 返回本地文件路径（企业微信无法访问，但保留记录）
        if report_path:
            return f"file://{Path(report_path).absolute()}"

        return None

    def _truncate_text(self, text, max_len=4000):
        """截断文本，保留Markdown格式"""
        if len(text) <= max_len:
            return text

        # 尝试在段落边界截断
        truncated = text[:max_len-20]
        last_newline = truncated.rfind('\n')
        if last_newline > max_len * 0.8:
            truncated = truncated[:last_newline]

        return truncated + "\n\n... (内容已截断)"

    def send_feishu(self, webhook_url, title, content, report_url=None, full_report=None):
        """飞书机器人推送"""
        # 构建消息内容
        msg_text = f"**{title}**\n\n{content}"

        # 如果报告不长，直接嵌入
        if full_report and len(full_report) < 3000:
            msg_text += f"\n\n---\n\n{full_report[:2500]}"
        elif report_url:
            msg_text += f"\n\n[查看完整报告]({report_url})"

        msg = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": self._truncate_text(msg_text, 3000)}
                    }
                ]
            }
        }

        if report_url and (not full_report or len(full_report) >= 3000):
            msg["card"]["elements"].append({
                "tag": "action",
                "actions": [{
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "查看完整报告"},
                    "url": report_url,
                    "type": "primary"
                }]
            })

        try:
            resp = requests.post(webhook_url, json=msg, timeout=10)
            result = resp.json()
            if result.get("code") == 0:
                print(f"   飞书: 推送成功")
                return True
            else:
                print(f"   飞书: 失败 - {result.get('msg', '未知错误')}")
                return False
        except Exception as e:
            print(f"   飞书: 异常 - {e}")
            return False

    def send_dingtalk(self, webhook_url, title, content, report_url=None, full_report=None):
        """钉钉机器人推送"""
        msg_text = f"## {title}\n\n{content}"

        if full_report and len(full_report) < 3000:
            msg_text += f"\n\n---\n\n{full_report[:2500]}"
        elif report_url:
            msg_text += f"\n\n[查看完整报告]({report_url})"

        msg = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": self._truncate_text(msg_text, 5000)
            }
        }

        try:
            resp = requests.post(webhook_url, json=msg, timeout=10)
            result = resp.json()
            if result.get("errcode") == 0:
                print(f"   钉钉: 推送成功")
                return True
            else:
                print(f"   钉钉: 失败 - {result.get('errmsg', '未知错误')}")
                return False
        except Exception as e:
            print(f"   钉钉: 异常 - {e}")
            return False

    def send_wework(self, webhook_url, title, content, report_url=None, full_report=None):
        """企业微信机器人推送 - 优化版"""
        msg_text = f"**{title}**\n\n{content}"

        # 策略1: 如果报告内容不长，直接嵌入推送
        if full_report and len(full_report) < 3500:
            # 清理Markdown，保留格式
            clean_report = full_report[:3000]
            msg_text += f"\n\n---\n\n{clean_report}"

            msg = {
                "msgtype": "markdown",
                "markdown": {
                    "content": self._truncate_text(msg_text, 4000)
                }
            }

        # 策略2: 如果报告太长，发送摘要 + 链接
        elif report_url:
            msg_text += f"\n\n[查看完整报告]({report_url})"
            msg = {
                "msgtype": "markdown",
                "markdown": {
                    "content": self._truncate_text(msg_text, 4000)
                }
            }

        # 策略3: 无链接，纯文本
        else:
            msg_text += "\n\n> 提示: 报告已保存到本地，请查看 output/latest.html"
            msg = {
                "msgtype": "markdown",
                "markdown": {
                    "content": self._truncate_text(msg_text, 4000)
                }
            }

        try:
            resp = requests.post(webhook_url, json=msg, timeout=10)
            result = resp.json()
            if result.get("errcode") == 0:
                print(f"   企业微信: 推送成功")
                return True
            else:
                print(f"   企业微信: 失败 - {result.get('errmsg', '未知错误')}")
                return False
        except requests.exceptions.ConnectionError as e:
            print(f"   企业微信: 网络连接失败 - {e}")
            print(f"   提示: 请检查网络，或启动本地HTTP服务器: python3 src/web_server.py")
            return False
        except Exception as e:
            print(f"   企业微信: 异常 - {e}")
            return False


def push_summary(data, md_path, html_path, config=None):
    """推送日报摘要 - 完整版"""
    config = config or {}
    notifier = Notifier(config)

    # 生成摘要
    topics = [t for t, _ in data.get('topic_heatmap', [])[:5]]
    summary = f"📊 今日科技热点: {', '.join(topics)}\n"
    summary += f"📰 共 **{data['total_articles']}** 篇文章，来自 {data['total_sources']} 个源\n\n"

    # 代表性文章
    summary += "**精选文章**:\n"
    for topic, articles in list(data.get('representative_articles', {}).items())[:3]:
        for article in articles[:2]:
            title = article.get('translated_title', article['title'])
            title = title.replace("[待翻译] ", "")
            summary += f"• {title}\n"

    title = f"TechDaily - {data['date']}"

    # 读取完整报告内容（用于短报告直接发送）
    full_report = None
    if md_path and md_path.exists():
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                full_report = f.read()
        except:
            pass

    # 构建报告URL
    report_url = notifier._build_report_url(html_path)

    print(f"\n📱 推送配置:")
    print(f"   报告URL: {report_url or '未配置（仅本地访问）'}")

    # 推送各渠道
    results = {}

    if config.get('feishu_webhook'):
        results['feishu'] = notifier.send_feishu(
            config['feishu_webhook'], title, summary, report_url, full_report
        )

    if config.get('dingtalk_webhook'):
        results['dingtalk'] = notifier.send_dingtalk(
            config['dingtalk_webhook'], title, summary, report_url, full_report
        )

    if config.get('wework_webhook'):
        results['wework'] = notifier.send_wework(
            config['wework_webhook'], title, summary, report_url, full_report
        )

    if not any([config.get('feishu_webhook'), config.get('dingtalk_webhook'), config.get('wework_webhook')]):
        print("   未配置任何推送渠道")

    return results


if __name__ == "__main__":
    # 测试推送
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("推送模块测试")
        print("请配置 webhook URL 后使用")
