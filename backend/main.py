"""
ShadeSense AI — Backend API
FastAPI server that processes face images, detects skin tone + undertone,
and recommends matching foundation products.
"""

import os
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
import numpy as np
import cv2
from PIL import Image
import io
import json
import traceback


def sanitize(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

from modules.lighting import normalize_lighting, assess_lighting_quality, assess_capture_quality
from modules.face_detection import FaceDetector
from modules.skin_analysis import SkinAnalyzer
from modules.intent_parser import IntentParser
from modules.recommender import Recommender
from modules.virtual_tryon import apply_virtual_tryon
from modules.look_generator import LookGenerator
from modules.shade_comparison import ShadeComparator, validate_hex_color
from modules.feedback_store import FeedbackStore

# ─── Initialize App ───────────────────────────────────────────────
app = FastAPI(
    title="ShadeSense AI",
    description="AI-powered makeup shade recommendation system",
    version="1.0.0"
)

# ─── CORS (allow frontend to call backend) ────────────────────────
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
allowed_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX") or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_request_log = defaultdict(deque)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


@app.middleware("http")
async def request_observability_and_rate_limit(request: Request, call_next):
    """Add lightweight request timing and in-memory rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    recent = _request_log[client_ip]
    while recent and now - recent[0] > RATE_LIMIT_WINDOW:
        recent.popleft()
    if len(recent) >= RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"success": False, "error": "Too many requests. Please slow down and try again."},
        )
    recent.append(now)

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-ms"] = f"{duration_ms:.1f}"
    print(f"{request.method} {request.url.path} {response.status_code} {duration_ms:.1f}ms")
    return response

# ─── Initialize Modules ───────────────────────────────────────────
face_detector = FaceDetector()
skin_analyzer = SkinAnalyzer()
intent_parser = IntentParser()
recommender = Recommender()
look_generator = LookGenerator()
shade_comparator = ShadeComparator()
feedback_store = FeedbackStore()


class FeedbackPayload(BaseModel):
    session_id: Optional[str] = None
    skin_hex: str = Field(..., min_length=6, max_length=7)
    predicted_shade: Optional[str] = None
    selected_product_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    actual_match: Optional[str] = Field(default=None, pattern="^(too_light|too_dark|too_warm|too_cool|good_match)$")
    corrected_hex: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=500)


# ─── Health Check ──────────────────────────────────────────────────
@app.get("/")
async def root():
    """Friendly root response for hosting platform probes and direct browser visits."""
    return {
        "status": "ok",
        "service": "ShadeSense AI",
        "message": "Backend API is running.",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Avoid noisy 404s when browsers request a favicon from the API host."""
    return Response(status_code=204)


@app.get("/api/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {"status": "ok", "service": "ShadeSense AI", "version": "1.0.0"}


# ─── Helpers ───────────────────────────────────────────────────────
async def _read_image(image: UploadFile):
    """Validate and read an uploaded image into a BGR numpy array."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image file (JPEG, PNG, or WebP)."
        )

    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image is too large. Please upload an image under 10MB."
        )

    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(
            status_code=400,
            detail="Could not read the image. Please try a different file."
        )

    max_dim = 1024
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    return img


def _build_single_result(img, text, product_type):
    """Run the full analysis pipeline for a single face and return a response dict."""
    lighting_quality = assess_lighting_quality(img)

    # Detect face before lighting normalization (normalization can break detection)
    face_result = face_detector.detect_face(img)
    if "error" in face_result:
        return {"success": False, "error": face_result["error"]}

    capture_quality = assess_capture_quality(img, face_result["face_bbox"])

    # Now normalize lighting for better skin color extraction
    img = normalize_lighting(img)
    # Re-extract skin regions from normalized image using the same face bbox
    fx = face_result["face_bbox"]["x"]
    fy = face_result["face_bbox"]["y"]
    fw = face_result["face_bbox"]["width"]
    fh = face_result["face_bbox"]["height"]
    face_result["skin_regions"] = face_detector._extract_skin_regions(img, fx, fy, fw, fh)

    skin_pixels = face_result["skin_regions"]["all_pixels"]
    region_pixels = face_result["skin_regions"]["regions"]
    skin_data = skin_analyzer.analyze(skin_pixels, region_pixels=region_pixels)

    if "error" in skin_data:
        return {"success": False, "error": skin_data["error"]}

    if lighting_quality["label"] == "poor":
        skin_data["confidence"] = round(max(0.35, skin_data.get("confidence", 0.7) - 0.12), 2)
    if capture_quality["label"] == "low":
        skin_data["confidence"] = round(max(0.30, skin_data.get("confidence", 0.7) - 0.10), 2)

    intent = intent_parser.parse(text)
    style_tips = intent_parser.get_style_tips(intent)

    products = recommender.recommend(skin_data, intent, top_n=5,
                                     product_type=product_type)

    # Shade comparisons for each product
    product_hexes = [p["hex_color"] for p in products]
    shade_comparisons = shade_comparator.compare_shades(skin_data["hex_color"], product_hexes)
    shade_map = {sc["hex_color"]: sc for sc in shade_comparisons}

    # Generate complete look
    all_products = recommender.products
    complete_look = look_generator.generate_look(skin_data, intent, all_products)

    return {
        "success": True,
        "skin_analysis": {
            "hex_color": skin_data["hex_color"],
            "rgb": skin_data["rgb"],
            "shade_name": skin_data["shade_name"],
            "shade_code": skin_data["shade_code"],
            "undertone": skin_data["undertone"],
            "undertone_description": skin_data["undertone_description"],
            "confidence": skin_data["confidence"],
            "ita_angle": skin_data["ita_angle"],
            "ita_category": skin_data["ita_category"],
            "skin_health_indicators": skin_data["skin_health_indicators"],
            "color_harmony": skin_data["color_harmony"],
            "ml_skin_tone": skin_data.get("ml_skin_tone"),
            "lighting_quality": lighting_quality,
            "capture_quality": capture_quality,
            "sample_quality": skin_data.get("sample_quality"),
        },
        "intent": {
            "occasion": intent["occasion"],
            "look": intent["look"],
            "coverage": intent["coverage"],
            "finish": intent["finish"],
            "preferences_detected": intent["preferences_detected"]
        },
        "recommendations": [
            {
                "id": p["id"],
                "brand": p["brand"],
                "line": p["line"],
                "shade_code": p["shade_code"],
                "shade_name": p["shade_name"],
                "hex_color": p["hex_color"],
                "finish": p["finish"],
                "coverage": p["coverage"],
                "price": p["price"],
                "match_percentage": p["match_percentage"],
                "image_url": p["image_url"],
                "buy_url": p["buy_url"],
                "type": p.get("type", product_type),
                "score_breakdown": p.get("score_breakdown", {}),
                "recommendation_explanation": p.get("recommendation_explanation", []),
                "shade_comparison": shade_map.get(p["hex_color"], {}),
            }
            for p in products
        ],
        "complete_look": complete_look,
        "style_tips": style_tips
    }


# ─── Main Analysis Endpoint ───────────────────────────────────────
@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(..., description="Face selfie image"),
    text: str = Form(default="", description="User preferences text"),
    product_type: str = Form(default="all", description="Product type to recommend")
):
    """
    Main endpoint: Analyze a face image and return shade recommendations.

    Steps:
    1. Validate image
    2. Normalize lighting
    3. Detect face
    4. Extract skin tone
    5. Parse user intent
    6. Generate recommendations
    """
    try:
        if product_type not in {"all", "foundation", "lipstick", "blush", "concealer"}:
            raise HTTPException(status_code=400, detail="Unsupported product type.")
        img = await _read_image(image)
        result = _build_single_result(img, text, product_type)

        if not result.get("success"):
            return JSONResponse(status_code=200, content=sanitize(result))

        return sanitize(result)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during analysis: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Something went wrong while analyzing your image. Please try again."
            }
        )


@app.post("/api/feedback")
async def submit_feedback(payload: FeedbackPayload):
    """Capture real user correction data for future ranking/model improvements."""
    try:
        skin_hex = validate_hex_color(payload.skin_hex)
        corrected_hex = validate_hex_color(payload.corrected_hex) if payload.corrected_hex else None
        event = feedback_store.record({
            "session_id": payload.session_id,
            "skin_hex": skin_hex,
            "predicted_shade": payload.predicted_shade,
            "selected_product_id": payload.selected_product_id,
            "rating": payload.rating,
            "actual_match": payload.actual_match,
            "corrected_hex": corrected_hex,
            "notes": payload.notes,
        })
        recommender.reload_feedback()
        return sanitize({"success": True, "feedback_id": event["id"]})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Multi-Face Analysis Endpoint ─────────────────────────────────
@app.post("/api/analyze-multi")
async def analyze_multi(
    image: UploadFile = File(..., description="Face selfie image"),
    text: str = Form(default="", description="User preferences text"),
    product_type: str = Form(default="all", description="Product type to recommend")
):
    """
    Detect ALL faces in an image and return analysis results for each.
    """
    try:
        if product_type not in {"all", "foundation", "lipstick", "blush", "concealer"}:
            raise HTTPException(status_code=400, detail="Unsupported product type.")
        img = await _read_image(image)
        lighting_quality = assess_lighting_quality(img)

        face_results = face_detector.detect_face(img, multi_face=True)

        if isinstance(face_results, dict) and "error" in face_results:
            return JSONResponse(
                status_code=200,
                content=sanitize({"success": False, "error": face_results["error"]})
            )

        intent = intent_parser.parse(text)
        style_tips = intent_parser.get_style_tips(intent)
        all_results = []

        for face_result in face_results:
            skin_pixels = face_result["skin_regions"]["all_pixels"]
            skin_data = skin_analyzer.analyze(skin_pixels)

            if "error" in skin_data:
                all_results.append(sanitize({
                    "success": False,
                    "error": skin_data["error"],
                    "face_bbox": face_result["face_bbox"]
                }))
                continue

            products = recommender.recommend(skin_data, intent, top_n=5,
                                             product_type=product_type)
            product_hexes = [p["hex_color"] for p in products]
            shade_comparisons = shade_comparator.compare_shades(skin_data["hex_color"], product_hexes)
            shade_map = {sc["hex_color"]: sc for sc in shade_comparisons}

            all_results.append(sanitize({
                "success": True,
                "face_bbox": face_result["face_bbox"],
                "skin_analysis": {
                    "hex_color": skin_data["hex_color"],
                    "rgb": skin_data["rgb"],
                    "shade_name": skin_data["shade_name"],
                    "shade_code": skin_data["shade_code"],
                    "undertone": skin_data["undertone"],
                    "undertone_description": skin_data["undertone_description"],
                    "confidence": skin_data["confidence"],
                    "ita_angle": skin_data.get("ita_angle"),
                    "ita_category": skin_data.get("ita_category"),
                    "skin_health_indicators": skin_data.get("skin_health_indicators"),
                    "color_harmony": skin_data.get("color_harmony"),
                    "ml_skin_tone": skin_data.get("ml_skin_tone"),
                    "lighting_quality": lighting_quality,
                },
                "intent": {
                    "occasion": intent["occasion"],
                    "look": intent["look"],
                    "coverage": intent["coverage"],
                    "finish": intent["finish"],
                    "preferences_detected": intent["preferences_detected"]
                },
                "recommendations": [
                    {
                        "id": p["id"],
                        "brand": p["brand"],
                        "line": p["line"],
                        "shade_code": p["shade_code"],
                        "shade_name": p["shade_name"],
                        "hex_color": p["hex_color"],
                        "finish": p["finish"],
                        "coverage": p["coverage"],
                        "price": p["price"],
                        "match_percentage": p["match_percentage"],
                        "image_url": p["image_url"],
                        "buy_url": p["buy_url"],
                        "type": p.get("type", product_type),
                        "score_breakdown": p.get("score_breakdown", {}),
                        "recommendation_explanation": p.get("recommendation_explanation", []),
                        "shade_comparison": shade_map.get(p["hex_color"], {}),
                    }
                    for p in products
                ],
                "style_tips": style_tips
            }))

        return sanitize({"success": True, "faces": all_results, "count": len(all_results)})

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during multi-analysis: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Something went wrong while analyzing your image. Please try again."
            }
        )


# ─── Virtual Try-On Endpoint ──────────────────────────────────────
@app.post("/api/tryon")
async def tryon(
    image: UploadFile = File(..., description="Face selfie image"),
    hex_color: str = Form(..., description="Hex color to apply"),
    product_type: str = Form(default="foundation", description="Product type: foundation, lipstick, blush, concealer")
):
    """
    Apply virtual try-on: overlay a makeup color on the face and return
    the modified image as JPEG.
    """
    try:
        hex_color = validate_hex_color(hex_color)
        img = await _read_image(image)
        img = normalize_lighting(img)

        face_result = face_detector.detect_face(img)

        if "error" in face_result:
            return JSONResponse(
                status_code=200,
                content=sanitize({"success": False, "error": face_result["error"]})
            )

        result_img = apply_virtual_tryon(
            img, face_result["face_bbox"], product_type, hex_color
        )

        _, encoded = cv2.imencode(".jpg", result_img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return Response(content=encoded.tobytes(), media_type="image/jpeg")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error during tryon: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Something went wrong during virtual try-on. Please try again."
            }
        )


# ─── Find Dupes Endpoint ──────────────────────────────────────────
@app.post("/api/find-dupes")
async def find_dupes(
    hex_color: str = Form(..., description="Hex color to find dupes for"),
):
    """Find products that are color-close (dupes) to a given hex color."""
    try:
        hex_color = validate_hex_color(hex_color)
        dupes = shade_comparator.find_dupes(hex_color, recommender.products, max_delta_e=8.0)
        return sanitize({"success": True, "dupes": dupes})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error finding dupes: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Something went wrong while finding dupes. Please try again."}
        )


# ─── Product Catalog Endpoint ────────────────────────────────────
@app.get("/api/products")
async def get_products():
    """Return the full product catalog grouped by type."""
    try:
        grouped = {}
        for p in recommender.products:
            ptype = p.get("type", "foundation")
            if ptype not in grouped:
                grouped[ptype] = []
            grouped[ptype].append(p)
        return sanitize(grouped)
    except Exception as e:
        print(f"Error fetching products: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Something went wrong while fetching products. Please try again."}
        )


# ─── Color Palette Endpoint ──────────────────────────────────────
@app.post("/api/color-palette")
async def color_palette(
    hex_color: str = Form(..., description="Skin hex color"),
    undertone: str = Form(..., description="Undertone: warm, cool, neutral, neutral-warm, neutral-cool"),
):
    """Return color harmony data (clothing, jewelry, lip colors) without uploading an image."""
    try:
        hex_color = validate_hex_color(hex_color)
        harmony = skin_analyzer._compute_color_harmony(undertone)
        return sanitize({"success": True, "hex_color": hex_color, "undertone": undertone, "color_harmony": harmony})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error generating color palette: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Something went wrong while generating your color palette. Please try again."}
        )


# ─── Run with Uvicorn ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
