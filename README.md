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
