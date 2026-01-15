"""
中医体质判定 API 服务（可线上对外）
基于规则系统的体质分类与判定
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

import anyio
import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from rules import ConstitutionEvidence, rulebook
from security import (
    PayloadTooLargeError,
    RateLimiter,
    RateLimitError,
    UnauthorizedError,
    error_payload,
    get_allowed_origins,
    get_api_keys,
    get_rate_limit_per_minute,
    hash_api_key,
    parse_bearer_token,
)


APP_VERSION = "1.1.0"
MAX_BODY_SIZE = int(os.getenv("MAX_BODY_SIZE", "32768"))
TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "5"))

API_KEYS = get_api_keys()
RATE_LIMITER = RateLimiter(get_rate_limit_per_minute())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)
logger = logging.getLogger("constitution_api")


app = FastAPI(
    title="中医体质判定 API",
    description="基于规则系统的中医体质分类与判定服务（非医疗诊断）",
    version=APP_VERSION,
)

allowed_origins = get_allowed_origins()
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# 请求模型
class MetaInfo(BaseModel):
    """元信息"""
    age: Optional[int] = Field(None, description="年龄")
    sex: Optional[str] = Field(None, description="性别：M/F")
    region: Optional[str] = Field(None, description="地区")
    notes: Optional[str] = Field(None, description="备注")


class ConstitutionRequest(BaseModel):
    """体质判定请求"""
    text: str = Field(..., description="症状/习惯/舌苔/脉象等描述（中文）", min_length=1)
    meta: Optional[MetaInfo] = Field(None, description="元信息（可选）")


# 响应模型
class EvidenceItem(BaseModel):
    """证据项"""
    type: str
    score: float
    matched: List[Dict[str, Any]]


class Recommendations(BaseModel):
    """建议"""
    lifestyle: List[str]
    diet: List[str]
    when_to_seek_help: List[str]


class ConstitutionResponse(BaseModel):
    """体质判定响应"""
    primary_type: str
    secondary_types: List[str]
    confidence: float
    evidence: List[EvidenceItem]
    recommendations: Recommendations
    questions_to_clarify: List[str]
    disclaimer: str


def format_evidence(evidence: ConstitutionEvidence) -> Dict[str, Any]:
    """格式化证据为响应格式"""
    return {
        "type": evidence.type,
        "score": round(evidence.score, 2),
        "matched": [
            {
                "keyword": match.keyword,
                "weight": match.weight,
                "span": match.span
            }
            for match in evidence.matched
        ]
    }


def verify_api_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    token = parse_bearer_token(auth_header)
    if not token:
        raise UnauthorizedError("缺少或无效的 Authorization: Bearer <API_KEY>")

    if not API_KEYS or token not in API_KEYS:
        raise UnauthorizedError("API Key 无效")

    RATE_LIMITER.check(token)
    api_key_hash = hash_api_key(token)
    request.state.api_key_hash = api_key_hash
    return token


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    start_time = time.time()
    response: Optional[JSONResponse] = None

    try:
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length and content_length.isdigit():
                if int(content_length) > MAX_BODY_SIZE:
                    raise PayloadTooLargeError(
                        f"请求体大小超过限制 {MAX_BODY_SIZE} 字节"
                    )
            body = await request.body()
            if len(body) > MAX_BODY_SIZE:
                raise PayloadTooLargeError(
                    f"请求体大小超过限制 {MAX_BODY_SIZE} 字节"
                )

        with anyio.fail_after(TIMEOUT_SECONDS):
            response = await call_next(request)

    except PayloadTooLargeError as exc:
        response = JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message, trace_id),
        )
    except RateLimitError as exc:
        response = JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message, trace_id),
        )
    except UnauthorizedError as exc:
        response = JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message, trace_id),
        )
    except Exception as exc:
        if isinstance(exc, anyio.exceptions.TimeoutError):
            response = JSONResponse(
                status_code=504,
                content=error_payload("TIMEOUT", "请求处理超时", trace_id),
            )
        else:
            response = JSONResponse(
                status_code=500,
                content=error_payload("INTERNAL_ERROR", "服务器内部错误", trace_id),
            )

    latency_ms = int((time.time() - start_time) * 1000)
    status_code = response.status_code if response else 500
    api_key_hash = getattr(request.state, "api_key_hash", "-")
    logger.info(
        "path=%s status=%s latency_ms=%s api_key_hash=%s trace_id=%s",
        request.url.path,
        status_code,
        latency_ms,
        api_key_hash,
        trace_id,
    )

    response.headers["X-Trace-Id"] = trace_id
    return response


@app.get("/health")
async def health_check():
    """健康检查端点（对外开放，便于平台健康检查）"""
    return {"ok": True}


@app.get("/version")
async def version():
    """版本信息（对外开放）"""
    return {"version": APP_VERSION}


@app.post("/v1/constitution/estimate", response_model=ConstitutionResponse, dependencies=[Depends(verify_api_key)])
async def estimate_constitution(request: ConstitutionRequest):
    """
    体质判定端点

    根据用户输入的症状描述，判定体质类型并给出建议。
    注意：这不是医疗诊断，仅供参考。
    """
    analysis_result = rulebook.analyze(request.text)

    if analysis_result.get("primary_type") == "信息不足":
        return ConstitutionResponse(
            primary_type="信息不足",
            secondary_types=[],
            confidence=0.0,
            evidence=[],
            recommendations=Recommendations(
                lifestyle=[],
                diet=[],
                when_to_seek_help=["请补充更多症状信息后重新判定"],
            ),
            questions_to_clarify=rulebook.get_common_questions(),
            disclaimer="本服务仅供参考，不构成医疗诊断。如有健康问题，请咨询专业医生或中医师。",
        )

    primary_type = analysis_result["primary_type"]
    secondary_types = analysis_result.get("secondary_types", [])
    confidence = analysis_result.get("confidence", 0.0)

    evidence_list = []
    evidence_dict = analysis_result.get("evidence", {})
    for const_type in [primary_type] + secondary_types:
        if const_type in evidence_dict:
            evidence_list.append(format_evidence(evidence_dict[const_type]))

    recommendations_dict = rulebook.get_recommendations(primary_type)
    recommendations = Recommendations(
        lifestyle=recommendations_dict.get("lifestyle", []),
        diet=recommendations_dict.get("diet", []),
        when_to_seek_help=recommendations_dict.get("when_to_seek_help", []),
    )

    questions_to_clarify = []
    if confidence < 0.5:
        questions_to_clarify = rulebook.get_common_questions()

    disclaimer = (
        "本服务基于规则系统进行体质倾向性分析，仅供参考，不构成医疗诊断。"
        "不提供疾病诊断、用药建议或处方。如有健康问题，请咨询专业医生或中医师。"
        "本服务不对任何医疗决策负责。"
    )

    return ConstitutionResponse(
        primary_type=primary_type,
        secondary_types=secondary_types,
        confidence=round(confidence, 3),
        evidence=evidence_list,
        recommendations=recommendations,
        questions_to_clarify=questions_to_clarify,
        disclaimer=disclaimer,
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
