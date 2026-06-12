"""
Test suite for Timelapse API endpoints.
Covers the video streaming/download endpoint.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from src.utils.dependencies import get_timelapse_service


@pytest.fixture
def client(test_app):
    """Test client fixture using test_app from conftest."""
    return TestClient(test_app)


class TestTimelapseVideoAPI:
    """Test GET /api/v1/timelapses/{timelapse_id}/video"""

    def test_get_video_success(self, client, test_app, tmp_path):
        """Streams the rendered video file inline."""
        video_file = tmp_path / "print_job.mp4"
        video_file.write_bytes(b"fake mp4 content")

        mock_service = Mock()
        mock_service.get_timelapse = AsyncMock(return_value={
            "id": "tl_001",
            "output_video_path": str(video_file)
        })
        test_app.dependency_overrides[get_timelapse_service] = lambda: mock_service

        response = client.get("/api/v1/timelapses/tl_001/video")

        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
        assert "inline" in response.headers["content-disposition"]
        assert response.content == b"fake mp4 content"

    def test_get_video_download_disposition(self, client, test_app, tmp_path):
        """download=true forces an attachment Content-Disposition."""
        video_file = tmp_path / "print_job.mp4"
        video_file.write_bytes(b"fake mp4 content")

        mock_service = Mock()
        mock_service.get_timelapse = AsyncMock(return_value={
            "id": "tl_001",
            "output_video_path": str(video_file)
        })
        test_app.dependency_overrides[get_timelapse_service] = lambda: mock_service

        response = client.get("/api/v1/timelapses/tl_001/video?download=true")

        assert response.status_code == 200
        assert "attachment" in response.headers["content-disposition"]

    def test_get_video_timelapse_not_found(self, client, test_app):
        """Unknown timelapse IDs return 404."""
        mock_service = Mock()
        mock_service.get_timelapse = AsyncMock(return_value=None)
        test_app.dependency_overrides[get_timelapse_service] = lambda: mock_service

        response = client.get("/api/v1/timelapses/unknown/video")

        assert response.status_code == 404

    def test_get_video_file_missing(self, client, test_app):
        """A record without a rendered video file returns 404."""
        mock_service = Mock()
        mock_service.get_timelapse = AsyncMock(return_value={
            "id": "tl_001",
            "output_video_path": "/nonexistent/video.mp4"
        })
        test_app.dependency_overrides[get_timelapse_service] = lambda: mock_service

        response = client.get("/api/v1/timelapses/tl_001/video")

        assert response.status_code == 404
