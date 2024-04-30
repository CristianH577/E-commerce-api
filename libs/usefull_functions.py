import random
from datetime import datetime, timedelta

def getRandomDate():
    date_start = datetime(2023, 1, 1)
    date_end = datetime(2024, 3, 31)
    date_random = date_start + timedelta(
        days=random.randint(0, (date_end - date_start).days),
        hours=random.randint(9, 20),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )

    return date_random