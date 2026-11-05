"""FastAPI project. Run with: uvicorn app.main:app --reload"""
import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .database import db_enabled, recent_results, save_result
from .engine import analyze_thread
from .predictor import ViSoBERTPredictor, default_model_path
from .schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse, HumanReviewBatch
from .review_store import save_reviews, list_reviews, review_stats, export_csv
from .moderation_adapter import InternalBodyLimit, build_router
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = default_model_path()
    app.state.predictor = None
    app.state.error = None
    if os.path.isdir(model_path):
        try:
            app.state.predictor = ViSoBERTPredictor(model_path)
        except Exception as exc:
            app.state.error = f"Không tải được mô hình: {type(exc).__name__}: {exc}"
    else:
        app.state.error = "Checkpoint chưa được gắn vào MODEL_PATH; không tạo điểm toxic giả."
    yield


app = FastAPI(
    title="Vietnamese Cyberbullying Detection API",
    version="0.3.0",
    description="Prototype AI hỗ trợ kiểm duyệt. Chỉ sử dụng với quyền truy cập hợp lệ; không tự động kết luận hành vi bắt nạt.",
    lifespan=lifespan,
)


def get_predictor(request: Request):
    p = getattr(request.app.state, "predictor", None)
    if p is None:
        raise HTTPException(
            status_code=503,
            detail=getattr(request.app.state, "error", None) or "Model unavailable",
        )
    return p


@app.get("/health", response_model=HealthResponse)
def health(request: Request):
    p = getattr(request.app.state, "predictor", None)
    return HealthResponse(
        status="ready" if p else "model_unavailable",
        model_loaded=p is not None,
        model_path=default_model_path() if p else None,
        details="Sẵn sàng phân tích" if p else (getattr(request.app.state, "error", "Chưa tải mô hình")),
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, predictor=Depends(get_predictor)):
    result = analyze_thread(payload, predictor)
    save_result(result)
    return result


from .signal_engine import analyze_thread_v2
from .schemas import AnalyzeResponseV2

@app.post('/api/v2/analyze', response_model=AnalyzeResponseV2)
def analyze_v2(payload: AnalyzeRequest, predictor=Depends(get_predictor)):
    # Evidence/context are versioned; raw model probabilities remain untouched.
    result = AnalyzeResponseV2.model_validate(analyze_thread_v2(payload, predictor))
    save_result(result)
    return result


@app.post('/api/reviews/batch')
def upsert_reviews(payload: HumanReviewBatch):
    count = save_reviews(payload)
    return {'saved': count, 'thread_id':payload.thread_id, 'reviewer_id':payload.reviewer_id,
            'note':'Không lưu nội dung bình luận; nhãn chỉ phản ánh người đánh giá.'}


@app.get('/api/reviews')
def get_reviews(thread_id: str | None = Query(default=None, max_length=120),
                reviewer_id: str | None = Query(default=None, max_length=30)):
    return {'items': list_reviews(thread_id, reviewer_id)}


@app.get('/api/reviews/stats')
def get_review_stats():
    return review_stats()


@app.get('/api/reviews/export')
def download_reviews(thread_id: str | None = Query(default=None, max_length=120),
                     reviewer_id: str | None = Query(default=None, max_length=30)):
    data = export_csv(list_reviews(thread_id, reviewer_id, limit=100000))
    return Response(content=data, media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition':'attachment; filename="shieldvi_human_reviews.csv"'})


@app.get("/api/recent")
def recent(limit: int = 30):
    if not db_enabled():
        return {"storage_enabled": False, "items": [], "note": "Bật STORE_SUMMARIES=1 để lưu metadata, không lưu nội dung gốc"}
    limit = max(1, min(limit, 100))
    return {"storage_enabled": True, "items": recent_results(limit)}


@app.get("/")
def index():
    return {
        "service": "Vietnamese Cyberbullying Detection API",
        "docs": "/docs",
        "health": "/health",
        "analyze": "POST /api/analyze",
        "notice": "Hỗ trợ kiểm duyệt, không tự động kết luận bắt nạt.",
    }


# Serve the built React dashboard from the SAME origin as the API.
app.add_middleware(InternalBodyLimit)
app.include_router(build_router(get_predictor))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc):
    if request.url.path != "/api/v1/moderate/comment":
        return await request_validation_exception_handler(request, exc)
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": [part if isinstance(part, int) or part in {"body", "query", "path", "header", "cookie"}
                 else "field" for part in error["loc"]], "type": error["type"], "msg": "Invalid moderation payload"}
        for error in exc.errors()
    ]})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc):
    # Model loading dependency runs before the adapter endpoint. Redact its
    # exception/path only for the internal API; preserve legacy responses.
    if request.url.path == "/api/v1/moderate/comment" and exc.status_code >= 500:
        return JSONResponse(status_code=exc.status_code, content={"detail": "Moderation service unavailable"})
    return await http_exception_handler(request, exc)


# Build apps/moderation-web/legacy-v3; Social dashboard has a separate dist.
_DASHBOARD_DIR = Path(__file__).parent / "static"
if (_DASHBOARD_DIR / "index.html").is_file():
    app.mount("/dashboard", StaticFiles(directory=str(_DASHBOARD_DIR), html=True), name="dashboard")
