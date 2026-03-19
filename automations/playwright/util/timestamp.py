from datetime import datetime

def get_timestamp(prefix: str = "IE") -> str:
    """
    Returns a formatted timestamp string like:
    'IE, 11/11/2025, 11:15 AM'
    """
    now = datetime.now()
    formatted_time = now.strftime("%m/%d/%Y, %I:%M %p")
    return f"{prefix}, {formatted_time}"