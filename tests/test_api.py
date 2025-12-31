"""
Tests for Guitar Platform API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthAndInfo:
    """Test basic health and info endpoints"""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Guitar Platform API"
        assert "version" in data
        assert "endpoints" in data

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestScalesAndPatterns:
    """Test scale, pattern, and tuning list endpoints"""

    def test_list_scales(self):
        response = client.get("/scales")
        assert response.status_code == 200
        data = response.json()
        assert "scales" in data
        assert isinstance(data["scales"], list)
        assert "phrygian" in data["scales"]
        assert "major" in data["scales"]
        assert "minor" in data["scales"]

    def test_list_patterns(self):
        response = client.get("/patterns")
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert isinstance(data["patterns"], list)
        assert "ascending" in data["patterns"]
        assert "pedal" in data["patterns"]

    def test_list_tunings(self):
        response = client.get("/tunings")
        assert response.status_code == 200
        data = response.json()
        assert "tunings" in data
        assert isinstance(data["tunings"], list)
        assert "standard" in data["tunings"]

    def test_list_progressions(self):
        response = client.get("/progressions")
        assert response.status_code == 200
        data = response.json()
        assert "progressions" in data
        assert isinstance(data["progressions"], list)


class TestTabGeneration:
    """Test tab generation endpoints"""

    def test_generate_tab_default(self):
        response = client.post("/generate-tab", json={})
        assert response.status_code == 200
        data = response.json()
        assert "tab" in data
        assert "root" in data
        assert "scale" in data
        assert data["root"] == "E"
        assert data["scale"] == "phrygian"

    def test_generate_tab_custom_params(self):
        response = client.post("/generate-tab", json={
            "root": "A",
            "scale": "minor",
            "pattern": "descending",
            "bars": 2,
            "tempo": 140
        })
        assert response.status_code == 200
        data = response.json()
        assert data["root"] == "A"
        assert data["scale"] == "minor"
        assert data["pattern"] == "descending"
        assert data["bars"] == 2
        assert data["tempo"] == 140

    def test_generate_tab_contains_tab_lines(self):
        response = client.post("/generate-tab", json={
            "root": "E",
            "scale": "phrygian",
            "pattern": "ascending"
        })
        assert response.status_code == 200
        data = response.json()
        tab = data["tab"]
        # Tab should contain string labels (e, B, G, D, A, E)
        assert "e|" in tab or "E|" in tab
        # Tab should contain numbers (fret positions)
        assert any(c.isdigit() for c in tab)


class TestGP5Generation:
    """Test GP5 file generation"""

    def test_generate_gp5_returns_file(self):
        response = client.post("/generate-gp5", json={
            "root": "E",
            "scale": "phrygian",
            "pattern": "ascending",
            "bars": 2
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "content-disposition" in response.headers
        assert ".gp5" in response.headers["content-disposition"]
        # Check file has content
        assert len(response.content) > 0


class TestBackingTrack:
    """Test backing track related endpoints"""

    def test_list_rhythm_patterns(self):
        response = client.get("/rhythm-patterns")
        assert response.status_code == 200
        data = response.json()
        assert "rhythm_patterns" in data
        assert isinstance(data["rhythm_patterns"], list)

    def test_list_accent_patterns(self):
        response = client.get("/accent-patterns")
        assert response.status_code == 200
        data = response.json()
        assert "accent_patterns" in data
        assert isinstance(data["accent_patterns"], list)

    def test_list_styles(self):
        response = client.get("/styles")
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data
        assert isinstance(data["styles"], list)
