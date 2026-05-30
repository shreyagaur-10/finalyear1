import numpy as np

from modules.skin_analysis import SkinAnalyzer


def test_skin_analyzer_returns_ita_and_harmony_fields():
    analyzer = SkinAnalyzer()
    pixels = np.tile(np.array([[115, 160, 205]], dtype=np.float32), (80, 1))

    result = analyzer.analyze(pixels.tolist())

    assert "error" not in result
    assert result["hex_color"].startswith("#")
    assert result["ita_category"] in {"Very Light", "Light", "Intermediate", "Tan", "Brown", "Dark"}
    assert result["sample_quality"]["score"] >= 0
    assert "color_harmony" in result
    assert result["undertone"] in {"warm", "cool", "neutral", "neutral-warm", "neutral-cool"}
