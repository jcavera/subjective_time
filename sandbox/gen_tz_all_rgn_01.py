### Generate the time zone files all_rgn.txt file from the timezone boundary
### builder.  Just grab every region, in order, from that.
### This makes use of:
###    https://github.com/GeospatialPython/pyshp
###    https://github.com/evansiroky/timezone-boundary-builder/releases

from time import time
import shapefile
import pytz
from datetime import datetime, timedelta

def supports_dst (tz_name):
    tz = pytz.timezone(tz_name)                 ## set the timezone to the incoming zone
    adate = datetime(2025, 1, 1, 12, 0, 0)      ## init the date to 2025-01-01
    utc_off_sr = int(tz.utcoffset(adate).total_seconds())   ## init the offset shift register
    for i in range(0, 364):
        adate = adate + timedelta(days=1)                   ## go to the next day
        utc_off = int(tz.utcoffset(adate).total_seconds())  ## get the offset for this date
        if (utc_off_sr != utc_off):  return " 9"            ## return a 9 second flag if the offset changes in the year
        utc_off_sr = utc_off                                ## update the shift register
    if (utc_off_sr == 0):  return "~~~~~~~"     ## return if no offset changes and offset == 0
    if (utc_off_sr < 0):   astr = " -"          ## otherwise format to: <+/->hh:mm
    else:                  astr = " +"
    utc_off_sr = abs(utc_off_sr)
    hours = utc_off_sr // (60*60)
    utc_off_sr %= (60*60)
    minutes = utc_off_sr // 60
    astr = astr + "%02i:%02i" % (hours, minutes)
    return astr

p = "C:/Users/eg494f/Downloads/timezones-with-oceans.shapefile.zip"  ## point this to the location of the timezone .zip file
print ("reading file: " + p)
sf = shapefile.Reader(p)                                             ## open up the time zone file and count the number of zones
sfrecs = sf.records()
shapes = sf.shapes()
numshapes = len(sfrecs)
print ("number of zones: " + str(numshapes))

for i in range(0, numshapes):
    astr = ((sf.record(i))[0])                      ## grab the ith timezone name
    bstr = astr.lower()                             ## convert to lower case and replace _ with spaces
    bstr = bstr.replace("_", " ")
    bbox = shapes[i].bbox                           ## find the center-ish of the timezone
    alat = int(1000 * ((bbox[1] + bbox[3]) / 2))
    alon = int(1000 * ((bbox[0] + bbox[2]) / 2))
    slat = format(abs(alat), '05d')                 ## format the center as: <+/->xxxxx,<+/->yyyyyy
    slon = format(abs(alon), '06d')
    if (alat >= 0): slat = "+" + slat
    else:           slat = "-" + slat
    if (alon >= 0): slon = "+" + slon
    else:           slon = "-" + slon
    res = slat + "," + slon + ";" + bstr + " "      ## assemble the line as: <+/->xxxxx,<+/->yyyyyy;timezone/name ~~~~~~~~
    numtildes = 47 - len(res)
    for j in range(numtildes): res = res + "~"
    res = res + supports_dst(astr)                  ## and add the offset string
    
    print (res)
