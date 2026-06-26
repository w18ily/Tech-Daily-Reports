# AI 翻译接入指南

TechDaily 已预留 AI 翻译接口，当前使用占位符 `[待翻译]` 标记。

## 接入方式

修改 `src/tech_daily.py` 中的 `_translate` 方法：

```python
def _translate(self, text):
    if not text or not text.strip():
        return text
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return text

    cached = self.cache.get(text)
    if cached and not cached.startswith('[待翻译]'):
        return cached

    # === 接入 AI 翻译 API ===
    # 方式1: DeepSeek
    # translated = self._translate_with_deepseek(text)

    # 方式2: OpenAI
    # translated = self._translate_with_openai(text)

    # 方式3: 本地模型 (Ollama)
    # translated = self._translate_with_ollama(text)

    # 当前: 占位符
    translated = f"[待翻译] {text}"

    self.cache.set(text, translated)
    return translated

# DeepSeek 翻译示例
def _translate_with_deepseek(self, text):
    import requests
    resp = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": "Bearer YOUR_API_KEY"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "将以下英文科技标题翻译成中文，保留专业术语。"},
                {"role": "user", "content": text}
            ]
        }
    )
    return resp.json()["choices"][0]["message"]["content"]
```

## 环境变量配置

在 `config/config.yaml` 中配置 AI 参数，或在系统环境变量中设置：

```bash
export AI_API_KEY="your-api-key"
export AI_MODEL="deepseek/deepseek-chat"
export AI_BASE_URL="https://api.deepseek.com"
```

## 缓存机制

翻译结果自动缓存到 `cache/translation_cache.json`：
- 键: MD5(原文)
- 值: 翻译结果
- 已翻译内容不会重复调用 API，节省成本
