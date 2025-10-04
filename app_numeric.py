##  Module:		    app_numeric
##  Description:    Computation module
##  Contains:       arand               A better random number generator than the built-in one
##                  cryptorand          A cryptographic random number generator
##                  get_julian_date     Return the julian date
##                  get_julian_time     Return the julian time
##                  is_leap_year        Return true if the specified year is a leap year
##                  get_sun_times       Return the sun rise, solar noon, and sun set times
##                  get_moon_phase      Return the current phase of the moon
##                  get_mars_time       Return the current martian coodinated time
##                  simple_project      A simple latitiude projection on to a map
##                  gps_dir_deg_*       Haversine or Rhumb-line computation of heading between points
##                  gps_dist_km_*       Haversine or Rhumb-line computation of distance between points
##                  day_fraction        Convert input time to a day fractional (0.00 = midnight (am), 1.00 = 23:59)
##                  ltc_to_utc          Conversion between LTC and UTC times
##                  utc_to_ltc
##                  round_to_val        Round a float to another float based on the accuracy figure
##                  check_time_in_range Check that a time is within a specified time range

import datetime
import math
import juliandate
import suntime
import ephem
import numpy
import os


## ------------------------------------------------------------------------------------------------- FUNCTIONS

## A better random number generator than the one that comes with python

def arand (n, lo, hi):
    a = -1
    while ((a < lo) or (a > hi)):
        a = int.from_bytes(os.urandom(n), byteorder='big')
    return (a)

def cryptorand (n):
    a = numpy.frombuffer(os.urandom(n*4), dtype=numpy.uint32) >> 5
    b = numpy.frombuffer(os.urandom(n*4), dtype=numpy.uint32) >> 6
    return (a * 67108864.0 + b) / 9007199254740992.0
    

## The dice parameter must be a string of the form 'xdy' such that x = number of dice to roll, and
## y = the range (1, y) of a single die.  D&D rules apply.

def roll_dice (dice):
    x       = int(dice[0:1])
    y       = int(dice[2:])
    result  = 0
    for i in range(x): result = result + arand(1, 1, y)
    return (result)
    

## Return the Julian date for a given date/time.  Date/time should be in UTC.  Default
## value is "now".

def get_julian_date (dt = datetime.datetime.now(datetime.UTC)):
    jd = juliandate.from_gregorian(dt.year, dt.month, dt.day)
    return (jd)
    
def get_julian_time (dt = datetime.datetime.now(datetime.UTC)):
    jt = juliandate.from_gregorian(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    return (jt)


## Determine if the given year is a leap year.  Return <True | False>.

def is_leap_year (year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


## Return the sunrise, sunset, and solar noon times (in local time) as a tuple, for the
## given lat/lon coordinates and date.   IMPORTANT: All sun computations are done using
## UTC and the results are also in UTC.  Conversion must be done to local time for this
## to make any sense at all.

def get_sun_times (lat, lon, dt = datetime.datetime.now(datetime.UTC)):
    sun = suntime.Sun(lat, lon)
    sr  = sun.get_sunrise_time(dt)
    ss  = sun.get_sunset_time(dt)
    if (ss < sr):
        ss = ss + datetime.timedelta(days=1)
    sn  = ((ss - sr) / 2) + sr
    return ([sr, sn, ss])


## Return the phase of the moon for the given time and location.  Phase is returned as a
## floating point number (0.0 = new, 0.5 = full, 1.0 = new again).

def get_moon_phase (lat, lon, dt = datetime.datetime.now()):
    d   = ephem.Date(datetime.date(dt.year, dt.month, dt.day))  ## fetch the ephemeris date
    nnm = ephem.next_new_moon(d)                                ## find the next new moon
    pnm = ephem.previous_new_moon(d)                            ## and the previous one
    lun = (d - pnm)/(nnm - pnm)                                 ## lunation is the ratio of the difference
    return (lun)

    
## Return the current martian sol and optionally, time within that sol.  Computed based on 
## the terrestrial Julian date from the algorithm at: https://en.wikipedia.org/wiki/Timekeeping_on_Mars
## Test example:     UTC = 2023-02-11 21:40:12
## Julian date:      2459987.402917
## Should render as: sol 53008 martian standard time 3:22
## Data is returned as a tuple: [sol, hh, mm]

def get_mars_time (dt = datetime.datetime.now(datetime.UTC)):
    jt = get_julian_time(dt)                        ## start with the julian date/time
    cc = 32.184 / 86400.0                           ## terrestrial time to UTC correction
    md = (jt + cc - 2405522.0025054) / 1.0274912517 ## martian date
    ml = math.floor(md)                             ## martian sol
    mf = md - ml                                    ## fractional day
    mh = math.floor((mf * 1440.00) / 60.00)         ## martian hours
    mm = int((mf * 1440.00) - (mh * 60.00))         ## martian minutes
    return ([int(ml), int(mh), mm])


## Determine the heading from GPS coordinate 1 to GPS coordinate 2.  In this case, the order makes a big difference.  The
## <lat1, lon1> coordinates represent the location of THIS system.   The <lat2, lon2> coordinates are the location of the
## remote thing.   Note that we're doing the computation in REVERSE order (i.e.: using the location of this system as the
## destination and not the source). This is because we're displaying (in example) "northwest of..." instead of "southeast
## to...".

## The haversine versions of the function use the "great circle" formula, which gives the shortest distance and direction
## but can lead to unexpected results in that the "as the crow flies" direction is sometimes counterintuitive, especially
## if the shortest path is near one of the poles. The rhumb versions use the "Rhumb-line" formula which leads to a longer
## distance, but with more intuitive directions as it tries to keep a constant distance with respect to the poles.

def simple_project(latitiude: float) -> float:
    return math.tan((math.pi / 4) + (latitiude / 2))
    
def gps_dir_deg_haversine (lat1, lon1, lat2, lon2):
    hapi  = math.pi / 180.0
    lat1  = lat1 * hapi         ## convert to radians
    lat2  = lat2 * hapi
    dlon  = (lon1 - lon2) * hapi
    x     = math.cos(lat1) * math.sin(dlon)
    y     = (math.cos(lat2) * math.sin(lat1)) - (math.sin(lat2) * math.cos(lat1) * math.cos(dlon))
    brad  = math.atan2(x, y)
    b     = int(brad / hapi)
    if (b < 0):
        b = b + 360
    return (b)

def gps_dir_deg_rhumb (lat1, lon1, lat2, lon2):
    lat_a = math.radians(lat2)
    lon_a = math.radians(lon2)
    lat_b = math.radians(lat1)
    lon_b = math.radians(lon1)
    
    a = simple_project(lat_a)
    if (a == 0): a = 0.01
    delta_psi = math.log(simple_project(lat_b) / a)
    delta_lambda = lon_b - lon_a

    if abs(delta_lambda) > math.pi:
        if delta_lambda > 0:
            delta_lambda = -(2 * math.pi - delta_lambda)
        else:
            delta_lambda = 2 * math.pi + delta_lambda
    return int(math.degrees(math.atan2(delta_lambda, delta_psi)))
    

## Determine the distance in kilometers between two GPS coordinates. 

k_earth_radius = 6367

def gps_dist_km_haversine (lat1, lon1, lat2, lon2):
    hapi  = math.pi / 180.0
    dLat  = ((lat2 - lat1) * hapi) / 2.00       ## distance between latitudes and longitudes (divided by 2)
    dLon  = ((lon2 - lon1) * hapi) / 2.00
    lat1  = lat1 * hapi                         ## convert to radians
    lat2  = lat2 * hapi
    a     = (((math.sin(dLat))) * ((math.sin(dLat)))) + (((math.sin(dLon))) * ((math.sin(dLon))) * ((math.cos(lat1))) * ((math.cos(lat2))))
    c     = 2.00 * ((math.atan2(math.sqrt(a), math.sqrt(1.00 - a))))
    return int(k_earth_radius * c)

def gps_dist_km_rhumb (lat1, lon1, lat2, lon2):
    lat_a = math.radians(lat2)
    lon_a = math.radians(lon2)
    lat_b = math.radians(lat1)
    lon_b = math.radians(lon1)

    delta_phi = lat_b - lat_a
    a = simple_project(lat_a)
    if (a == 0): a = 0.01
    delta_psi = math.log(simple_project(lat_b) / a)
    delta_lambda = lon_b - lon_a

    if abs(delta_psi) > 10e-12:
        q = delta_phi / delta_psi
    else:
        q = math.cos(lat_a)
    if abs(delta_lambda) > math.pi:
        if delta_lambda > 0:
            delta_lambda = -(2 * math.pi - delta_lambda)
        else:
            delta_lambda = 2 * math.pi + delta_lambda

    dist = math.sqrt(delta_phi * delta_phi + q * q * delta_lambda * delta_lambda) * k_earth_radius
    return int(dist)


## Convert the input time to a day fractional (0.00 = midnight (am), 1.00 = 23:59:59).  Conversely, format
## the day fractional as hh:mm 

def day_fraction (t = datetime.datetime.now()):
    d = float(t.hour) / 24.00
    d = d + ((float(t.minute) / 60) / 24)
    d = d + (((float(t.second) / 60) / 60) / 24)
    return (d)
    
def day_fraction_format (t):
    hh = math.floor(t * 24)
    mm = math.floor(((t * 24) - hh) * 60)
    s  = ""
    if (hh < 10): s = "0"
    s = s + str(hh) + ":"
    if (mm < 10): s = s + "0"
    s = s + str(mm)
    return (s)


## Functions for converting between LTC and UTC using the current timezone offset.  Offset is given
## as an integer in the form: <+|->hhmm.  Example: PDT = utc_to_ltc(-700, UTC)
    
def ltc_to_utc (offset, ltc = datetime.datetime.now()):
    hh = int(offset / 100)
    mm = int(abs(offset) % 100)
    if (offset < 0):
        mm = mm * -1
    utc = ltc - datetime.timedelta(hours=hh, minutes=mm)
    return (utc)
    
def utc_to_ltc (offset, utc = datetime.datetime.now(datetime.UTC)):
    hh = int(offset / 100)
    mm = int(abs(offset) % 100)
    if (offset < 0):
        mm = mm * -1
    ltc = utc + datetime.timedelta(hours=hh, minutes=mm)
    return (ltc)
    

## Round the input number to the nearest value (defaulted to 0.05) and return it to y decimal 
## places (defaulted to 2).

def round_to_val (x, b = 0.05, y = 2):
    return (round(b * round(x / b), y))


## Check that the datetime stamp is inside the bounding box defined by the initial datetime
## and the final datetime - return true if it is. This is its own function (rather than one
## included in python) because we want to ignore any embedded timezone information and just
## compare the numbers. To make comparisons easy, we turn each timestamp to integer numbers
## equal to:  yyyymmddhhmm

def check_time_in_range (dt, dti, dtf):
    i = (dti.year * 100000000) + (dti.month * 1000000) + (dti.day * 10000) + (dti.hour * 100) + (dti.minute)
    t = ( dt.year * 100000000) + ( dt.month * 1000000) + ( dt.day * 10000) + ( dt.hour * 100) + ( dt.minute)
    f = (dtf.year * 100000000) + (dtf.month * 1000000) + (dtf.day * 10000) + (dtf.hour * 100) + (dtf.minute)
    return ((t >= min(i, f)) and (t <= max(i, f)))


## Get the emphemeris data for any of the major planets (including the moon).  If the planet id is -1,
## then choose a planet at random.

planet_list = [ "null", "mercury", "venus", "the moon", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto" ]

def return_planet_ephem (dt, planet_id):
    if   (planet_id < 0):   planet_id = arand(1, 1, 10)     ## return a random planet
    if   (planet_id == 1):  p = ephem.Mercury(dt)           ## create an ephemeris object for the planet
    elif (planet_id == 2):  p = ephem.Venus(dt)
    elif (planet_id == 3):  p = ephem.Moon(dt)
    elif (planet_id == 4):  p = ephem.Mars(dt)
    elif (planet_id == 5):  p = ephem.Jupiter(dt)
    elif (planet_id == 6):  p = ephem.Saturn(dt)
    elif (planet_id == 7):  p = ephem.Uranus(dt)
    elif (planet_id == 8):  p = ephem.Neptune(dt)
    elif (planet_id == 9):  p = ephem.Pluto(dt)
    else:                   return ""
    
    c = ephem.constellation(p)
    return ( planet_list[planet_id] + " is in the constellation of " + c[1].lower() )
    

