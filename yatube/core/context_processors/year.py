from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    date_now = datetime.today()
    return {
        'year': date_now.year
    }
