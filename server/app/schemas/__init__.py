"""Unified Pydantic schema exports for FastAPI routes."""

from .common import BaseResponse, ErrorResponse, PaginationParams, PaginatedResponse, success_response
from .auth import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    EmailVerifyRequest,
    UserResponse,
    LoginResponse,
    RegisterResponse,
)
from .subscription import (
    SubscriptionPlanResponse,
    UserSubscriptionResponse,
    PaymentRecordResponse,
    CreatePaymentRequest,
    ConfirmPaymentRequest,
    UpdateSubscriptionRequest,
    CreateSubscriptionRequest,
    CancelSubscriptionRequest,
)
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
    "UserRegisterRequest",
    "UserLoginRequest",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "EmailVerifyRequest",
    "UserResponse",
    "LoginResponse",
    "RegisterResponse",
    "SubscriptionPlanResponse",
    "UserSubscriptionResponse",
    "PaymentRecordResponse",
    "CreatePaymentRequest",
    "ConfirmPaymentRequest",
    "UpdateSubscriptionRequest",
    "CreateSubscriptionRequest",
    "CancelSubscriptionRequest",
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

