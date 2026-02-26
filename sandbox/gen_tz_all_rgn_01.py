### Generate the time zone files all_rgn.txt file from the timezone boundary
### builder.  Just grab every region, in order, from that.
### This makes use of:
###    https://github.com/GeospatialPython/pyshp
###    https://github.com/evansiroky/timezone-boundary-builder/releases

import shapefile

p = "C:/Users/eg494f/Downloads/timezones-with-oceans.shapefile.zip"  ## point this to the location of the timezone .zip file
print ("reading file: " + p)
sf = shapefile.Reader(p)                                             ## open up the time zone file and count the number of zones
sfrecs = sf.records()
shapes = sf.shapes()
numshapes = len(sfrecs)
print ("number of zones: " + str(numshapes))

astr = ""
for i in range(0, numshapes):
    astr = ((sf.record(i))[0]).lower()
    astr = astr.replace("_", " ")
    bbox = shapes[i].bbox
    alat = int(1000 * ((bbox[1] + bbox[3]) / 2))
    alon = int(1000 * ((bbox[0] + bbox[2]) / 2))
    slat = format(abs(alat), '05d')
    slon = format(abs(alon), '06d')
    if (alat >= 0): slat = "+" + slat
    else:           slat = "-" + slat
    if (alon >= 0): slon = "+" + slon
    else:           slon = "-" + slon
    res = slat + "," + slon + ";" + astr + " "
    numtildes = 47 - len(res)
    for j in range(numtildes): res = res + "~"
    print (res)
