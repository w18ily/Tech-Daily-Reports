# GitHub Pages 部署指南

## 方式一：GitHub Actions 自动部署（推荐）

### 1. 创建 GitHub 仓库

在 GitHub 上创建新仓库，命名为 `tech-daily-reports`（或任意名称）。

### 2. 推送代码

```bash
cd ~/tech-daily
git init
git add .
git commit -m "init"
git remote add origin https://github.com/你的用户名/tech-daily-reports.git
git push -u origin master
```

### 3. 开启 GitHub Pages

进入仓库 **Settings → Pages**：
- Source: Deploy from a branch
- Branch: `gh-pages` / (root)
- 点击 Save

### 4. 配置完成

- 报告地址：`https://你的用户名.github.io/tech-daily-reports/latest.html`
- 索引页：`https://你的用户名.github.io/tech-daily-reports/`

### 5. 修改 notify_config.json

```json
{
    "wework_webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
    "report_base_url": "https://你的用户名.github.io/tech-daily-reports",
    "local_server_port": 8080
}
```

## 方式二：手动部署脚本

```bash
cd ~/tech-daily
export GITHUB_USER=你的用户名
bash deploy.sh
```

## 方式三：本地 HTTP 服务器（临时）

```bash
cd ~/tech-daily
python3 src/web_server.py
```

报告地址：`http://你的IP:8080/latest.html`

---

## URL 优先级

1. `report_base_url`（GitHub Pages 等外部托管）
2. `http://本机IP:8080/`（本地 HTTP 服务器）
3. `file://...`（本地文件，仅本地查看）
