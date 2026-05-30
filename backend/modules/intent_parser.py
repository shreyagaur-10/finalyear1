"""
Intent Parser Module
Parses user text input to extract makeup preferences like
occasion, look style, coverage level, and finish type.
"""


# Keyword dictionaries for classification
OCCASION_KEYWORDS = {
    "college": ["college", "class", "school", "university", "campus", "everyday", "daily", "casual", "office", "work"],
    "party": ["party", "night out", "club", "dinner", "date", "evening", "night"],
    "wedding": ["wedding", "shaadi", "reception", "sangeet", "mehendi", "bridal", "bride", "dulhan"],
    "festival": ["festival", "diwali", "holi", "eid", "puja", "navratri", "celebration", "festive"],
    "interview": ["interview", "meeting", "professional", "formal", "corporate"],
    "photoshoot": ["photo", "photoshoot", "shoot", "selfie", "picture", "instagram", "social media"],
}

LOOK_KEYWORDS = {
    "natural": ["natural", "minimal", "simple", "subtle", "no makeup", "bare", "light", "fresh", "clean", "dewy"],
    "glam": ["glam", "glamorous", "bold", "dramatic", "heavy", "full glam", "instagram", "influencer"],
    "classic": ["classic", "elegant", "timeless", "sophisticated", "polished"],
    "trendy": ["trendy", "korean", "k-beauty", "glass skin", "douyin", "viral", "aesthetic"],
}

COVERAGE_KEYWORDS = {
    "light": ["light", "sheer", "tinted", "minimal", "natural", "bare", "bb cream"],
    "medium": ["medium", "moderate", "buildable", "everyday", "regular"],
    "full": ["full", "heavy", "maximum", "complete", "cover", "high coverage", "full coverage", "opaque"],
}

FINISH_KEYWORDS = {
    "matte": ["matte", "flat", "oil free", "oil control", "shine free", "powder"],
    "dewy": ["dewy", "glow", "glass", "glowing", "radiant", "luminous", "hydrating", "moisturizing"],
    "satin": ["satin", "semi matte", "semi-matte", "natural finish", "balanced"],
}


class IntentParser:
    def __init__(self):
        pass

    def parse(self, text: str) -> dict:
        """
        Parse user text input to extract makeup preferences.

        Args:
            text: User's text input (e.g., "natural look for college")

        Returns:
            dict with occasion, look, coverage, finish, and raw_text
        """
        if not text or not text.strip():
            # Default preferences when no text provided
            return {
                "occasion": "everyday",
                "look": "natural",
                "coverage": "medium",
                "finish": "satin",
                "raw_text": "",
                "preferences_detected": False
            }

        text_lower = text.lower().strip()

        occasion = self._match_keywords(text_lower, OCCASION_KEYWORDS, default="everyday")
        look = self._match_keywords(text_lower, LOOK_KEYWORDS, default="natural")
        coverage = self._match_keywords(text_lower, COVERAGE_KEYWORDS, default="medium")
        finish = self._match_keywords(text_lower, FINISH_KEYWORDS, default="satin")

        return {
            "occasion": occasion,
            "look": look,
            "coverage": coverage,
            "finish": finish,
            "raw_text": text.strip(),
            "preferences_detected": True
        }

    def _match_keywords(self, text: str, keyword_dict: dict, default: str) -> str:
        """
        Find the best matching category by counting keyword matches.
        Returns the category with the most keyword hits.
        """
        best_match = default
        best_count = 0

        for category, keywords in keyword_dict.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > best_count:
                best_count = count
                best_match = category

        return best_match

    def get_style_tips(self, intent: dict) -> list:
        """
        Generate personalized style tips based on parsed intent.
        """
        tips = []

        occasion_tips = {
            "college": "For college, a lightweight foundation or BB cream keeps you looking fresh all day without feeling heavy.",
            "party": "For parties, layer your foundation with a primer for long-lasting coverage that photographs beautifully.",
            "wedding": "For weddings, use a full-coverage foundation with setting spray to look flawless from ceremony to reception.",
            "festival": "For festive occasions, pair your foundation with a luminous primer for that special glow.",
            "interview": "For interviews, go with a medium-coverage foundation that looks professional and polished.",
            "photoshoot": "For photos, use a foundation that doesn't flashback — matte or satin finishes photograph best.",
        }

        look_tips = {
            "natural": "For a natural look, apply foundation only where needed (center of face) and blend outward for a skin-like finish.",
            "glam": "For a glam look, build coverage in thin layers and set with translucent powder for a flawless canvas.",
            "classic": "A classic look starts with a well-matched foundation — blend along the jawline for a seamless finish.",
            "trendy": "For a trendy glass-skin look, mix a drop of facial oil with your foundation for that lit-from-within glow.",
        }

        if intent["occasion"] in occasion_tips:
            tips.append(occasion_tips[intent["occasion"]])
        if intent["look"] in look_tips:
            tips.append(look_tips[intent["look"]])

        if not tips:
            tips.append("Start with a clean, moisturized face. Apply primer, then foundation from the center outward.")

        return tips
