"""
Recommendation Engine
Matches detected skin tone + undertone + user preferences to
the best foundation products from our curated database.
"""

import json
import os
from typing import List, Optional

from modules.shade_comparison import ShadeComparator, delta_e_ciede2000


class Recommender:
    def __init__(self):
        """Load product database from JSON file."""
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "products.json")
        with open(data_path, "r", encoding="utf-8") as f:
            self.products = json.load(f)
        self.shade_comparator = ShadeComparator()
        self.feedback_path = os.path.join(os.path.dirname(__file__), "..", "data", "feedback.jsonl")
        self.feedback_stats = self._load_feedback_stats()

    def _load_feedback_stats(self):
        """Aggregate user feedback into lightweight ranking priors."""
        stats = {}
        if not os.path.exists(self.feedback_path):
            return stats

        with open(self.feedback_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                product_id = event.get("selected_product_id")
                if not product_id:
                    continue
                product_stats = stats.setdefault(product_id, {
                    "count": 0,
                    "rating_sum": 0.0,
                    "good_matches": 0,
                    "issues": {},
                })
                product_stats["count"] += 1
                product_stats["rating_sum"] += float(event.get("rating") or 0)
                actual_match = event.get("actual_match")
                if actual_match == "good_match":
                    product_stats["good_matches"] += 1
                elif actual_match:
                    product_stats["issues"][actual_match] = product_stats["issues"].get(actual_match, 0) + 1

        for product_stats in stats.values():
            count = max(product_stats["count"], 1)
            product_stats["avg_rating"] = product_stats["rating_sum"] / count
            product_stats["good_match_rate"] = product_stats["good_matches"] / count
        return stats

    def reload_feedback(self):
        """Refresh feedback priors without restarting the process."""
        self.feedback_stats = self._load_feedback_stats()

    def recommend(self, skin_data: dict, intent: dict, top_n: int = 5,
                  product_type: str = "foundation") -> List[dict]:
        """
        Find the best matching products.

        Args:
            skin_data: Output from SkinAnalyzer.analyze()
                       Contains: hex_color, luminance, undertone, shade_name
            intent: Output from IntentParser.parse()
                    Contains: occasion, look, coverage, finish
            product_type: Filter by product type (default "foundation")

        Returns:
            List of top N product matches with scores
        """
        undertone = skin_data.get("undertone", "neutral")
        skin_hex = skin_data.get("hex_color")
        analysis_confidence = float(skin_data.get("confidence", 0.75))

        scored_products = []

        filtered_products = self.products if product_type == "all" else [
            p for p in self.products
            if p.get("type", "foundation") == product_type
        ]

        for product in filtered_products:
            score_data = self._score_product(product, skin_data, undertone, intent)
            score = score_data["score"]
            if score > 0:
                scored_products.append({
                    **product,
                    "match_score": round(score * analysis_confidence, 1),
                    "score_breakdown": score_data["breakdown"],
                    "recommendation_explanation": score_data["explanation"],
                })

        # Sort by match score (highest first)
        scored_products.sort(key=lambda x: x["match_score"], reverse=True)

        if product_type == "all":
            grouped_results = []
            counts_by_type = {}
            for product in scored_products:
                ptype = product.get("type", "foundation")
                if counts_by_type.get(ptype, 0) >= top_n:
                    continue
                grouped_results.append(product)
                counts_by_type[ptype] = counts_by_type.get(ptype, 0) + 1
            results = grouped_results
        else:
            results = scored_products[:top_n]

        # Add match percentage (normalize to 0-100) and ensure type is present
        if results:
            max_score = results[0]["match_score"]
            for product in results:
                product["match_percentage"] = round(
                    (product["match_score"] / max_score) * 100
                ) if max_score > 0 else 0
                if "type" not in product:
                    product["type"] = product_type
                if skin_hex and product.get("hex_color"):
                    delta_e = delta_e_ciede2000(skin_hex, product["hex_color"])
                    product["delta_e"] = round(delta_e, 2)
                    product["delta_e_method"] = "CIEDE2000"
                    product["match_quality"] = self.shade_comparator._get_match_quality(delta_e)

        return results

    def _score_product(self, product: dict, skin_data: dict,
                       undertone: str, intent: dict) -> dict:
        """
        Score a product based on how well it matches.

        Scoring weights:
        - Shade match (luminance): 50 points max (most important)
        - Undertone match: 25 points max
        - Finish preference: 15 points max
        - Coverage preference: 10 points max
        """
        score = 0.0
        breakdown = {}
        explanation = []
        luminance = skin_data.get("luminance", 150)
        skin_hex = skin_data.get("hex_color")

        # 1. SHADE MATCH (50 points) using Delta-E when catalog color is present.
        if skin_hex and product.get("hex_color"):
            delta_e = delta_e_ciede2000(skin_hex, product["hex_color"])
            shade_score = max(0, 50 - min(delta_e, 24) * 1.85)
            if delta_e > 22:
                return {"score": 0, "breakdown": {}, "explanation": []}
            breakdown["shade"] = round(shade_score, 1)
            explanation.append(f"CIEDE2000 {delta_e:.1f} color distance")
            score += shade_score
        else:
            lum_min, lum_max = product.get("luminance_range", [0, 255])
            lum_center = (lum_min + lum_max) / 2
            lum_range = max((lum_max - lum_min) / 2, 1)
            if lum_min <= luminance <= lum_max:
                distance = abs(luminance - lum_center)
                shade_score = 50 - (distance / lum_range * 15)
            else:
                distance = lum_min - luminance if luminance < lum_min else luminance - lum_max
                if distance > 15:
                    return {"score": 0, "breakdown": {}, "explanation": []}
                shade_score = max(0, 35 - distance * 2)
            breakdown["shade"] = round(shade_score, 1)
            explanation.append("luminance range match")
            score += shade_score

        # 2. UNDERTONE MATCH (25 points)
        product_undertones = product.get("undertone", [])
        if undertone in product_undertones:
            undertone_score = 25
            explanation.append("undertone match")
        elif any(undertone.split("-")[0] in ut for ut in product_undertones):
            # Partial match (e.g., "neutral-warm" partially matches "warm")
            undertone_score = 15
            explanation.append("partial undertone match")
        elif "neutral" in product_undertones:
            # Neutral products work for everyone
            undertone_score = 10
            explanation.append("neutral shade flexibility")
        else:
            undertone_score = 0
        breakdown["undertone"] = undertone_score
        score += undertone_score

        # 3. FINISH PREFERENCE (15 points)
        preferred_finish = intent.get("finish", "satin")
        product_finish = product.get("finish", "satin")

        if product_finish == preferred_finish:
            finish_score = 15
            explanation.append("finish preference match")
        elif preferred_finish == "satin":
            # Satin is a middle ground — partially matches everything
            finish_score = 8
        else:
            finish_score = 3
        breakdown["finish"] = finish_score
        score += finish_score

        # 4. COVERAGE PREFERENCE (10 points)
        preferred_coverage = intent.get("coverage", "medium")
        product_coverage = product.get("coverage", "medium")

        coverage_map = {"light": 1, "medium": 2, "full": 3}
        pref_level = coverage_map.get(preferred_coverage, 2)
        prod_level = coverage_map.get(product_coverage, 2)

        coverage_diff = abs(pref_level - prod_level)
        if coverage_diff == 0:
            coverage_score = 10
            explanation.append("coverage preference match")
        elif coverage_diff == 1:
            coverage_score = 5
        else:
            coverage_score = 1
        breakdown["coverage"] = coverage_score
        score += coverage_score

        # Budget boost — affordable products get a small bonus for college students
        price_str = product.get("price", "₹500")
        try:
            price = int(price_str.replace("₹", "").replace(",", ""))
            if price <= 350:
                breakdown["budget"] = 3
                explanation.append("budget-friendly option")
                score += 3
        except (ValueError, AttributeError):
            pass

        feedback_score, feedback_explanation = self._score_feedback_prior(product)
        if feedback_score:
            breakdown["feedback"] = round(feedback_score, 1)
            explanation.append(feedback_explanation)
            score += feedback_score

        return {
            "score": score,
            "breakdown": breakdown,
            "explanation": explanation[:4],
        }

    def _score_feedback_prior(self, product: dict) -> tuple:
        """Use real-world feedback as a small ranking prior."""
        product_id = product.get("id")
        stats = self.feedback_stats.get(product_id)
        if not stats or stats.get("count", 0) < 2:
            return 0.0, ""

        avg_rating = stats.get("avg_rating", 3.0)
        good_rate = stats.get("good_match_rate", 0.0)
        issue_count = sum(stats.get("issues", {}).values())
        count = stats.get("count", 1)

        score = 0.0
        score += max(-4.0, min(4.0, (avg_rating - 3.0) * 1.5))
        score += max(0.0, min(3.0, good_rate * 3.0))
        score -= min(4.0, issue_count / count * 4.0)

        if score > 0:
            return score, f"user feedback prior +{score:.1f}"
        if score < 0:
            return score, f"user feedback prior {score:.1f}"
        return 0.0, ""

    def get_shade_matches(self, luminance: float) -> List[dict]:
        """
        Get all products that match a given luminance, regardless of other preferences.
        Useful for showing "All shades in your range" section.
        """
        matches = []
        for product in self.products:
            lum_min, lum_max = product.get("luminance_range", [0, 255])
            if lum_min - 10 <= luminance <= lum_max + 10:
                matches.append(product)
        return matches
