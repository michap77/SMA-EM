import time
import datetime

from libs.Sun import Sun

sun = Sun()

lat =49.47318753476173
long=7.788081334039965

coords = {
    'latitude' : lat,
    'longitude' : long
        }

isDark = sun.isDark(coords)

print(f"isDark: {isDark}")