### Generate the time zone files all_rgn.txt file from the timezone boundary
### builder.  Just grab every region, in order, from that.  If needed, also
### generate timezone (z_) files for those zones that require it.
### This makes use of:
###    https://github.com/GeospatialPython/pyshp
###    https://github.com/evansiroky/timezone-boundary-builder/releases

import shapefile
import pytz
from datetime import datetime, timedelta

### Build a file for the particular timezone.  File is of the form:
###    000000000011111111112222222222333333333344444444445555555555
###    012345678901234567890123456789012345678901234567890123456789
###    
###    2023:+0100;01-14;+0000;02-18;+0100;12-30;+0000 ~~~~~~~~~~~~
###    
###    Bytes 00..03:  four digit year
###    Bytes 05..09:  the offset in <+/->hhmm from GMT at the start of the year
###    Bytes 11..15:  the MM-DD of the first changeover, occuring at 0100 local time
###    Bytes 17..21:  the offset in <+/->hhmm from GMT after the first changeover
###    Bytes 23..27:  the MM-DD of the second changeover, occuring at 0100 local time
###    Bytes 29..33:  the offset in <+/->hhmm from GMT after the second changeover
###    Bytes 35..39:  the MM-DD of the third changeover, occuring at 0100 local time
###    Bytes 41..45:  the offset in <+/->hhmm from GMT after the third changeover
###    Bytes 47..51:  the MM-DD of the fourth changeover, occuring at 0100 local time
###    Bytes 52..57:  the offset in <+/->hhmm from GMT after the fourth changeover
###    
###    Timezone lines always start at 2023 and run through 2099

def build_zone_file (tz_name, zfile_name):
    for y in range(2023, 2100):             ### produce a single line for the year (y)
        return

### Build the offset portion of the string equal to...
###    ~~~~~~~  if the time zone offset from UTC is 00:00 and DST is not observed
###     +hh:mm  if the time zone offset from UTC is +hh:mm and DST is not observed
###     -hh:mm  if the time zone offset from UTC is -hh:mm and DST is not observed
###     z_iii.  if the time zone offset varies during the year (DST or otherwise)

def supports_dst (tz_name, tz_idx):
    astr = ""
    tz = pytz.timezone(tz_name)                 ## set the timezone to the incoming zone
    adate = datetime(2025, 1, 1, 12, 0, 0)      ## init the date to 2025-01-01
    utc_off_sr = int(tz.utcoffset(adate).total_seconds())   ## init the offset shift register
    for i in range(0, 364):
        adate = adate + timedelta(days=1)                   ## go to the next day
        utc_off = int(tz.utcoffset(adate).total_seconds())  ## get the offset for this date
        if (utc_off_sr != utc_off):  
            astr = " z_" + "%03i" % tz_idx + "."
            build_zone_file(tz_name, astr)                  ## build a new time zone file
            return astr                                     ## return zone file name if offset changes
        utc_off_sr = utc_off                                ## update the shift register
    if (utc_off_sr == 0):  return "~~~~~~~"     ## return null if no offset from GMT
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
    res = res + supports_dst(astr, i + 1)           ## and add the offset string
    
    print (res)
