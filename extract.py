"""
extract-skill — 任意素材 → Markdown
Skill 客户端，只调 Worker API + 本地 pdfplumber/mammoth。
不含任何内部基础设施信息。
"""
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# === Config ===

WORKER_URL = os.environ.get("EXTRACT_WORKER_URL", "https://extract-worker.mirrorsverse.workers.dev")
CACHE_DIR = Path(os.environ.get("EXTRACT_CACHE_DIR", os.path.expanduser("~/.cache/extract-skill")))
CACHE_TTL = int(os.environ.get("EXTRACT_CACHE_TTL", "604800"))

# --local-only: 不调任何网络服务，仅用本地 pdfplumber/mammoth
LOCAL_ONLY = os.environ.get("EXTRACT_LOCAL_ONLY", "").lower() in ("1", "true", "yes")


# === Type Detection ===

def detect_type(source: str) -> str:
    if source.startswith(("http://", "https://")):
        return "url"
    ext = Path(source).suffix.lower()
    type_map = {
        ".pdf": "pdf", ".docx": "docx", ".doc": "docx",
        ".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image", ".gif": "image",
        ".epub": "ebook", ".mobi": "ebook",
    }
    return type_map.get(ext, "text")


# === Quality Check ===

ANTI_CRAWL_PATTERNS = re.compile(
    r"请开启\s*JavaScript|403 Forbidden|Access Denied|Cloudflare|Just a moment",
    re.IGNORECASE,
)

def quality_check(text: str, source_type: str = "") -> dict:
    warnings = []
    if len(text.strip()) < 200:
        warnings.append("too_short")
    if text:
        def is_normal(c):
            cp = ord(c)
            if cp < 0x80: return True
            if 0x4E00 <= cp <= 0x9FFF: return True
            if 0x3000 <= cp <= 0x303F: return True
            if 0xFF00 <= cp <= 0xFFEF: return True
            if 0x2000 <= cp <= 0x206F: return True
            if c.isalpha() or c.isdigit(): return True
            return False
        weird = sum(1 for c in text if not is_normal(c))
        if weird / max(len(text), 1) > 0.05:
            warnings.append("garbled")
    if ANTI_CRAWL_PATTERNS.search(text[:2000]):
        warnings.append("anti_crawl_page")
    confidence = max(0.0, 1.0 - len(warnings) * 0.3)
    return {"ok": len(warnings) == 0, "confidence": confidence, "warnings": warnings}


# === Cache ===

def cache_key(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()[:16]

def cache_get(source: str) -> Optional[dict]:
    p = CACHE_DIR / f"{cache_key(source)}.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        import time
        if time.time() - data.get("ts", 0) > CACHE_TTL:
            p.unlink(missing_ok=True)
            return None
        return data
    except Exception:
        return None

def cache_set(source: str, result: dict):
    import time
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    result["ts"] = time.time()
    (CACHE_DIR / f"{cache_key(source)}.json").write_text(json.dumps(result, ensure_ascii=False))


# === Local Processing (--local-only 的唯一引擎) ===

def local_pdf(path: str) -> Optional[str]:
    try:
        import pdfplumber
    except ImportError:
        return None
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    md = "\n\n---\n\n".join(pages)
    if pages and len(md) / max(len(pages), 1) < 50:
        return None  # 可能是扫描版
    return md

def local_docx(path: str) -> Optional[str]:
    try:
        import mammoth
    except ImportError:
        return None
    with open(path, "rb") as f:
        result = mammoth.convert_to_markdown(f)
    return result.value

def local_text(path: str) -> Optional[str]:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return None


# === Worker API ===

def call_worker(source: str, kind: str) -> Optional[str]:
    """调用 extract-worker。Worker 内部决定走哪个后端。"""
    import urllib.request
    import urllib.parse
    import urllib.error

    headers = {"User-Agent": "extract-skill/0.1"}

    try:
        if kind == "url":
            url = f"{WORKER_URL}/extract?url={urllib.parse.quote(source, safe='')}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        if kind == "pdf":
            boundary = "----ExtractSkillBoundary"
            filename = os.path.basename(source)
            with open(source, "rb") as f:
                file_data = f.read()
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: application/pdf\r\n\r\n"
            ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
            req = urllib.request.Request(
                f"{WORKER_URL}/pdf",
                data=body,
                headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read().decode("utf-8")
        return None
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return None
        return None
    except Exception:
        return None


# === Progress + Health ===

def _progress(msg: str):
    """进度输出到 stderr — Agent 和用户都能看到, 不污染 stdout 结果。"""
    import sys
    print(f"[extract] {msg}", file=sys.stderr, flush=True)


def _worker_healthy() -> bool:
    """快速检查 Worker /health (2s timeout)。返回 False = Worker 挂了。"""
    import urllib.request, urllib.error
    try:
        req = urllib.request.Request(
            f"{WORKER_URL}/health",
            headers={"User-Agent": "extract-skill-health/1.0"},
        )
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


# === Main Entry ===

def extract(source: str) -> dict:
    """
    主入口。
    - 正常模式: 调 Worker（Worker 内部决定使用哪个后端）
    - --local-only: 仅用本地 pdfplumber/mammoth
    """
    cached = cache_get(source)
    if cached:
        cached["meta"]["from_cache"] = True
        return cached

    kind = detect_type(source)
    result = {"content": "", "meta": {"source": source, "type": kind, "engine": "", "layer": 0, "confidence": 0, "chars": 0, "warnings": []}}

    # === Local-only 模式: 只用本地引擎 ===
    if LOCAL_ONLY:
        md = None
        if kind == "pdf":
            md = local_pdf(source)
            engine = "local_pdfplumber"
        elif kind == "docx":
            md = local_docx(source)
            engine = "local_mammoth"
        elif kind == "text":
            md = local_text(source)
            engine = "local_text"
        else:
            result["meta"]["warnings"] = ["local_only_unsupported_type"]
            result["meta"]["suggestion"] = "本地隐私模式不支持 URL 提取，请选择云转换模式"
            return result

        if md:
            qc = quality_check(md, kind)
            result.update(content=md, meta={**result["meta"], "engine": engine, "layer": 1, "confidence": qc["confidence"], "chars": len(md), "warnings": qc["warnings"]})
            cache_set(source, result)
        else:
            result["meta"]["warnings"] = ["local_extraction_failed"]
        return result

    # === 正常模式（云优先）===
    # PDF/URL → Worker（Worker 内部路由: Tunnel→内网引擎 或 fallback→Jina/LlamaParse）
    # DOCX/text → 本地处理（Worker 没有 DOCX 端点）

    if kind == "docx":
        md = local_docx(source)
        if md:
            qc = quality_check(md, kind)
            result.update(content=md, meta={**result["meta"], "engine": "local_mammoth", "layer": 1, "confidence": qc["confidence"], "chars": len(md)})
            cache_set(source, result)
            return result

    elif kind == "text":
        md = local_text(source)
        if md:
            result.update(content=md, meta={**result["meta"], "engine": "local_text", "layer": 1, "confidence": 1.0, "chars": len(md)})
            cache_set(source, result)
            return result

    # URL / PDF → Worker 云端处理
    if kind in ("url", "pdf"):
        # 预检: Worker 是否在线
        _progress(f"正在连接云端服务...")
        if not _worker_healthy():
            _progress("⚠️ 云端服务暂时不可用")
            # PDF fallback 到本地 pdfplumber（如果有的话）
            if kind == "pdf":
                _progress("尝试本地处理...")
                md = local_pdf(source)
                if md:
                    qc = quality_check(md, kind)
                    if qc["ok"]:
                        result.update(content=md, meta={**result["meta"], "engine": "local_pdfplumber", "layer": 1, "confidence": qc["confidence"], "chars": len(md)})
                        cache_set(source, result)
                        return result
            result["meta"]["warnings"] = ["worker_unavailable"]
            result["meta"]["suggestion"] = "云端服务暂时不可用。请稍后重试，或使用 --local-only 模式本地处理。"
            return result

        # 上传 + 处理
        if kind == "pdf":
            file_size = os.path.getsize(source)
            _progress(f"上传 PDF ({file_size // 1024}KB)...")
        else:
            _progress(f"提取中...")

        md = call_worker(source, kind)
        if md:
            qc = quality_check(md, kind)
            if qc["ok"]:
                _progress("完成")
                result.update(content=md, meta={**result["meta"], "engine": "worker", "layer": 2, "confidence": qc["confidence"], "chars": len(md)})
                cache_set(source, result)
                return result
            _progress(f"云端返回内容质量不足 ({qc['warnings']})")

        # PDF 云端失败 → 最后 fallback 到本地 pdfplumber
        if kind == "pdf":
            _progress("云端处理失败，尝试本地 pdfplumber...")
            md = local_pdf(source)
            if md:
                qc = quality_check(md, kind)
                if qc["ok"]:
                    result.update(content=md, meta={**result["meta"], "engine": "local_pdfplumber", "layer": 1, "confidence": qc["confidence"], "chars": len(md), "warnings": ["cloud_failed_local_fallback"]})
                    cache_set(source, result)
                    return result

    # 全部失败
    result["meta"]["warnings"] = ["all_layers_failed"]
    result["meta"]["suggestion"] = (
        "提取失败。可能原因:\n"
        "1. URL/文件路径不正确\n"
        "2. 需要登录才能访问的页面\n"
        "3. 云端服务暂时不可用 — 稍后重试或用 --local-only 模式"
    )
    return result


def extract_to_file(source: str, output_path: str = None) -> dict:
    """提取内容并写到文件。"""
    r = extract(source)
    if not r["content"]:
        return r
    if output_path is None:
        output_dir = Path(os.environ.get("EXTRACT_OUTPUT_DIR", "/tmp"))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"extract_{cache_key(source)}.md")
    Path(output_path).write_text(r["content"], encoding="utf-8")
    r["meta"]["output_path"] = output_path
    return r


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if not args:
        print("Usage: python extract.py [--local-only] <url_or_path> [output_path]")
        print("  --local-only  本地隐私模式，文件不离开本机")
        sys.exit(1)
    if "--local-only" in flags:
        LOCAL_ONLY = True
    output = args[1] if len(args) > 1 else None
    r = extract_to_file(args[0], output)
    if r["content"]:
        out = r["meta"].get("output_path", "stdout")
        print(f"✅ 已提取到 {out} ({r['meta']['chars']} 字, engine={r['meta']['engine']}, layer={r['meta']['layer']})")
    else:
        print(f"❌ Failed: {json.dumps(r['meta'], ensure_ascii=False)}")
