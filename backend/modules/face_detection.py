"""
Face Detection Module
Uses OpenCV's Haar Cascade (haarcascade_frontalface_alt2 + profileface)
to detect faces and extract skin regions (cheeks + forehead) for skin tone analysis.
"""

import cv2
import numpy as np


class FaceDetector:
    def __init__(self):
        """Initialize OpenCV Haar Cascade face detectors."""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
        )
        self.profile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_profileface.xml"
        )

    def detect_face(self, image: np.ndarray, multi_face: bool = False):
        """
        Detect face(s) in image and extract skin regions.

        Args:
            image: BGR image as numpy array
            multi_face: if True, return results for ALL detected faces

        Returns:
            When multi_face=False: dict with face_bbox, skin_regions, or error
            When multi_face=True: list of dicts (one per face), or dict with error
        """
        h, w, _ = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Primary detection with frontal face cascade
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
        )

        # Second-pass with profile face cascade for side profiles
        if len(faces) == 0:
            faces = self.profile_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(80, 80),
            )

        if len(faces) == 0:
            return {"error": "No face detected. Please upload a clear selfie with good lighting."}

        faces = list(faces)

        if multi_face:
            results = []
            for fx, fy, fw, fh in faces:
                face_bbox = {
                    "x": int(fx),
                    "y": int(fy),
                    "width": int(fw),
                    "height": int(fh),
                }
                skin_regions = self._extract_skin_regions(image, fx, fy, fw, fh)
                results.append({
                    "face_bbox": face_bbox,
                    "skin_regions": skin_regions,
                    "confidence": 0.85,
                })
            return results

        # Single-face mode: pick the largest face
        if len(faces) > 1:
            areas = [fw * fh for (_, _, fw, fh) in faces]
            faces = [faces[np.argmax(areas)]]

        fx, fy, fw, fh = faces[0]

        face_bbox = {
            "x": int(fx),
            "y": int(fy),
            "width": int(fw),
            "height": int(fh),
        }

        skin_regions = self._extract_skin_regions(image, fx, fy, fw, fh)

        return {
            "face_bbox": face_bbox,
            "skin_regions": skin_regions,
            "confidence": 0.85,
        }

    def _extract_skin_regions(self, image: np.ndarray, fx: int, fy: int, fw: int, fh: int) -> dict:
        """
        Extract skin pixel samples from cheek and forehead regions
        using geometric approximations within the detected face bbox.
        """
        h, w = image.shape[:2]
        radius = max(5, int(fw * 0.04))

        # Approximate landmark positions relative to face bbox
        sample_points = {
            "left_cheek": [
                (fx + int(fw * 0.25), fy + int(fh * 0.55)),
                (fx + int(fw * 0.20), fy + int(fh * 0.50)),
                (fx + int(fw * 0.30), fy + int(fh * 0.60)),
            ],
            "right_cheek": [
                (fx + int(fw * 0.75), fy + int(fh * 0.55)),
                (fx + int(fw * 0.80), fy + int(fh * 0.50)),
                (fx + int(fw * 0.70), fy + int(fh * 0.60)),
            ],
            "forehead": [
                (fx + int(fw * 0.50), fy + int(fh * 0.15)),
                (fx + int(fw * 0.40), fy + int(fh * 0.18)),
                (fx + int(fw * 0.60), fy + int(fh * 0.18)),
            ],
        }

        skin_pixels = []
        region_pixels = {}

        for region_name, points in sample_points.items():
            region_px = []
            for cx, cy in points:
                y_start = max(0, cy - radius)
                y_end = min(h, cy + radius)
                x_start = max(0, cx - radius)
                x_end = min(w, cx + radius)

                patch = image[y_start:y_end, x_start:x_end]
                if patch.size > 0:
                    pixels = patch.reshape(-1, 3)
                    region_px.extend(pixels.tolist())
                    skin_pixels.extend(pixels.tolist())

            region_pixels[region_name] = region_px

        return {
            "all_pixels": skin_pixels,
            "regions": region_pixels,
            "total_samples": len(skin_pixels),
        }
