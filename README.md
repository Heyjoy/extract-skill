# extract-skill

> **[中文](#中文) | [English](#english)**

---

## 中文

给 Agent 任何 URL、PDF、DOCX 或图片，零配置转成 Markdown。安装在 Claude Code / Cursor 里即可使用。

### 安装

```bash
git clone https://github.com/Heyjoy/extract-skill.git
claude skill install ./extract-skill
```

或手动复制到 `~/.claude/skills/extract/`。

### 使用

装好后直接用自然语言：

```
帮我把这个 PDF 转成 markdown: /path/to/report.pdf
看看这个链接说了什么: https://example.com/article
提取这个 Word 文档: ~/Documents/spec.docx
这个图片上写了什么: ~/Desktop/screenshot.png
```

### 架构

四层 fallback，本地优先：

1. **Agent WebFetch** — 简单 URL，零成本
2. **本地 Python** — PDF/DOCX，零成本（`pdfplumber` / `mammoth`）
3. **extract-worker** — 复杂 URL / 扫描 PDF，免费配额 50 次/天
4. **用户自带 key** — 配额耗尽后的可选通道

### 支持范围

| 场景 | 状态 | 说明 |
|---|---|---|
| 英文博客 / 文档 / GitHub / Wikipedia | ✅ | |
| 中文站点（雪球 / CSDN / 掘金 / 头条） | ✅ | |
| 微信公众号文章 | ✅ | Worker 云端处理 |
| Twitter / X | ✅ | |
| 日文 / 多语言 | ✅ | |
| 知乎专栏 | ⚠️ | 反爬限制，可能截断 |
| SPA 页面（OpenAI docs 等） | ⚠️ | JS 渲染页，骨架内容 |
| 扫描版 PDF | ⚠️ | 大部分可处理，复杂表格/公式可能丢失 |
| 登录后才可见的内容 | ❌ | 无登录态 |

### 隐私模式

对于机密文件，使用 `--local-only` 参数，文件不会离开本机：

```bash
python3 extract.py --local-only /path/to/confidential.pdf /tmp/output.md
```

### 可选依赖

```bash
pip install pdfplumber mammoth  # 本地 PDF/DOCX 处理，推荐安装，省配额
```

### 合规声明

本工具仅供个人学习、研究和合法用途。使用时请遵守：

- **robots.txt** — 本工具通过第三方 API（Jina Reader 等）获取公开网页内容，这些服务自行处理 robots.txt 合规。本地处理（PDF/DOCX）不涉及爬虫行为。
- **版权与合理使用** — 提取的内容受原始版权保护。用户有责任确保其使用符合当地法律和目标网站的服务条款。本工具不存储、传播或公开提取的内容。
- **速率限制** — 云端处理有每日 50 次免费配额限制，防止滥用。请勿绕过此限制进行批量抓取。
- **禁止事项** — 不得用于：绕过付费墙或访问限制；批量采集用于训练数据集；侵犯他人隐私或知识产权。

使用本工具即表示您同意自行承担合规责任。

---

## English

Feed any URL, PDF, DOCX, or image to your Agent — zero-config conversion to Markdown. Works with Claude Code and Cursor.

### Install

```bash
git clone https://github.com/Heyjoy/extract-skill.git
claude skill install ./extract-skill
```

Or manually copy to `~/.claude/skills/extract/`.

### Usage

Just describe what you need in natural language:

```
Convert this PDF to markdown: /path/to/report.pdf
What does this link say: https://example.com/article
Extract this Word doc: ~/Documents/spec.docx
What's written in this image: ~/Desktop/screenshot.png
```

### Architecture

Four-layer fallback, local-first:

1. **Agent WebFetch** — simple URLs, zero cost
2. **Local Python** — PDF/DOCX via `pdfplumber` / `mammoth`, zero cost
3. **extract-worker** — complex URLs / scanned PDFs, 50 free requests/day
4. **User-provided keys** — optional, when free quota runs out

### Supported Content

| Source | Status | Notes |
|---|---|---|
| English blogs / docs / GitHub / Wikipedia | ✅ | |
| Chinese sites (Xueqiu / CSDN / Juejin) | ✅ | |
| WeChat articles | ✅ | Processed via cloud worker |
| Twitter / X | ✅ | |
| Japanese / multilingual | ✅ | |
| Zhihu columns | ⚠️ | Anti-scraping may truncate content |
| SPA pages (OpenAI docs, etc.) | ⚠️ | JS-rendered, skeleton content only |
| Scanned PDFs | ⚠️ | Most work; complex tables/formulas may be lost |
| Login-required content | ❌ | No auth session |

### Privacy Mode

For confidential files, use `--local-only` — nothing leaves your machine:

```bash
python3 extract.py --local-only /path/to/confidential.pdf /tmp/output.md
```

### Optional Dependencies

```bash
pip install pdfplumber mammoth  # Local PDF/DOCX processing, recommended
```

### Compliance

This tool is intended for personal learning, research, and lawful purposes only.

- **robots.txt** — Web content is fetched via third-party APIs (Jina Reader, etc.) that handle robots.txt compliance on their end. Local processing (PDF/DOCX) involves no crawling.
- **Copyright & fair use** — Extracted content remains under its original copyright. You are responsible for ensuring your use complies with local laws and the target site's terms of service. This tool does not store, redistribute, or publish extracted content.
- **Rate limiting** — Cloud processing is capped at 50 free requests/day to prevent abuse. Do not circumvent this limit for bulk scraping.
- **Prohibited uses** — Do not use this tool to: bypass paywalls or access restrictions; bulk-harvest content for training datasets; infringe on others' privacy or intellectual property.

By using this tool, you accept full responsibility for compliance.

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill metadata + agent instructions |
| `extract.py` | Main entry (4-layer fallback + quality check + cache) |
| `version.json` | Version info |

## Development

```bash
python extract.py https://www.paulgraham.com/greatwork.html
python extract.py /path/to/report.pdf
python extract.py --local-only /path/to/doc.docx /tmp/out.md
```

## License

MIT
