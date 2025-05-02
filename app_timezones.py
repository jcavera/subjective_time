## Module:      app_timezones
## Description: Functions for determining the timezone in which a set of geographic coordinates
##              resides.
## Contains:    get_timezone        Return the timezone ID for the given geographic coordinates
##              get_timezone_data   Return the timezone data for the given timezone ID
##              get_timezone_file   Return the offset for a particular timezone, given the timezone file name and date

import os
import datetime
from dataclasses import dataclass

import app_files
import app_numeric

## ------------------------------------------------------------------------------------------------- STRUCTURES

@dataclass
class tz_info:
    region: int   = 0       ## index in the timezone data file
    lat:    float = 0.00    ## representative timezone latitude
    lon:    float = 0.00    ## representative timezone longitude
    offset: int   = 0       ## timezone offset = (hours * 100) + minutes (-9999 = use lookup)
    name:   str   = ""      ## name of the timezone
    lookup: str   = ""      ## name of the lookup file for the timezone data


## ------------------------------------------------------------------------------------------------- FUNCTIONS

## Data from this location: https://github.com/evansiroky/timezone-boundary-builder/releases
## And time zone names:     https://www.iana.org/time-zones
## 
## The code in "test_each_point.py" was run in QGIS against the full timezone (with oceans) data set 
## to produce region data files.  These files consist of lines in the following format:
## 
##     <longitude>;<latitude>;<region ID>\n
## 
## with both longitude and latitude being multiplied by 100 and then rounded to the nearest 5 (0.05 
## degrees).  Region is an index to the line in the region data file.  An example of a single line:
## 
##     -17995;-8500;204
## 
## This indicates that the point (-179.95, -85.00) falls in to region 204 (Antarctica/Macquarie).  If 
## a region is not found, the algorithm returns a -1 to indicate a singularity.  This can result if a 
## point is at a boundary of two different regions. To eliminate these, the resulting file is scanned 
## and singularities are resolved manually.
## 
## The LabVIEW VI, "rgn file to rle string.vi", is then used to do run-length encoding on each region 
## file in order to come up with a single line for each line of longitude.  This encoding reduces the 
## size of the data set by a factor of (on the average) 500, without sacrificing the simplicity of 
## finding the region of a single point.  One line is of the form:
## 
##     <longitude>;<latitude 0>;<region 01>;<latitude 1>;<region 12>;<latitude 2>;..;<latude m>;<region mn>;<latitude n>
## 
## As an example:
##     
##     -1970;-8500;206;-7165;439;6310;300;6635;439;7345;93;7500;105;8290;439;8495
## 
## These lines can be scanned based on the longitude (rounded to 0.05 degrees) and the latitude in the 
## starting and ending range.  Taking the above line as an example, a position of (-19.70, 10.05) would 
## fall in region 439 (Etc/GMT+1).
## 
## I generated the region and RLE files in parts (in order to effectively monitor the process and catch 
## singularities).  The RLE files were then combined in to a single, master file, covering all co-
## ordinates from -180.00 to 180.00 longitude, and -85.00 to 85.00 latitude, in 0.05 degree steps.  I 
## then used the LabVIEW VI, "rle file to data array v2.vi", to create two separate files.  This VI 
## combines each line in the RLE file in to a single array by the following process:
## 
## 1)  The RLE file is converted in to an array of strings, one per line in the file.
## 2)  Each line is stepped through in a for loop, one at a time.
## 3)  The line is converted in to an array of integers (I16 type).
## 4)  The first two numbers (index 0 and 1) are stripped off of the array.  The first number is the
##     longitude and the second is always the same for every line (-8500).
## 5)  An empty U8 array is created to serve as the final data array.  An empty I32 array is created
##     to serve as the final index array.
## 6)  If any element in the current line array is not equal to any element in the previous line array...
##     a)  The array is decimated in to two separate arrays (fragment A and B).  Array fragment A contains
##         the elements at even indicies in the original (0, 2, 4,...), and fragment B contains the elements
##         at odd indicies (1, 3, 5,...).
##     b)  The two fragments are stepped through in a for loop, indexing each element in turn.  The ith
##         element in each fragment is then operated on (Ai, Bi).
##     c)  The value of 8500 is added to Bi to change its range from 0 to 17000.  It is then divided (integer
##         division) by 5 to change its range from 0 to 3400.  This allows it to fit in to 12 bits.
##     d)  The range of Ai is from 0 to 451, allowing it to fit in to 9 bits.
##     e)  The first eight bits (bits 0..7) of Ai are cast to an unsigned 8-bit (U8) integer (U8_1).
##     f)  The first two bits of a U8 (bits 0..1 of U8_2) are set to the ninth and tenth bits (bits 8..9) of Ai.
##     g)  The remaining bits of U8_2 (bits 2..7) are set to the first six bits (0..5) of Bi.
##     h)  The remaining 8 bits of Bi (bits 6..13) are set to a U8 integer (U8_3, bits 0..7 respectively).
##     i)  These three U8 integers (U8_1..U8_3) are appended to a sub-array.  Following the indexing of the
##         array fragments, this U8 sub-array will have three elements for every two elements in the original
##         current line array.  Since the original current line array of of data type I16, this saves one
##         byte per entry.
##     j)  The size of the final data array (in bytes) is determined.  This size is appended to the final
##         index array.
##     k)  The sub-array is appended to the final data array.
## 7)  If every element in the current line array is equal to every element in the previous line array...
##     a)  The size of the final data array (in bytes) is determined.  This size is appended to the final
##         index array.
## 8)  The final data array is written to the binary file, "all_tz.map", in big-endian format.
## 9)  The final index array is written to the binary file, "all_tz.idx", in big-endian format.
## 
## The upshot of this is that the entire timezone map is compressed down from nearly 100 megs, to just
## over 400 kilobytes (with a separate index file requiring 29 kilobytes).  This is not data compression
## in the traditional sense, but data optimization.  Therefore, no complex decompression schemes need to
## be implemented on reading the information, allowing almost any microcontroller (with the capacity to
## actually store all of the map and index data) to implement the reading algorithm.
## 
## Given a set of input co-ordinates (longitude, latitude), their corresponding time zone can be determined 
## through the following process:
## 
## 1)  If the latitude is less than or equal to -85.00 degree, or greater than or equal to 85.00, the time
##     zone is 316 (Etc/UTC).  If it is between -85 and +85 degrees...
## 2)  Latitude is muliplied by 100 to give the lat co-ordinate.
## 3)  Multiply the longitude by 100 to put it in the range of -18000 to 18000.  Add 18000 to change the
##     range to 0 to 36000.  Divide it by 5 to change the range to 0 to 7200.  This gives a single offset
##     to each point in the input file.  
## 4)  From the input file, read the I32 at this offset (I32_1) and at offset + 1 (I32_2).  If the offset 
##     is the last point in the index file, then set I32_2 to be the size of the map data file.
## 5)  As a byte array (U8), read in all of the data in the map data file from I32_1 to I32_2.  The largest
##     line in the data file is 208 bytes long, so if you are pre-allocating the data array, it does not
##     need to be any larger than that.
## 6)  Step through the map data array, 3 points at a time (U8_1, U8_2, U8_3).
##     a)  I16_1 represents the region ID.  The first 8 bits of this are U8_1 (bits 0..7) and the next two
##         bits (8..9) are the first two (0..1) bits of U8_2.  Unused bits in I16_1 (10..15) are set to 0.
##     b)  I16_2 represents the latitude.  The first 6 bits of this (0..5) are the upper 6 bits (2..7) of
##         U8_2.  The next 8 bits (6..13) are all of the bits in order (0..7) of U8_3.  Unused bits in I16_2
##         (14..15) are set to 0.
##     c)  Multiply I16_2 by 5, and then subtract 8500 from it to put in in the range of -8500 to 8500.
## 
##         As an example of the reassembly algorithm:
## 
##             ## values are from the input line:
##             ##      -18000;-8500;204;-7000;426;-1975;397;-1555;426;-965;398;-920;...
##             ## which encodes to:
##             ##      CC B0 04 AA 65 14 8D B5 15 AA 8D 17 8E B1 17 ...
##         
##             uint8_t U8_1 = 0xAA;
##             uint8_t U8_2 = 0x65;
##             uint8_t U8_3 = 0x14;
##             int16_t rgn  = U8_1 + ((U8_2 & 3) << 8);
##             int16_t lat  = ((((U8_2 & 252) >> 2) + (U8_3 << 6)) * 5) - 8500;
##             printf("Region = %d [426] , Lat = %d [-1975] \n", rgn, lat);
## 
##         Given the values for U8_1..U8_3, this algorithm should print the line:
##         
##             Region = 426 [426] , Lat = -1975 [-1975]
## 
##     d)  If lat is less than or equal to I16_2, then stop the indexing and return I16_1 as the region.
##     e)  If lat is greater than I16_2, go to the next set of three bytes.
## 
## This algorithm returns a region ID that can then be used as an index in to the region list to get the
## actual time zone for the input co-ordinates, down to a resolution of 0.05 degrees in both longitude and
## latitude.

## Get the timezone for the given coordinates.  If the timezone cannot be determined, return -1.  Otherwise, the timezone
## is an index in to the all_rgn.txt file.  WARNING: This makes use of platform-specific file system calls and so must be
## re-written for each particular platform.  OTHER WARNING: The parameters (alat, alon) MUST be expressed no smaller than
## 0.05 degrees.  We'll round to that to make sure.

def get_timezone (alat, alon):
    if ((alat < -90.00) or (alat > 90.00)):                             ## return null on invalid cases
        return (-1)
    if ((alon < -180.00) or (alon > 180.00)):
        return (-1)
    if (alat <= -89.50):                                                ## if at the south pole, region = pacific/auckland
        return (390)
    if ((alat <= -84.95) or (alat >= 84.95)):                           ## if too far north or south, region = 316 (Etc/UTC)
        return (316)
    alat = app_numeric.round_to_val(alat)                               ## force these to 0.05 degree increments
    alon = app_numeric.round_to_val(alon)
    
    region = -1
    lat    = int( alat * 100.0 )                                        ## turn lat and lon into pointers to the index file
    lon    = int( (((alon * 100.0) + 18000.0) / 5.0) * 4.0 )

    ## For <lat = 47.45, lon = -122.65> we should have a lon index of 4588 (5735), and a lat index
    ## of 4745.  This is your sanity check...
    
    ## print ("--- lon index [4588 (5735)] = " + str(lon) + " (" + str((alon * 100) + 18000) + ")")
    ## print ("--- lat index [4745       ] = " + str(lat))
    
    f_idx  = open(app_files.file_tz_index, mode='rb')                   ## open up the index file
    f_idx.seek(lon, 0)                                                  ## jump to the position as given by the "lon" pointer
    start = app_files.file_read_uint(f_idx)                             ## grab the next 4 bytes as an uint32_t
    
    ##  If the longitude is 180.00, then there is no stop location in the index file, and we just
    ##  read all the way to the end of the map file.  In that instance, set the stop location to
    ##  zero as a flag that we're going to read the rest.
    if (alon == 180.0):
        stop = 0
    else:
        ##  If the longitude is less than 180.00, we need to figure out where to stop reading the map
        ##  file.  We do this by getting the next location, and then reading everything from start to
        ##  stop.  It is possible that the stop location is the same as the start location. This will
        ##  happen when two entries in the map file are the same and duplicates are eliminated in the
        ##  name of saving space.  If they are the same, then we keep scanning until we find one that
        ##  is different.
        stop = app_files.file_read_uint(f_idx)
        while (stop == start):
            stop = app_files.file_read_uint(f_idx)
    
    f_idx.close()                                                       ## done with the index file
    
    ## Now it's time to open up the map file and read its data from the appropriate spot.  There
    ## are no lines longer than 208 bytes and so we've hard-coded the map data array to that.
    
    f_map  = open(app_files.file_tz_map, mode='rb')                     ## open up the index file
    
    ## If stop is zero, then that's our flag that there's nothing past the last data line (i.e.:
    ## we're at +180.00 degrees longitude).  In that case we need to figure out where the end of
    ## the map data file is and use that as our stopping point.
    
    if (stop == 0):
        f_map.seek(0, 2)                                                ## move to the end of file
        stop = f_map.tell()                                             ## get the byte offset
        f_map.seek(0, 0)                                                ## move back to the start
    slen = stop - start
    
    ## Now that we have a valid start and stop, we can actually read the data.  For the aforementioned
    ## <lat,lon> coordinates, we should have a map start of 33039, a map stop of 33060, and a map span
    ## of 21.  This is your sanity check...
    
    ## print(" --- map start (33039) = " + str(start))
    ## print(" --- map stop  (33060) = " + str(stop))
    ## print(" --- map slen  (   21) = " + str(slen))
    
    f_map.seek(start, 0)                                                ## move to the map start
    map_dat = f_map.read(slen)                                          ## read x-bytes to an array
    f_map.close()

    ## We now have a buffer full of data, so we can step-through it and convert it from its optimized
    ## form in to our original scheme of [region][latitude][region][latitude]...
    ## Next sanity check: map data = be 29 26 85 e0 29 c2 dc 2b 5f ac 2c 66 50 2d c6 80 32 be 1d 35
    
    ## print("\nbe292685e029c2dc2b5fac2c66502dc68032be1d35")
    ## print(bytes(map_dat).hex())    
    
    ##  Step through the array three bytes at a time and copy them in to placeholder values. And the
    ##  values with 0x00FF in order to have enough room to bit shift and to clear out extra data.
        
    i = 0
    while (i < slen):
        ua = map_dat[i]
        ub = map_dat[i + 1]
        uc = map_dat[i + 2]
        
        ##  Region is equal to all of the bits of the first U8, and the first two bits of the second.
        
        region = ua + ((ub & 3) * 256)
        
        ##  Latitude is a little more complicated. It's equal to the last six bits of the second U8 and
        ##  all of the bits of the third.  And then we have to multiply by 5 and subtract 8500 from the
        ##  value in order to get actual latitude.
        
        i_lat = ((((ub & 252) / 4) + (uc * 64)) * 5) - 8500;
        
        ##  If our current latitude is less than the latitude in the map file, then we've found the right
        ##  region and we can get out of here.  Otherwise, we go on to the next three bytes and start the
        ##  process over.  The process ends when we get a hit.  This is guaranteed to always return valid
        ##  data since (a) we designed the map file that way, and (b) we already accounted for the limits
        ##  of far-north and far-south.
        
    ##  print(" +++ i = " + str(i) + " [ " + hex(ua) + " " + hex(ub) + " " + hex(uc) + " ] r = " + str(region) + ", lat = " + str(i_lat) )
        
        if (lat <= i_lat):
            break
        i = i + 3
    
    ## Final sanity check from the above printf statement:
    ##     +++ i = 0 [ 0xbe 0x29 0x26 ] r = 446, lat = 3710
    ##     +++ i = 3 [ 0x85 0xe0 0x29 ] r = 133, lat = 4900
    ##     new tz : 134
    
    return (region + 1)


## Return the region information for a given region ID number.  The region information comes from the
## "file_region" file ("all_rgn.txt").   The format of the file (and some representative lines) is as
## follows:
##      000000000011111111112222222222333333333344444444445555
##      012345678901234567890123456789012345678901234567890123
##      -- a -|-- b --|--------------- c --------------|-- d -
##      +04050,+009700;africa/douala ~~~~~~~~~~~~~~~~~~ +01:00
##      +27154,-013203;africa/el aaiun ~~~~~~~~~~~~~~~~ z_021.
##      +08484,-013234;africa/freetown ~~~~~~~~~~~~~~~~~~~~~~~
##
## chars 00-05: latitude in the form  a =  <+|->ddfff
## chars 07-13: longitude in the form b = <+|->dddfff
## chars 15-46: timezone name as string (delimited by ~ character)
## chars 48-53: timezone offset in one of three forms...
##                  <+|->hh:mm = hours and minutes of offset from utc
##                  z_nnn.     = the timezone file to lookup for the offset
##                  ~~~~~~~~~~ = no offset from utc

def get_timezone_data (region_id, adate):
    s = app_files.file_read_line(app_files.file_all_rgn, region_id, app_files.k_LEN_ALL_RG)
    atz = tz_info(region = region_id)                           ## set the region id in the struct
    atz.lat  = float(s[0:6]) / 1000                             ## determine the representative lat/lon
    atz.lon  = float(s[7:14]) / 1000
    t        = s.index('~')
    atz.name = s[15:(t - 1)]                                    ## get the timezone name
    
    if ((s[48] == '+') or (s[48] == '-')):                      ## if there is an offset
        atz.offset = (int(s[49:51]) * 100) + int(s[52:54])      ## read the offset time
        if (s[48] == '-'):                                      ## and negate if needed
            atz.offset = 0 - atz.offset
    if (s[48] == 'z'):                                          ## if there is a timezone file
        atz.lookup = dir_z_time + s[48:54] + "txt"              ## read the filename
        atz.offset = get_timezone_file(atz.lookup, adate)
        
    return (atz)


## Return the offset for a particular timezone, given the timezone file name and the year, month, and
## day.  This reads the target timezone file and parses out the information.  Timezone files start at
## line one = year 2023 and extend to year 2099.   Any year outside of that range is invalid and must
## use the closest year in the file (2023 for years less than 2023, and 2099 for years greater than).
##
## The year files are structured as follows:
##      0000000000111111111122222222223333333333444444444455555555
##      0123456789012345678901234567890123456789012345678901234567
##      a --|--b--|--c--|--d--|--e--|--f--|--g--|--h--|--i--|--j--
##      2027:-0500;03-14;-0400;11-07;-0500~~~~~~~~~~~~~~~~~~~~~~~~
##
## chars 00-03  a = the year for which the line is valid
## chars 05-09  b = the start-of year offset
## chars 11-15  c = the first break mm-dd
## chars 17-21  d = the offset starting on the date of the first break
## chars 23-27  e = the second break mm-dd
## chars 29-33  f = the offset starting on the date of the second break
## chars 35-39  g = the third break mm-dd
## chars 41-45  h = the offset starting on the date of the third break
## chars 47-51  i = the fourth break mm-dd
## chars 53-57  j = the offset starting on the fourth break to the end of the year

def get_timezone_file (fname, adate):
    if (adate.year < 2023):                                     ## trap out invalid years
        adate.year = 2023
    if (adate.year > 2099):
        adate.year = 2099
    s = app_files.file_read_line(fname, (adate.year-2022), app_files.k_LEN_Z_xxxx)
    a = int(s[0:4])                                             ## get each component and test against them
    eoy = datetime.date(year = a, month = 12, day = 31)         ## set the end of year flag
    b = int(s[5:10])                                            ## get the first (only required) offset
    
    for i in range(4):
        k = i * 12                                              ## character offset for each range
        if (s[11 + k] != '~'):                                  ## if the ith date field is valid
            m = int(s[(11 + k):(13 + k)])                       ##      get the month
            d = int(s[(14 + k):(16 + k)])                       ##      get the day
            c = datetime.date(year = a, month = m, day = d)     ##      assemble the date
        else:                                                   ## if invalid
            c = eoy                                             ##      set the date to end of year
        if (adate < c):                                         ## check the interval and return if in range
            return (b)
        if (s[17 + k] != '~'):                                  ## get the next offset if valid
            b = int(s[(17 + k):(22 + k)])
    return (b)


## ------------------------------------------------------------------------------------------------- TEST CODE

def app_timezones_test ():
    ar = get_timezone(47.45, -122.65)
    print("47.45,-122.65: ar = " + str(ar))
    
    ad = datetime.date(year=2024, month=6, day=20)
    print(get_timezone_data(ar, ad))
    print(get_timezone_data(249, ad))
    print(get_timezone_data(49, ad))
    
## app_timezones_test()
