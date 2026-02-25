from django.urls import path
from .views import video_source_analysis_view, quality_selection_redirect_view

urlpatterns = [
    path("", video_source_analysis_view, name="video-analyzer"),
    path("select-quality/", quality_selection_redirect_view, name="quality-selection"),
]