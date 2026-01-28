### Generate the time zone files for every point on the earth (barring the poles) in 0.05 degree increments.
### Refer to issue #12 (Automatic build for the timezone files) for the process on this. And to the timezone
### python file (app_timezones.py) for the format that the system wants to see at the end. This first try is
### just to generate the IDs of every point on the earth and NOT to compress them in to the final files.
### 
### This makes use of:
###    https://shapely.readthedocs.io/en/stable/installation.html
###    https://github.com/GeospatialPython/pyshp
###    https://github.com/evansiroky/timezone-boundary-builder/releases

import numpy
import shapefile
from shapely.geometry import Point
from shapely.geometry import shape

f = open("C:/Users/eg494f/Downloads/tz_test.txt",'w')                ## point this to the location of the output file
p = "C:/Users/eg494f/Downloads/timezones-with-oceans.shapefile.zip"  ## point this to the location of the timezone .zip file
print ("reading file: " + p)
sf = shapefile.Reader(p)                                             ## open up the time zone file and count the number of zones
sfshps = sf.shapes()
sfrecs = sf.records()
numshapes = len(sfshps) - 1
print ("number of zones: " + str(numshapes + 1))

zone_sr = 0
point_to_check = (0.0, 0.0) ## lon, lat
found = 0

def print_me (lon, lat, tz):
    print("lon: " + "{:.2f}".format(lon) + ", lat: " + "{:.2f}".format(lat) + ", zone: " + str(tz) + "              ", end='\r')
    print(str(zone_sr), file=f, end='')
    if (lon < 179.95):
        print(",", file=f, end='')
    else:
        print(" ", file=f)
    return (0)

## latitude runs from -85.00 to 85.00 in 0.05 degree increments
for alat in numpy.arange(-85.00, 85.00, 0.05):
    ## longitude runs from -180.00 to 180.00 in 0.05 degree increments
    ## looks like the valid range may be from -172.50 to 180.00 ???
    for alon in numpy.arange(-172.50, 180.05, 0.05):
        
        point_to_check = (alon, alat)                   ## set the point to check
        if (zone_sr > 0):
            boundary = sfshps[zone_sr - 1]
            if Point(point_to_check).within(shape(boundary)):
                print_me(alon, alat, zone_sr)
                found = 1
            else:
                found = 0
        
        if (found == 0):
            zone_sr = 0
            for i in range(0, numshapes):
                boundary = sfshps[i]
                if Point(point_to_check).within(shape(boundary)):
                    zone_sr = i + 1
                    print_me(alon, alat, zone_sr)
                    break
                    
            if (zone_sr == 0):
                print_me(alon, alat, 0)

print("\n *** done ***")
