import os
import threading
from django.conf import settings
from django.core.management import call_command

_has_seeded = False
_seed_lock = threading.Lock()

class AutoSeedDataMiddleware:
    """
    Automatically populates the database with initial jobs, internships,
    courses, and user profiles if the database is empty.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _has_seeded
        if not _has_seeded:
            with _seed_lock:
                if not _has_seeded:
                    try:
                        from jobs.models import Job
                        if Job.objects.count() == 0:
                            datadump_path = os.path.join(settings.BASE_DIR, 'datadump.json')
                            if os.path.exists(datadump_path):
                                call_command('loaddata', datadump_path)
                                print("Successfully auto-seeded initial data from datadump.json")
                        _has_seeded = True
                    except Exception as e:
                        print("Auto-seed notice:", e)
                        _has_seeded = True
        return self.get_response(request)
