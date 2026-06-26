#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechDaily - 个人科技资讯日报
"""

import os
import json
import hashlib
import re
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Optional

import feedparser
import requests
import yaml

BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"

for d in [OUTPUT_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class TranslationCache:
    def __init__(self, cache_file=None):
        self.cache_file = cache_file or CACHE_DIR / "translation_cache.json"
        self.cache = {}
        self._load()

    def _load(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}

    def _save(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def get(self, text):
        key = hashlib.md5(text.encode()).hexdigest()
        return self.cache.get(key)

    def set(self, text, translation):
        key = hashlib.md5(text.encode()).hexdigest()
        self.cache[key] = translation
        self._save()


class KeywordFilter:
    def __init__(self, config_file):
        self.global_filters = []
        self.word_groups = []
        self._parse_config(config_file)

    def _parse_config(self, config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()

        global_match = re.search(r'\[GLOBAL_FILTER\](.*?)(?=\[WORD_GROUPS\]|$)', content, re.DOTALL)
        if global_match:
            for line in global_match.group(1).strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    self.global_filters.append(self._compile_pattern(line))

        group_pattern = re.compile(r'\[([^\]]+)\](.*?)(?=\[|\Z)', re.DOTALL)
        for match in group_pattern.finditer(content):
            group_name = match.group(1).strip()
            if group_name == 'GLOBAL_FILTER':
                continue
            keywords = []
            for line in match.group(2).strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    keywords.append(self._compile_pattern(line))
            if keywords:
                self.word_groups.append({'name': group_name, 'keywords': keywords})

    def _compile_pattern(self, pattern):
        if pattern.startswith('/') and pattern.endswith('/'):
            try:
                return re.compile(pattern[1:-1], re.IGNORECASE)
            except:
                return re.compile(re.escape(pattern[1:-1]), re.IGNORECASE)
        return re.compile(re.escape(pattern), re.IGNORECASE)

    def is_filtered(self, text):
        for pattern in self.global_filters:
            if pattern.search(text):
                return True
        return False

    def match_groups(self, text):
        matched = []
        for group in self.word_groups:
            for pattern in group['keywords']:
                if pattern.search(text):
                    matched.append(group['name'])
                    break
        return matched


class RSSFetcher:
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch(self, url, name):
        articles = []
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            for entry in feed.entries:
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'published': entry.get('published', ''),
                    'source_name': name,
                    'source_id': url,
                }
                if 'published_parsed' in entry and entry.published_parsed:
                    article['pub_date'] = datetime(*entry.published_parsed[:6])
                else:
                    article['pub_date'] = datetime.now()
                articles.append(article)
        except Exception as e:
            print(f"  [WARN] Fetch failed [{name}]: {e}")
        return articles


class GitHubTrending:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html'
        }

    def fetch(self, language=None, since='daily'):
        repos = []
        url = f'https://github.com/trending/{language or ""}?since={since}'
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            for article in soup.find_all('article', class_='Box-row')[:10]:
                try:
                    h2 = article.find('h2')
                    if not h2:
                        continue
                    repo_link = h2.find('a')
                    if not repo_link:
                        continue

                    repo_name = repo_link.get_text(strip=True).replace('\n', '').replace(' ', '')
                    repo_url = 'https://github.com' + repo_link.get('href', '')

                    desc_p = article.find('p', class_='col-9')
                    description = desc_p.get_text(strip=True) if desc_p else ''

                    lang_span = article.find('span', itemprop='programmingLanguage')
                    language = lang_span.get_text(strip=True) if lang_span else 'Unknown'

                    stars_a = article.find('a', href=lambda x: x and 'stargazers' in x)
                    stars = stars_a.get_text(strip=True) if stars_a else '0'

                    repos.append({
                        'name': repo_name,
                        'url': repo_url,
                        'description': description,
                        'language': language,
                        'stars': stars
                    })
                except:
                    continue
        except Exception as e:
            print(f"  [WARN] GitHub Trending fetch failed: {e}")
        return repos


class ReportGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.date_str = datetime.now().strftime('%Y-%m-%d')

    def generate_markdown(self, data):
        lines = [
            f'# TechDaily - {data["date"]}',
            '',
            f'> 生成时间: {data["generated_at"]} | 数据来源: {data["total_sources"]} 个 RSS 源 | 共 {data["total_articles"]} 篇文章',
            '',
            '---',
            '',
            '## RSS 抓取统计',
            '',
            '| 来源 | 抓取数量 | 匹配数量 | 状态 |',
            '|------|----------|----------|------|'
        ]

        for stat in data['source_stats']:
            status = 'OK' if stat['success'] else 'FAIL'
            lines.append(f"| {stat['name']} | {stat['total']} | {stat['matched']} | {status} |")

        lines.extend(['', '## 主题热度排行', ''])
        for topic, count in data['topic_heatmap']:
            bar = '█' * min(count, 20)
            lines.append(f"- **{topic}**: {count} 篇 {bar}")

        lines.extend(['', '## 来源贡献排行', ''])
        for source, count in data['source_contrib']:
            lines.append(f"- **{source}**: {count} 篇")

        lines.extend(['', '## 代表性文章', ''])
        for topic, articles in data['representative_articles'].items():
            lines.extend([f"### {topic}", ''])
            for article in articles[:5]:
                title = article.get('translated_title', article['title'])
                lines.append(f"- [{title}]({article['link']}) *-- {article['source_name']}*")
            lines.append('')

        lines.extend(['', '## GitHub Trending', ''])
        if data['github_trending']:
            for repo in data['github_trending']:
                desc = repo.get('translated_desc', repo['description'])
                lines.append(f"- **[{repo['name']}]({repo['url']})** `{repo['language']}` ⭐{repo['stars']}")
                lines.append(f"  > {desc}")
                lines.append('')
        else:
            lines.append('> 暂无数据')

        if data.get('ai_analysis'):
            lines.extend(['', '## AI 深度分析', '', data['ai_analysis'], ''])

        lines.extend(['', '---', '', f'*TechDaily - {data["date"]}*'])
        return '\n'.join(lines)

    def generate_html(self, data):
        md = self.generate_markdown(data)
        # 读取HTML模板
        template_path = CONFIG_DIR / "report_template.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
        else:
            # 基础模板 - 使用字符串拼接避免花括号问题
            template = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head><meta charset="UTF-8"><title>TechDaily - ' + data['date'] + '</title></head>\n<body>' + md + '</body></html>'
            return template

        # 简化的 Markdown 转 HTML
        html_content = md.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html_content)
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_content)
        html_content = re.sub(r'^- (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)

        return template.replace('{{DATE}}', data['date']).replace('{{CONTENT}}', html_content).replace('{{GENERATED_AT}}', data['generated_at'])

    def save(self, data):
        md_path = self.output_dir / f"tech-daily-{self.date_str}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.generate_markdown(data))

        html_path = self.output_dir / f"tech-daily-{self.date_str}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self.generate_html(data))

        import shutil
        shutil.copy2(md_path, self.output_dir / "latest.md")
        shutil.copy2(html_path, self.output_dir / "latest.html")

        return md_path, html_path


class TechDaily:
    def __init__(self):
        self.config = self._load_config()
        self.filter = KeywordFilter(CONFIG_DIR / "frequency_words.txt")
        self.fetcher = RSSFetcher()
        self.github = GitHubTrending()
        self.cache = TranslationCache()
        self.reporter = ReportGenerator(OUTPUT_DIR)

        self.rss_feeds = [
            {"id": "hacker-news", "name": "Hacker News", "url": "https://hnrss.org/frontpage"},
            {"id": "arxiv-ai", "name": "arXiv AI", "url": "https://export.arxiv.org/rss/cs.AI"},
            {"id": "arxiv-ml", "name": "arXiv ML", "url": "https://export.arxiv.org/rss/cs.LG"},
            {"id": "hugging-face", "name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml"},
            {"id": "aws-ai", "name": "AWS AI/ML", "url": "https://aws.amazon.com/blogs/machine-learning/feed/"},
            {"id": "google-ai", "name": "Google AI", "url": "https://ai.googleblog.com/feeds/posts/default"},
            {"id": "github-blog", "name": "GitHub Blog", "url": "https://github.blog/feed/"},
            {"id": "infoq", "name": "InfoQ", "url": "https://feed.infoq.com/"},
            {"id": "oschina", "name": "开源中国", "url": "https://www.oschina.net/news/rss"},
            {"id": "solidot", "name": "Solidot", "url": "https://www.solidot.org/index.rss"},
            {"id": "ifanr", "name": "爱范儿", "url": "https://www.ifanr.com/feed"},
        ]

    def _load_config(self):
        with open(CONFIG_DIR / "config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _translate(self, text):
        if not text or not text.strip():
            return text
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            return text

        cached = self.cache.get(text)
        if cached:
            return cached

        translated = f"[待翻译] {text}"
        self.cache.set(text, translated)
        return translated

    def run(self):
        print("=" * 60)
        print("TechDaily - Tech News Daily Generator")
        print("=" * 60)

        all_articles = []
        source_stats = []

        print("\nFetching RSS feeds...")
        for feed in self.rss_feeds:
            print(f"  -> {feed['name']}")
            articles = self.fetcher.fetch(feed['url'], feed['name'])

            matched = []
            for article in articles:
                title = article['title']
                if self.filter.is_filtered(title):
                    continue
                groups = self.filter.match_groups(title)
                if groups:
                    article['matched_groups'] = groups
                    matched.append(article)

            all_articles.extend(matched)
            source_stats.append({
                'name': feed['name'],
                'total': len(articles),
                'matched': len(matched),
                'success': len(articles) > 0
            })
            print(f"    Fetched: {len(articles)}, Matched: {len(matched)}")

        print("\nTranslating...")
        for article in all_articles:
            article['translated_title'] = self._translate(article['title'])

        print("\nAnalyzing...")
        topic_counter = Counter()
        for article in all_articles:
            for group in article.get('matched_groups', []):
                topic_counter[group] += 1
        topic_heatmap = topic_counter.most_common(15)

        source_counter = Counter(a['source_name'] for a in all_articles)
        source_contrib = source_counter.most_common(10)

        representative = defaultdict(list)
        for article in all_articles:
            for group in article.get('matched_groups', []):
                if len(representative[group]) < 5:
                    representative[group].append(article)

        print("\nFetching GitHub Trending...")
        github_repos = self.github.fetch()
        for repo in github_repos:
            repo['translated_desc'] = self._translate(repo['description'])

        now = datetime.now()
        data = {
            'date': now.strftime('%Y-%m-%d'),
            'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'total_sources': len(self.rss_feeds),
            'total_articles': len(all_articles),
            'source_stats': source_stats,
            'topic_heatmap': topic_heatmap,
            'source_contrib': source_contrib,
            'representative_articles': dict(representative),
            'github_trending': github_repos,
            'ai_analysis': None
        }

        print("\nGenerating reports...")
        md_path, html_path = self.reporter.save(data)

        print(f"\nDone!")
        print(f"   Markdown: {md_path}")
        print(f"   HTML:     {html_path}")


        # ===== 推送通知 =====
        print("\n📱 推送通知...")
        try:
            import json
            from pathlib import Path

            notify_config_path = CONFIG_DIR / "notify_config.json"
            if notify_config_path.exists():
                with open(notify_config_path, "r", encoding="utf-8") as f:
                    notify_config = json.load(f)

                # 从 src 目录导入 notifier
                import sys
                sys.path.insert(0, str(BASE_DIR / "src"))
                from notifier import push_summary

                push_summary(data, md_path, html_path, notify_config)
            else:
                print("   未配置 notify_config.json，跳过推送")
                print("   提示: 配置 webhook URL 后可自动推送")
        except Exception as e:
            print(f"   推送异常: {e}")
            import traceback
            traceback.print_exc()
        # ===== 推送结束 =====

        return data, md_path, html_path


if __name__ == "__main__":
    daily = TechDaily()
    daily.run()
