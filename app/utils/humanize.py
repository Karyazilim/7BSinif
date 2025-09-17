from datetime import datetime, timedelta


def humanize_time(dt: datetime) -> str:
    """Convert datetime to Turkish human-readable format"""
    now = datetime.now()
    diff = now - dt
    
    if diff.total_seconds() < 60:
        return "Az önce"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() // 60)
        return f"{minutes} dakika önce"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f"{hours} saat önce"
    elif diff.days < 7:
        return f"{diff.days} gün önce"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks} hafta önce"
    elif diff.days < 365:
        months = diff.days // 30
        return f"{months} ay önce"
    else:
        years = diff.days // 365
        return f"{years} yıl önce"