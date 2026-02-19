"""Unified Pydantic schema exports for FastAPI routes.
简化版 - 无用户系统
"""

from .common import BaseResponse, ErrorResponse, PaginationParams, PaginatedResponse, success_response
from .live_audio import (
    StartLiveAudioRequest,
    LiveAudioAdvancedRequest,
    LiveAudioPreloadRequest,
)
from .live_report import StartLiveReportRequest
from .douyin import (
    StartDouyinMonitoringRequest,
    DouyinStatusResponse,
)
from .ai import (
    StartAILiveAnalysisRequest,
    GenerateLiveAnswersRequest,
    GenerateOneScriptRequest,
    SubmitScriptFeedbackRequest,
)

__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "success_response",
    "StartLiveAudioRequest",
    "LiveAudioAdvancedRequest",
    "LiveAudioPreloadRequest",
    "StartLiveReportRequest",
    "StartDouyinMonitoringRequest",
    "DouyinStatusResponse",
    "StartAILiveAnalysisRequest",
    "GenerateLiveAnswersRequest",
    "GenerateOneScriptRequest",
    "SubmitScriptFeedbackRequest",
]
