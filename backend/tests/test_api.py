from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "X-Process-Time-ms" in response.headers


def test_color_palette_rejects_invalid_hex():
    response = client.post(
        "/api/color-palette",
        data={"hex_color": "not-a-color", "undertone": "warm"},
    )

    assert response.status_code == 400
    assert "hex color" in response.json()["detail"]


def test_feedback_endpoint_records_learning_signal():
    response = client.post(
        "/api/feedback",
        json={
            "skin_hex": "#C8A07A",
            "predicted_shade": "Warm Honey",
            "selected_product_id": "test-product",
            "rating": 4,
            "actual_match": "good_match",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["feedback_id"]
