from .models import RecentPlay

def now_playing(request):
    """Context processor for currently playing song"""
    if request.user.is_authenticated:
        recent = RecentPlay.objects.filter(user=request.user).first()
        return {
            'now_playing': recent.song if recent else None
        }
    return {}