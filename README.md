# TechDaily - 个人科技资讯日报

基于 TrendRadar 架构定制的个人科技资讯日报系统，专注 AI 模型、基础设施、芯片、机器人等领域。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置通知（可选）
# 编辑 config/notify_config.json，填入 webhook URL

# 3. 运行
bash run.sh

# 4. 设置定时任务（每天上午10点）
bash cron_setup.sh
```

## 项目结构

```
tech-daily/
├── config/              # 配置文件
│   ├── config.yaml      # 主配置
│   ├── frequency_words.txt  # 关键词过滤
│   ├── timeline.yaml    # 调度配置
│   └── report_template.html # HTML模板
├── src/
│   ├── tech_daily.py    # 主程序
│   └── notifier.py      # 推送模块
├── output/              # 报告输出
├── cache/               # 翻译缓存
├── run.sh               # 运行脚本
└── cron_setup.sh        # 定时任务设置
```

## 核心功能

- **RSS 抓取**: 11个精选科技 RSS 源
- **智能过滤**: 关键词匹配 + 全局过滤（排除前端/设计/招聘/营销/官媒）
- **主题分类**: AI模型、AI工程、Agent、MCP、开源工具、基础设施、数据库、芯片、机器人、AI商业化
- **GitHub Trending**: 每日热门仓库
- **翻译缓存**: 避免重复翻译，节省 API 成本
- **双格式输出**: Markdown（归档）+ HTML（阅读）
- **多通道推送**: 钉钉/飞书/企业微信

## 与 TrendRadar 的关系

本项目是 TrendRadar 的**精简定制版**：
- 保留核心架构（RSS聚合、关键词过滤、AI分析、多通道推送）
- 移除热榜平台抓取（更稳定）
- 专注科技领域关键词体系
- 简化部署流程（单脚本运行）

## 自定义

### 添加 RSS 源
编辑 `src/tech_daily.py` 中的 `rss_feeds` 列表。

### 调整关键词过滤
编辑 `config/frequency_words.txt`：
- `[GLOBAL_FILTER]` 区域: 排除不想看的内容
- `[WORD_GROUPS]` 区域: 设置关注的关键词

### 接入 AI 翻译
参考 `AI_TRANSLATION_GUIDE.md`。
