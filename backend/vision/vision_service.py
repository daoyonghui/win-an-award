"""视觉分析服务：接入 DeepSeek 视觉模型。

对外统一接口：analyze_print_image(image_path)

设计原则：
- API Key 从环境变量 / .env 读取，绝不写死；
- 未配置 API Key 时返回 {"status": "vision_not_configured"}；
- 任何异常都被捕获，绝不抛出，保证 /diagnose 不会崩溃；
- 失败 / 未配置时，调用方（fusion）会继续使用现有 PETG 规则诊断。

成功时返回固定结构：
{
    "defect": "stringing",
    "confidence": 0.85,
    "severity": "medium",
    "visual_evidence": ["模型两结构之间存在明显细丝"]
}
"""

import base64
import json
import logging
import os
import re
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

try:  # 读取本地 .env（如存在）；不会上传任何内容
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv 缺失时安全忽略
    pass

from . import prompts

logger = logging.getLogger("printmind.vision")

ALLOWED_DEFECTS = {"stringing", "under_extrusion", "first_layer_issue", "unknown"}
ALLOWED_SEVERITIES = {"low", "medium", "high"}

# 默认模型；旧名称 "deepseek-v4-flash-vision-exp" 仍可通过环境变量手动指定。
DEFAULT_MODEL = "deepseek-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_TIMEOUT = 60  # 秒

_MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def get_api_key() -> str:
    """读取 API Key（DEEPSEEK_API_KEY 优先，兼容 VISION_API_KEY）。"""
    return (os.getenv("DEEPSEEK_API_KEY") or os.getenv("VISION_API_KEY") or "").strip()


def get_base_url() -> str:
    return (os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")


def get_model() -> str:
    return (
        os.getenv("DEEPSEEK_VISION_MODEL") or os.getenv("VISION_MODEL") or DEFAULT_MODEL
    ).strip()


def get_timeout() -> int:
    try:
        return int(os.getenv("VISION_TIMEOUT", "") or DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


def is_vision_configured() -> bool:
    """是否已配置视觉模型 API Key。"""
    return bool(get_api_key())


def _not_configured(reason: Optional[str] = None) -> dict:
    result = {"status": "vision_not_configured"}
    if reason:
        result["reason"] = reason
    return result


def _error(reason: str) -> dict:
    """失败回退结构：记录原因并交由 fusion 继续使用规则诊断。

    仅记录分类后的原因码，不记录 API Key、图片 base64 或敏感配置。
    """
    logger.warning("vision_analysis_failed reason=%s", reason)
    return {"status": "vision_error", "reason": reason}


def _encode_image(image_path) -> Tuple[Optional[str], Optional[str]]:
    """将本地图片编码为 data URL。返回 (data_url, error_reason)。"""
    path = Path(image_path)
    if not path.exists():
        return None, "image_not_found"

    mime = _MIME_BY_SUFFIX.get(path.suffix.lower())
    if not mime:
        return None, "unsupported_image_type"

    try:
        content = path.read_bytes()
    except OSError:
        return None, "image_read_failed"

    if not content:
        return None, "empty_image"

    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime};base64,{encoded}", None


def _build_payload(data_url: str) -> dict:
    return {
        "model": get_model(),
        "messages": [
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompts.build_analysis_prompt()},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
    }


def _call_deepseek(data_url: str) -> str:
    """调用 DeepSeek 兼容 OpenAI 的 chat/completions 接口，返回模型文本内容。"""
    request = urllib.request.Request(
        f"{get_base_url()}/chat/completions",
        data=json.dumps(_build_payload(data_url)).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_api_key()}",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=get_timeout()) as response:
        raw = response.read().decode("utf-8")

    parsed = json.loads(raw)
    return parsed["choices"][0]["message"]["content"]


def _extract_json(text) -> dict:
    """从模型输出中稳健地提取 JSON（兼容 ```json 代码块与前后噪声）。"""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty_model_content")

    candidate = text.strip()

    fence = _JSON_FENCE_RE.search(candidate)
    if fence:
        candidate = fence.group(1).strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end > start:
            return json.loads(candidate[start : end + 1])
        raise


def _normalize(data: dict) -> dict:
    """规整为固定返回结构，并做取值约束。"""
    defect = str(data.get("defect", "unknown")).strip().lower()
    if defect not in ALLOWED_DEFECTS:
        defect = "unknown"

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    severity = str(data.get("severity", "")).strip().lower()
    if severity not in ALLOWED_SEVERITIES:
        severity = "medium"

    evidence = data.get("visual_evidence") or []
    if isinstance(evidence, str):
        evidence = [evidence]
    if not isinstance(evidence, list):
        evidence = []
    evidence = [str(item).strip() for item in evidence if str(item).strip()]

    return {
        "defect": defect,
        "confidence": round(confidence, 2),
        "severity": severity,
        "visual_evidence": evidence,
    }


def analyze_print_image(image_path) -> dict:
    """分析本地打印件图片。

    参数:
        image_path: 已保存到本地的图片路径（jpg / jpeg / png）。

    返回:
        成功: {"defect", "confidence", "severity", "visual_evidence"}
        未配置: {"status": "vision_not_configured"}
        失败:   {"status": "vision_error", "reason": "..."}
    """
    if not is_vision_configured():
        return _not_configured()

    data_url, encode_error = _encode_image(image_path)
    if encode_error:
        return _error(encode_error)

    try:
        content = _call_deepseek(data_url)
        return _normalize(_extract_json(content))
    except (TimeoutError, socket.timeout):
        return _error("timeout")
    except urllib.error.HTTPError as exc:
        return _error("http_4xx" if 400 <= exc.code < 500 else "http_5xx")
    except urllib.error.URLError:
        return _error("network_error")
    except json.JSONDecodeError:
        return _error("json_parse_error")
    except (KeyError, IndexError, ValueError):
        return _error("invalid_model_response")
    except Exception:  # pragma: no cover - 兜底，保证 /diagnose 不崩溃
        return _error("analysis_failed")
