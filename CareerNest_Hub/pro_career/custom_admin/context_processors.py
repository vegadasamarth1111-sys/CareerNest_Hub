from datetime import datetime


def admin_panel_context(request):
    return {
        "today_date": datetime.now().strftime("%d %b %Y"),
    }
