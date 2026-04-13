# extract-skill

用户安装在 Claude Code / Cursor / Claude.ai 里的 skill。给 Agent 任何 URL/PDF/DOCX/图片，零配置转成 Markdown。

## 安装

```bash
# Claude Code
claude skill install ./extract-skill

# 或者手动: 把这个目录复制到 ~/.claude/skills/extract/
```

## 架构

四层 fallback，本地优先：

1. **Agent WebFetch** — 简单 URL，零成本
2. **本地 Python** — PDF/DOCX，零成本（`pdfplumber` / `mammoth`）
3. **extract-worker** — 复杂 URL/扫描 PDF，消耗免费配额 (50/天)
4. **用户自带 key** — 配额耗尽后的可选通道

## 支持范围

| 场景 | 状态 | 说明 |
|---|---|---|
| 英文博客/文档/GitHub/Wikipedia | ✅ | 实测通过 |
| 中文站点（雪球/CSDN/掘金/头条） | ✅ | 实测通过 |
| **微信公众号文章** | ✅ | 通过 Worker 云端处理 |
| **知乎专栏** | ⚠️ 部分 | 反爬限制，内容可能被截断 |
| **SPA 页面** (OpenAI docs 等) | ⚠️ 部分 | JS 渲染页，提取到的是骨架内容 |
| **扫描版 PDF** | ⚠️ 看质量 | 大部分可处理，复杂表格/公式可能丢失 |
| Twitter/X | ✅ | 实测通过 |
| 日文/多语言 | ✅ | 实测通过 |
| 登录后才可见的内容 | ❌ | 无登录态 |

## 文件

| 文件 | 用途 |
|------|------|
| `SKILL.md` | Skill 元数据 + 使用指南（Agent 读） |
| `extract.py` | 主入口（四层 fallback + 质量校验 + 缓存） |
| `version.json` | 版本信息 |

## 开发

```bash
# 本地测试
python extract.py https://www.paulgraham.com/greatwork.html
python extract.py /path/to/report.pdf
python extract.py /path/to/doc.docx
```
