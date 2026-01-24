import os
from django.http import FileResponse, Http404
from django.conf import settings

def serve_media(request, path):
    """
    Serve media files even when DEBUG=False (for local development only)
    In production, use a proper web server like Nginx
    """
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    if not os.path.exists(file_path):
        raise Http404("Media file not found")
    
    return FileResponse(open(file_path, 'rb'))
