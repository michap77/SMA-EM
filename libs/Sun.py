""" 
Berechnung Sonnenauf- und -untergang

Implementierung adaptiert von

https://stackoverflow.com/a/39867990

Basierend auf https://web.archive.org/web/20161202180207/http://williams.best.vwh.net/sunrise_sunset_algorithm.htm

Sunrise/Sunset Algorithm

Source:
	Almanac for Computers, 1990
	published by Nautical Almanac Office
	United States Naval Observatory
	Washington, DC 20392

Inputs:
	day, month, year:      date of sunrise/sunset
	latitude, longitude:   location for sunrise/sunset
	zenith:                Sun's zenith for sunrise/sunset
	  offical      = 90 degrees 50'
	  civil        = 96 degrees
	  nautical     = 102 degrees
	  astronomical = 108 degrees
	
	NOTE: longitude is positive for East and negative for West
        NOTE: the algorithm assumes the use of a calculator with the
        trig functions in "degree" (rather than "radian") mode. Most
        programming languages assume radian arguments, requiring back
        and forth convertions. The factor is 180/pi. So, for instance,
        the equation RA = atan(0.91764 * tan(L)) would be coded as RA
        = (180/pi)*atan(0.91764 * tan((pi/180)*L)) to give a degree
        answer with a degree input for L.


1. first calculate the day of the year

	N1 = floor(275 * month / 9)
	N2 = floor((month + 9) / 12)
	N3 = (1 + floor((year - 4 * floor(year / 4) + 2) / 3))
	N = N1 - (N2 * N3) + day - 30

2. convert the longitude to hour value and calculate an approximate time

	lngHour = longitude / 15
	
	if rising time is desired:
	  t = N + ((6 - lngHour) / 24)
	if setting time is desired:
	  t = N + ((18 - lngHour) / 24)

3. calculate the Sun's mean anomaly
	
	M = (0.9856 * t) - 3.289

4. calculate the Sun's true longitude
	
	L = M + (1.916 * sin(M)) + (0.020 * sin(2 * M)) + 282.634
	NOTE: L potentially needs to be adjusted into the range [0,360) by adding/subtracting 360

5a. calculate the Sun's right ascension
	
	RA = atan(0.91764 * tan(L))
	NOTE: RA potentially needs to be adjusted into the range [0,360) by adding/subtracting 360

5b. right ascension value needs to be in the same quadrant as L

	Lquadrant  = (floor( L/90)) * 90
	RAquadrant = (floor(RA/90)) * 90
	RA = RA + (Lquadrant - RAquadrant)

5c. right ascension value needs to be converted into hours

	RA = RA / 15

6. calculate the Sun's declination

	sinDec = 0.39782 * sin(L)
	cosDec = cos(asin(sinDec))

7a. calculate the Sun's local hour angle
	
	cosH = (cos(zenith) - (sinDec * sin(latitude))) / (cosDec * cos(latitude))
	
	if (cosH >  1) 
	  the sun never rises on this location (on the specified date)
	if (cosH < -1)
	  the sun never sets on this location (on the specified date)

7b. finish calculating H and convert into hours
	
	if if rising time is desired:
	  H = 360 - acos(cosH)
	if setting time is desired:
	  H = acos(cosH)
	
	H = H / 15

8. calculate local mean time of rising/setting
	
	T = H + RA - (0.06571 * t) - 6.622

9. adjust back to UTC
	
	UT = T - lngHour
	NOTE: UT potentially needs to be adjusted into the range [0,24) by adding/subtracting 24

10. convert UT value to local time zone of latitude/longitude
	
	localT = UT + localOffset
"""

import math
import datetime
from zoneinfo import ZoneInfo

class Sun:

    def getSunriseTime( self, coords):
        return self.calcSunTime( coords, True )

    def getSunsetTime( self, coords):
        return self.calcSunTime( coords, False )

    def isDark( self, coords, time = None):

        if time == None:
            time = datetime.datetime.now(datetime.UTC)
            
        sunrise = self.getSunriseTime(coords)
        sunset = self.getSunsetTime(coords)

        print(f"is it dark at {time.isoformat()}")
        print(f"location (lat {coords['latitude']}, long: {coords['longitude']})")
        print(f"sunrise: {sunrise.isoformat()}")
        print(f"sunset: {sunset.isoformat()}")

        return time < sunrise or time > sunset

    def getCurrentUTC( self ):
        now = datetime.datetime.now()
        return [ now.day, now.month, now.year ]
    
    def calcSunTime( self, coords, isRiseTime, zenith = 90.8 ):
    
        # isRiseTime == False, returns sunsetTime
    
        day, month, year = self.getCurrentUTC()
    
        longitude = coords['longitude']
        latitude = coords['latitude']

        TO_RAD = math.pi/180
    
        #1. first calculate the day of the year
        N1 = math.floor(275 * month / 9)
        N2 = math.floor((month + 9) / 12)
        N3 = (1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3))
        N = N1 - (N2 * N3) + day - 30

        #2. convert the longitude to hour value and calculate an approximate time
        lngHour = longitude / 15
        
        if isRiseTime:
            t = N + ((6 - lngHour) / 24)
        else: #sunset
            t = N + ((18 - lngHour) / 24)
    
        #3. calculate the Sun's mean anomaly
        M = (0.9856 * t) - 3.289
    
        #4. calculate the Sun's true longitude
        L = M + (1.916 * math.sin(TO_RAD*M)) + (0.020 * math.sin(TO_RAD * 2 * M)) + 282.634
        L = self.forceRange( L, 360 ) #NOTE: L adjusted into the range [0,360)
    
        #5a. calculate the Sun's right ascension
    
        RA = (1/TO_RAD) * math.atan(0.91764 * math.tan(TO_RAD*L))
        RA = self.forceRange( RA, 360 ) #NOTE: RA adjusted into the range [0,360)
    
        #5b. right ascension value needs to be in the same quadrant as L
        Lquadrant  = (math.floor( L/90)) * 90
        RAquadrant = (math.floor(RA/90)) * 90
        RA = RA + (Lquadrant - RAquadrant)
    
        #5c. right ascension value needs to be converted into hours
        RA = RA / 15
    
        #6. calculate the Sun's declination
        sinDec = 0.39782 * math.sin(TO_RAD*L)
        cosDec = math.cos(math.asin(sinDec))
    
        #7a. calculate the Sun's local hour angle
        cosH = (math.cos(TO_RAD*zenith) - (sinDec * math.sin(TO_RAD*latitude))) / (cosDec * math.cos(TO_RAD*latitude))
    
        if cosH > 1:
            # the sun never rises on this location (on the specified date)
            return datetime.datetime(year,month,day,0,0,0,0,tz)
    
        if cosH < -1:
            # the sun never sets on this location (on the specified date)
            return datetime.datetime(year,month,day,23,59,0,0,tz)
    
        #7b. finish calculating H and convert into hours
        
        if isRiseTime:
            H = 360 - (1/TO_RAD) * math.acos(cosH)
        else: #setting
            H = (1/TO_RAD) * math.acos(cosH)
        
        H = H / 15
    
        #8. calculate local mean time of rising/setting
        T = H + RA - (0.06571 * t) - 6.622
    
        #9. adjust back to UTC
        UT = T - lngHour
        UT = self.forceRange( UT, 24) # UTC time in decimal format (e.g. 23.23)
    
        #10. convert UT value to local time zone of latitude/longitude
        hr = self.forceRange(int(UT), 24)
        min = int(round((UT - int(UT))*60,0))
        utcT = datetime.datetime(year,month,day,hr,min,0,0,datetime.UTC)

        #10. Return
        return utcT

    def forceRange( self, v, max ):
        # force v to be >= 0 and < max
        if v < 0:
            return v + max
        elif v >= max:
            return v - max
    
        return v
