"""
Complete Makeup Look Generator
Generates curated makeup looks based on skin analysis and user intent,
matching each step to available products when possible.
"""


# Look name templates based on occasion + look combinations
LOOK_NAMES = {
    ("everyday", "natural"): "Fresh-Faced Daily",
    ("everyday", "glam"): "Effortless Chic",
    ("everyday", "classic"): "Polished & Ready",
    ("everyday", "trendy"): "Soft Girl Everyday",
    ("college", "natural"): "Campus Ready Glow",
    ("college", "glam"): "Lecture Hall Glam",
    ("college", "classic"): "Study Session Chic",
    ("college", "trendy"): "K-Beauty Campus",
    ("party", "natural"): "Night Out Natural",
    ("party", "glam"): "Golden Hour Glow",
    ("party", "classic"): "Evening Elegance",
    ("party", "trendy"): "After Dark Aesthetic",
    ("wedding", "natural"): "Bridal Radiance",
    ("wedding", "glam"): "Boss Babe Matte",
    ("wedding", "classic"): "Timeless Bridal",
    ("wedding", "trendy"): "Modern Bride Glow",
    ("festival", "natural"): "Festive Freshness",
    ("festival", "glam"): "Diwali Dazzle",
    ("festival", "classic"): "Festive Elegance",
    ("festival", "trendy"): "Festival Fairy",
    ("interview", "natural"): "Confidence Boost",
    ("interview", "glam"): "Power Move",
    ("interview", "classic"): "Professional Polish",
    ("interview", "trendy"): "Modern Professional",
    ("photoshoot", "natural"): "Camera Ready Glow",
    ("photoshoot", "glam"): "Full Glam Shoot",
    ("photoshoot", "classic"): "Editorial Classic",
    ("photoshoot", "trendy"): "Viral Look",
}

LOOK_DESCRIPTIONS = {
    "natural": "A lightweight, skin-first look that enhances your natural beauty. Perfect for when you want to look put-together without looking 'done'.",
    "glam": "A full-coverage, statement look that's bold and camera-ready. Build up layers for a flawless, sculpted finish.",
    "classic": "An elegant, timeless look with balanced coverage and a polished finish. Sophisticated without being over the top.",
    "trendy": "A fresh, modern look inspired by the latest beauty trends. Think glass skin, soft focus, and effortless cool.",
}

STEP_TEMPLATES = {
    "natural": [
        {"category": "primer", "instruction": "Apply a thin layer of hydrating primer on clean, moisturized skin. Focus on the T-zone and cheeks.", "pro_tip": "Mix a drop of primer with your moisturizer for an even lighter base."},
        {"category": "foundation", "instruction": "Apply foundation only where needed — center of forehead, nose, chin, and under eyes. Blend outward with fingers or a damp sponge.", "pro_tip": "Use your ring finger to blend for a natural, skin-like finish."},
        {"category": "concealer", "instruction": "Dab concealer under eyes in an inverted triangle shape. Tap gently to blend.", "pro_tip": "Set concealer with a tiny bit of translucent powder to prevent creasing."},
        {"category": "blush", "instruction": "Smile and apply a soft blush on the apples of your cheeks. Blend upward toward the temples.", "pro_tip": "Cream blush gives a more natural, dewy finish than powder."},
        {"category": "lipstick", "instruction": "Apply a tinted lip balm or sheer lipstick. Blot with tissue for a natural stain.", "pro_tip": "Dab lipstick on with your finger for a lived-in, casual look."},
    ],
    "glam": [
        {"category": "primer", "instruction": "Apply a pore-filling primer all over, and a luminous primer on the high points of your face.", "pro_tip": "Layer two primers — mattifying on T-zone, glowy on cheekbones."},
        {"category": "foundation", "instruction": "Apply full-coverage foundation in thin layers. Use a beauty blender for an airbrushed finish. Build coverage gradually.", "pro_tip": "Set each layer with a light dusting of powder before adding the next."},
        {"category": "concealer", "instruction": "Apply concealer under eyes, on the bridge of your nose, and on any spots. Blend with a damp sponge.", "pro_tip": "Use a shade lighter than your foundation under the eyes for a brightening effect."},
        {"category": "blush", "instruction": "Apply a pigmented blush on the cheekbones, blending upward. Layer cream blush under powder blush for intensity.", "pro_tip": "Tap off excess product from your brush before applying to avoid patchiness."},
        {"category": "lipstick", "instruction": "Line lips with a matching liner, then fill in with a bold lipstick. Blot and reapply for a long-lasting finish.", "pro_tip": "Apply concealer around the lip line for a crisp, defined edge."},
    ],
    "classic": [
        {"category": "primer", "instruction": "Apply a smoothing primer evenly across the face. Let it set for 1 minute before moving on.", "pro_tip": "Press primer into skin rather than rubbing for better adhesion."},
        {"category": "foundation", "instruction": "Apply medium-coverage foundation with a brush, starting from the center and blending outward. Focus on evening out skin tone.", "pro_tip": "Use downward strokes to lay down the foundation for a smoother finish."},
        {"category": "concealer", "instruction": "Apply concealer on under-eye area and any blemishes. Blend with a sponge for seamless coverage.", "pro_tip": "Warm the concealer between your fingers before applying for easier blending."},
        {"category": "blush", "instruction": "Apply blush on the apples of the cheeks and blend toward the hairline for a classic flush.", "pro_tip": "Choose a shade that matches the color your cheeks naturally flush."},
        {"category": "lipstick", "instruction": "Apply a classic lipstick shade that complements your skin tone. Use a lip brush for precision.", "pro_tip": "Apply lipstick, blot, then reapply for a stain that lasts all day."},
    ],
    "trendy": [
        {"category": "primer", "instruction": "Apply a dewy, hydrating primer all over. Look for one with light-reflecting particles for that glass-skin base.", "pro_tip": "Skip primer on oily areas and use a water-based gel instead."},
        {"category": "foundation", "instruction": "Mix foundation with a drop of facial oil or strobe cream. Apply with a damp sponge using pressing motions for a skin-like finish.", "pro_tip": "Apply foundation to the center of the face only and let your natural skin show at the edges."},
        {"category": "concealer", "instruction": "Use a luminous concealer only where needed. Skip heavy coverage — embrace your skin texture.", "pro_tip": "Try the 'dot and blend' technique — place small dots and tap in with your ring finger."},
        {"category": "blush", "instruction": "Apply cream or liquid blush on cheekbones and dab a tiny bit on the nose and forehead for a sun-kissed effect.", "pro_tip": "Apply blush before powder products for a more natural, from-within glow."},
        {"category": "lipstick", "instruction": "Apply a gradient lip — dab color on the center of your lips and blend outward with your finger.", "pro_tip": "Use a lip tint for that effortless, just-bitten look that's trending everywhere."},
    ],
}

COMPLEXITY = {
    "natural": {"estimated_time": "5 mins", "difficulty": "beginner"},
    "glam": {"estimated_time": "15 mins", "difficulty": "pro"},
    "classic": {"estimated_time": "10 mins", "difficulty": "intermediate"},
    "trendy": {"estimated_time": "10 mins", "difficulty": "intermediate"},
}


class LookGenerator:
    def generate_look(self, skin_data: dict, intent: dict, products: list) -> dict:
        """
        Generate a complete curated makeup look.

        Args:
            skin_data: Output from SkinAnalyzer.analyze()
            intent: Output from IntentParser.parse()
            products: List of available products from the database

        Returns:
            dict with look_name, look_description, steps, estimated_time, difficulty
        """
        occasion = intent.get("occasion", "everyday")
        look = intent.get("look", "natural")

        look_name = LOOK_NAMES.get((occasion, look), "Custom Beauty Look")
        look_description = LOOK_DESCRIPTIONS.get(look, LOOK_DESCRIPTIONS["natural"])
        step_templates = STEP_TEMPLATES.get(look, STEP_TEMPLATES["natural"])
        complexity = COMPLEXITY.get(look, COMPLEXITY["natural"])

        steps = []
        for i, tmpl in enumerate(step_templates, start=1):
            matched_product = self._match_product(tmpl["category"], products)
            steps.append({
                "step_number": i,
                "category": tmpl["category"],
                "instruction": tmpl["instruction"],
                "product": matched_product,
                "pro_tip": tmpl["pro_tip"],
            })

        return {
            "look_name": look_name,
            "look_description": look_description,
            "steps": steps,
            "estimated_time": complexity["estimated_time"],
            "difficulty": complexity["difficulty"],
        }

    def _match_product(self, category: str, products: list):
        """Find the best matching product for a given category."""
        for p in products:
            if p.get("type", "foundation") == category:
                return {
                    "id": p["id"],
                    "brand": p["brand"],
                    "line": p["line"],
                    "shade_name": p["shade_name"],
                    "hex_color": p["hex_color"],
                    "price": p["price"],
                }
        return None
