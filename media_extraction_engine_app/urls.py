# media_extraction_engine_app/urls.py

from .views import (
    video_source_analysis_view,
    quality_selection_redirect_view,
    download_selected_video_view
)
from django.urls import path

urlpatterns = [
    path("", video_source_analysis_view, name="video-analyzer"),
    path("select-quality/", quality_selection_redirect_view, name="quality-selection"),
    path("download/<str:format_id>/", download_selected_video_view, name="download-video"),
]