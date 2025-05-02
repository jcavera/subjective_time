##  Module:         app_parser
##  Description:    Primary parser interface
##  Contains        Class - Parser

from dataclasses import dataclass
from dateutil import relativedelta

import datetime
import math
import re

import app_files
import app_strings
import app_numeric
import app_markup

## ------------------------------------------------------------------------------------------------- STRUCTURES

@dataclass
class parser_data:
    attrib:     int         = 0                             ## reference id of the attribution associated with the message
    bg_img:     str         = ""                            ## file name of the current background image
    message:    str         = "welcome to subjective time"  ## initial message for the system (never used)
    
@dataclass
class coordinate:
    ltc:        datetime.datetime                           ## local date/time
    utc:        datetime.datetime                           ## universal date/time
    lat:        float       = 0.0                           ## current latitude
    lon:        float       = 0.0                           ## current longitude
    tz:         int         = 0                             ## current timezone identifier
    tz_off:     int         = 0                             ## current timezone offset (lct = utc + off) in <+|->hhmm

## ------------------------------------------------------------------------------------------------- CLASS - Parser

class Parser:
    
    ## Class initialization function
    
    def __init__ (self):
        self.data  = parser_data()                      ## initialize the data structure
    
    
    ## Fetch the next message to display and write it to the work string buffer. If this goes completely pear-shaped,
    ## the failure string gets written to the buffer by the message_get_any() function.  The output string ends up in
    ## the working buffer.  From here it needs to be processed for display and moved to the line buffer.   Parameters
    ## are the current date/time/location coordinate structure and a T/F flag for "on-playa".
    
    def fetch (self, coord, on_playa = False):
        self.data.attrib  = 0                           ## reset all internal data
        self.data.bg_img  = ""
        self.data.message = ""
        s                 = ""                          ## generic string holder
        
        s = self.fetch_high_priority(coord)             ## check for high-priority messages before anything else
        if (s != ""):                                   ## high priority message found
            self.data.message = s
            self.rules_image_display(s)                 ## before going on, check for any image display rules
            return (self.data)
        
        aseed = int((app_numeric.cryptorand(1))[0] * 10000)
        r = app_numeric.arand(1, 1, 100)                ## roll percentile dice
        if (on_playa):                                  ## black rock city rules apply
            if   (r <= 8):                  s = self.fetch_algorithmic(coord)       ## fetch an algorithmic message
            elif ((r > 8) and (r <= 15)):   s = self.fetch_year_based(coord)        ## year-day-based message
            elif ((r > 15) and (r <= 30)):  s = self.fetch_time_based(coord)        ## retreive a time-based message
            elif ((r > 30) and (r <= 50)):  s = self.fetch_res_based(coord, 'brc')  ## black rock city specific message
            else:                           s = ""
        else:                                           ## we are literally anywhere else in the world
            if   (r <= 8):                  s = self.fetch_algorithmic(coord)       ## fetch an algorithmic message
            elif ((r > 8) and (r <= 15)):   s = self.fetch_year_based(coord)        ## year-day-based message
            elif ((r > 15) and (r <= 35)):  s = self.fetch_time_based(coord)        ## retreive a time-based message
            else:                           s = ""
        self.rules_image_display(s)                     ## before going on, check for any image display rules
        s = app_markup.process_me(s, coord)             ## and fix the markups
        if (s == ""):                                   ## if we still don't have a message
            i = 1
            while ((s == "") and (i <= 5)):             ## try up to 5 times for a conditional message
                s = self.fetch_res_based(coord, 'con')
                self.rules_image_display(s)
                s = app_markup.process_me(s, coord)
                i = i + 1
            if (s == ""):                               ## if none of the conditionals worked out
                while ((s == "") and (i <= 25)):        ## try another 20 times for an any-time valid message
                    s = self.fetch_res_based(coord, 'any')
                    self.rules_image_display(s)
                    s = app_markup.process_me(s, coord)
                    i = i + 1
        s = re.sub(' +', ' ', s)                        ## replace multiple spaces with single spaces if needed
        s = re.sub(r'[ ]*[/][ ]*', '/', s)              ## get rid of any oddly formatted line-breaks that may remain
        self.data.message = s
        return (self.data)
    
    
    ## Attempt to get a valid message from the high-priority message file for the current year.  If a valid message is not
    ## found, return null.  The format of the high-priority year file is as follows...
    ## h_yyyy.txt:
    ##      Messages that are tied to a date and time (and possibly geoboxed) for a specific UTC year.  These are higher in
    ##      priority to the ones in r_20xx and are checked first.  Lines in this file are in no particular order and the
    ##      entire file must be walked to find a match.  This file has a particular and unique format, as follows:
    ##          (start time)(end time)(start geobox)(end geobox) message
    ##      Start and end times are in mm-dd HHMM format, always in GMT unless specified.
    ##      Start and end geoboxes are in lat,lon with each coordinate being in <+|->(d)dd.dddd format.
    ##      Latitude must have 2 digits to the left of the decimal; longitude must have 3.
    ##      Start and end geoboxes are set to (-90.0000,-180.0000)(+90.0000,+180.0000) if unused.
    ##      As an example:
    ##          (01-20 1640)(01-20 1710)(-90.0000,-180.0000)(+90.0000,+180.0000) penumbral lunar eclipse ~~~~~~~~~~~~
    ##      If the current date and time is 01-20 at 1700 GMT, anywhere in the world, then this would render as:
    ##          time for the united states to change administrations
    ##      As a geoboxed example:
    ##          (05-16 0134)(05-16 0653)(-90.0000,-154.0000)(+90.0000,+034.0000) time to burn ~~~~~~~~~~~~~~~~~~~~~~~
    ##      Note that the co-ordinates are ALWAYS formatted as: (<+/->dd.dddd,<+/->ddd.dddd) with the latitude first
    ##      and including the sign and leading zeroes as needed.
    ##      
    ##      It is possible to specify LOCAL rather than GMT time by replacing the parentheses in the date and the time 
    ##      specifier with square brackets.  Note that the year, must be the same in LTC as UTC. In example:
    ##          [03-26 2030][03-26 2130](-90.0000,-180.0000)(+90.0000,+180.0000) @623
    ##      If the current date and time is 03-26 at 9pm LOCAL time, anywhere in the world, then this would render as:
    ##          earth hour
    ## For the purposes of reverse engineering the line read, line positions are:
    ##          [03-26 2030][03-26 2130](-90.0000,-180.0000)(+90.0000,+180.0000) penumbral lunar eclipse ~~~~~~~~~~~~
    ##          -----------------------------------------------------------------------------------------------------
    ##          0000000000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999A
    ##          01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
    
    def fetch_high_priority (self, coord):
        yy = coord.ltc.year
        if ((yy < 2024) or (yy > 2100)): return ("")                    ## if year is out of range, return an error
        fname = app_files.dir_h_year + "h_" + str(yy) + ".txt"          ## generate the target file name from the year
        lc = app_files.file_get_lines(fname, app_files.k_LEN_H_20xx)    ## count the number of lines in the target file
        if (lc <= 0): return ("")                                       ## throw an error if the count goes wrong
            
        for i in range(lc):                                             ## iterate through each line and check it
            s = app_files.file_read_line(fname, i + 1, app_files.k_LEN_H_20xx)
            s = self.check_high_priority(s, coord)
            if (s != ""): return (s)
        return ""                                                       ## return a found message (or null if none found)
        
    
    def check_high_priority (self, s, coord):
        a = re.findall(r'[-+]?[\d]+', s)                                ## extract all numbers as a string list
        b = [int(i) for i in a]                                         ## convert all of those to signed ints
        if (s[0] == '['):                                               ## check for local vs utc time
            dt = coord.ltc
        else:
            dt = coord.utc
        s = (s[65:]).strip(' ~')                                        ## get the message and strip off any trailing stuff
        
        ## build a set of date/time structures from the integer list and check against them
        y  = dt.year
        d1 = datetime.datetime(year=y, month=b[0], day=(b[1] * -1), hour=int(b[2] / 100), minute=(b[2] % 100) )
        d2 = datetime.datetime(year=y, month=b[3], day=(b[4] * -1), hour=int(b[5] / 100), minute=(b[5] % 100) )
        if (app_numeric.check_time_in_range(dt, d1, d2)):               ## match for time, now check location
            lat1 = float(a[6]) + (float(a[7]) / 1000)                   ## fetch the location box from the line
            lon1 = float(a[8]) + (float(a[9]) / 1000)
            lat2 = float(a[10]) + (float(a[11]) / 1000)
            lon2 = float(a[12]) + (float(a[13]) / 1000)
            r    = app_numeric.arand(1, 1, 100)                         ## we only want to hit 15% of the time
            if ((coord.lat >= (min(lat1, lat2))) and 
                (coord.lat <= (max(lat1, lat2))) and 
                (coord.lon >= (min(lon1, lon2))) and 
                (coord.lon <= (max(lon1, lon2))) and 
                (r <= 20)):
                return (s)                                              ## if everything matches, return the message
        return ("")                                                     ## not a match, return a nullstring
    
    
    ## Select an algorithmic message at random and add it to the data structure.  Algorithmic messages are either
    ## generated based on the current date/time or are looked up from the file: r_<year>.txt.  To be efficient we
    ## are going to open and grab the appropriate line in the needed r_<year> file before doing anything else and
    ## then just pass that line to the functions that need it.  The format of the r_<year> file is as follows...
    ## 
    ##      -------------- character position -------------------
    ##      0000000000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999
    ##      0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
    ##      -- A --- --- B --- -- C --- ---- D ---- -- E --- -- F --- ----- Z ------
    ##      ddmmyyyy;ddmmyyyyY;ddmmyyyy;kkwwttKKKbb;ddmmyyyy;ddmmyyyy;aaa;bbb;ccc;...
    ##      
    ##      [00..07]    A = Arabic date(Kuwati algorithm, see case 61)
    ##      [09..17]    B = Chinese date(look up table, Y = year sign, see case 70)
    ##      [19..26]    C = hebrew calendar date(look up table, see case 71)
    ##      [28..38]    D = mesoamerican long count calendar date(computed, see case 68)
    ##      [40..47]    E = inidan national calendar date(look up table, see case 73)
    ##      [49..56]    F = coptic calendar date
    ##      [58... ]    Z = variable length, special events by 3 - digit number, separated by semicolons
    ##      End of line is filled with a space then tilde characters up to the maximum line length (100).
    
    def fetch_algorithmic (self, coord):
        s = ""                                                          ## generic string placeholder
        yy = coord.ltc.year
        if ((yy < 2024) or (yy >= 2100)):  return ("")                  ## if year is out of range, return an error
        fname = app_files.dir_r_year + "r_" + str(yy) + ".txt"          ## generate the target file name from the year
        lnum = coord.ltc.timetuple().tm_yday                            ## line number is the day of the year
        line = app_files.file_read_line(fname, lnum, app_files.k_LEN_R_20xx)
        
        r = app_numeric.arand(1, 1, 22) ## roll the dice and...
        if (r == 1) or (r == 2):        s = self.message_algo_sun(coord)                    ## sunrise/sunset for the current date/time/place
        elif (r == 3) or (r == 4):      s = self.message_algo_moon(coord)                   ## the phase of the moon for the current date/time/place
        elif (r == 5):                  s = self.message_algo_julian(coord)                 ## julian date
        elif (r == 6) or (r == 7):      s = self.message_algo_zodiac(coord)                 ## zodiac information
        elif (r == 8) or (r == 9):      s = self.message_algo_islam(coord, line[0:8])       ## islamic calendar date (look up table)
        elif (r == 10) or (r == 11):    s = self.message_algo_china(coord, line[9:18])      ## chinese calendar date or zodiac information (look up table)
        elif (r == 12) or (r == 13):    s = self.message_algo_hebrew(coord, line[19:27])    ## hebrew calendar date (look up table)
        elif (r == 14) or (r == 15):    s = self.message_algo_mayan(coord, line[28:39])     ## mayan long-count calendar (look up table)
        elif (r == 16) or (r == 17):    s = self.message_algo_indian(coord, line[40:48])    ## indian national calendar date (look up table)
        elif (r == 18) or (r == 19):    s = self.message_algo_coptic(coord, line[49:57])    ## coptic calendar date (look up table)
        elif (r == 20):                 s = self.message_algo_mars(coord)                   ## martian calendar date or time
        elif (r == 21):                 s = self.message_algo_burn(coord)                   ## burning man event countdown time
        elif (r == 22):                 s = self.message_algo_extrasol(coord)               ## distance to an extra-solar object
        else:                           return ("")
        return (s)
    
    
    ## Get a year-day-based message (from r_yyyy file) - zero on failure, line number on found. If there is
    ## no failure in reading the file, then assemble the line based on the associated indicies in the macro
    ## table.  This only holds for year files that we have (year < 2100).   If we do not have the year file
    ## in question (or if its read failed), then read the day number line straight from the macro file.  If
    ## even that fails, return null.
    ## r_20xx.txt:
    ##      Messages that are tied to a date for a specific year, all with equal probability.  Lines are
    ##      indexed by day of the year such that each file has 365 (or 366 for leap years) lines.
    
    def fetch_year_based (self, coord, thing = 0):
        s    = ""                                                       ## line placeholder
        yy   = coord.ltc.year
        lnum = coord.ltc.timetuple().tm_yday                            ## line number is the day of the year
        
        if ((yy > 2023) and (yy < 2100)):                               ## if there is a r_year file for this year
            fname = app_files.dir_r_year + "r_" + str(yy) + ".txt"                  ## generate the target file name from the year
            line = app_files.file_read_line(fname, lnum, app_files.k_LEN_R_20xx)    ## read the line number
            line = line[58:104].strip('~ ')                                         ## extract the macro.txt file indicies
            n    = [int(i) for i in (line.split(';'))]                              ## change them to an integer list and append
        else:
            if ((app_numeric.is_leap_year(yy) == False) and 
                (coord.ltc.month >= 3)):                                ## if we're not a leap year and the month is march or later, we
                lnum = lnum + 1                                         ## have to add 1 to the day since macro.txt assumes a leap year
            n    = [ lnum ]                                             ## set the day of the year as the first line number

        for j in n:                                                     ## step through each entry in the macro.txt file
            s = s + app_files.file_read_line(app_files.file_macro, j, app_files.k_LEN_R_MACR)   ## grab the jth line (in the set n)
            try:                                                                                ## get rid of any eol flags (~)
                eos  = s.index('~')
                s    = s[:(eos-1)]
            except:                                                                 ## or just strip trailing spaces if no eol
                s    = s.strip()
            s = s + ";"                                                             ## tack on a delimiter and get the next line
        
        if (thing == 1): return (s)                                     ## return every option on debug flag
        s = app_strings.choose_between(s, ';')                          ## fetch a random one
        return (s)
    
    
    ## From the r_time list - return the line number, no conditionals in this one.
    ## r_time.txt      Messages that are tied to the time of day, in 5 minute increments. 
    ##                 Extract the line number equal to ((hour * 12) + (minute / 5)).
    
    def fetch_time_based (self, coord, return_all = 0):
        ln = int((coord.ltc.hour * 12) + (coord.ltc.minute / 5)) + 1    ## figure out the line to get from the time.txt file
        if (ln >= 290): return ("")                                     ## return null if that calculation breaks
        s = app_files.file_read_line(app_files.file_time, ln, app_files.k_LEN_R_TIME)   ## grab the line
        try:                                                                            ## get rid of any eol flags
            eos = s.index('~')
            s   = s[:(eos-1)]
        except:
            s   = s.strip()
        if (return_all == 1): return (s)                                ## return every possibility for debugging
        s = app_strings.choose_between(s, ';')                          ## fetch a random one
        if (s != ""):
            r = app_numeric.arand(1, 1, 100)
            if (r < 40): self.data.bg_img = 'hrg'
        return (s)
    
    
    ## From a line-based list (any list) - return "" if a failed, or a valid (unprocessed) string on success
    ## List ID (l) r_xxx.txt type options:
    ##    'brc'     r_brc.txt   Conditional messages from r_anys that are valid ONLY on the playa.  There is an implied
    ##                          check for the location (via timezone = black rock city) to all of these.  They are in
    ##                          their own file so as not to interfere with the previous conditional file.
    ##    'con'     r_cond.txt  Conditional messages from r_anys with a low probablility of hitting (a time range of a
    ##                          single day or a very specific geographic region). These are in their own file in order
    ##                          to increase their probability of being chosen.
    ##    'any'     r_anys.txt  Messages that are always valid regardless of date or time.
    ##
    ## Important note: Each of the aforementioned files must have no more than 65535 lines.
    
    def fetch_res_based (self, coord, type):
        if   (type == 'brc'):   fname = app_files.file_brc              ## figure out which file to open or bail if invalid
        elif (type == 'con'):   fname = app_files.file_cond
        elif (type == 'any'):   fname = app_files.file_any
        else:                   return ("")
        s   = app_files.file_read_random_line(fname)                    ## grab a line at random
        if (s == ""): return ("")                                       ## return a null on read error
        ref = app_strings.get_reference_num(s)                          ## find any reference numbers or reference images
        img = app_strings.get_reference_image(s)
        try:                                                            ## get rid of any eol flags
            eos = s.index('~')
            s   = s[:(eos-1)]
        except:
            s   = s.strip()
        self.data.attrib = ref                                          ## save off the reference and image (if any)
        self.data.bg_img = img
        if ((coord.tz == 452) and (img == 'nop')): return ("")          ## check for "on playa" and "do not display"
        if ((type == 'brc') and (img == '')): self.data.bg_img = 'brc'  ## add a brc background if needed
        return (s)
        
    
    ## Check for any image display rules.  This does not override any current images that
    ## may be in place.
    
    def rules_image_display (self, s):
        if (s == ""): return                                            ## safety check -- pop out if nothing there
        if (self.data.bg_img != ""): return                             ## pop out if there already is an image
        p = app_numeric.arand(1, 1, 100)                                ## roll percentile dice
        
        if (("<G=" in s) and (p < 40)):     self.data.bg_img = "map"    ## map display conditions
        if (("<O=" in s) and (p < 40)):     self.data.bg_img = "map"
        if ("_&" in s):                     self.data.bg_img = "mun"    ## markup for "moon"
        if ("lunar eclipse" in s):          self.data.bg_img = "mun"
        if ("retrograde" in s):             self.data.bg_img = "zod"    ## zodiac related
        if ("perihelion" in s):             self.data.bg_img = "zod"
        if ("aphelion" in s):               self.data.bg_img = "zod"
        if ("are in conjunction" in s):     self.data.bg_img = "zod"
        if ("gahanbar" in s):               self.data.bg_img = "ind"    ## hindu holiday related
        
    
    ## ------------------------------------------------------------------------------------------- algorithmic message generation
    
    ## Display the time around sunrise, solar noon, or sunset.  If thing == 1, return all times as a string for debugging.
    
    def message_algo_sun (self, coord, thing = 0):
        st = app_numeric.get_sun_times(coord.lat, coord.lon, coord.utc) ## compute sunrise, sunset, and solar noon times
        sr = app_numeric.day_fraction(app_numeric.utc_to_ltc(coord.tz_off, st[0]))
        sn = app_numeric.day_fraction(app_numeric.utc_to_ltc(coord.tz_off, st[1]))
        ss = app_numeric.day_fraction(app_numeric.utc_to_ltc(coord.tz_off, st[2]))
        ct = app_numeric.day_fraction(coord.ltc)                        ## get the day fraction for the current time
        s  = ""                                                         ## string for assembly
        r = app_numeric.arand(1, 1, 100)
        
        if (thing == 1):                                                ## debug string
            s =     "sunrise time:  " + app_numeric.day_fraction_format(sr) + "\n"
            s = s + "solar noon:    " + app_numeric.day_fraction_format(sn) + "\n"
            s = s + "sunset time:   " + app_numeric.day_fraction_format(ss) + "\n"
            s = s + "calls to prayer \n"
            s = s + "      fajr:    " + app_numeric.day_fraction_format(sr - 0.04) + "\n"
            s = s + "      zuhr:    " + app_numeric.day_fraction_format(sn) + "\n"
            s = s + "      asr:     " + app_numeric.day_fraction_format((sn + ss) / 2) + "\n"
            s = s + "      maghrib: " + app_numeric.day_fraction_format(ss) + "\n"
            s = s + "      isha:    " + app_numeric.day_fraction_format((ss + 1.00) / 2) + "\n"
            return (s)
        
        if (r < 40):                                                    ## islamic call for prayer times
            if   ((ct >= (sr - 0.04)) and (ct <= (sr))):            s = "fajr"                                              ## morning prayer
            elif ((ct >= (sn))        and (ct <= (sn + 0.04))):     s = "zuhr"                                              ## noon prayer
            elif ((ct >= (sn + 0.05)) and (ct <  (ss))):            s = "asr"                                               ## afternoon prayer
            elif ((ct >= (ss))        and (ct <  (ss + 0.04))):     s = "maghrib"                                           ## sunset prayer
            elif (ct >  (ss + 0.05)):                               s = "isha"                                              ## evening prayer
            if (s != ""): self.data.bg_img = 'isl'
        
        if (s == ""):                                                   ## actual sunrise-sunset relative time
            if   ((ct >= 0)           and (ct <  (sr - 0.01))):     s = app_strings.time_diff_str((sr - ct), "sunrise")     ## before sunrise
            elif ((ct >= (sr - 0.01)) and (ct <= (sr + 0.01))):     s = "sunrise"                                           ## sunrise
            elif ((ct >  (sr + 0.01)) and (ct <  (sn - 0.06))):     s = app_strings.time_diff_str((sr - ct), "sunrise")     ## after sunrise
            elif ((ct >= (sn - 0.06)) and (ct <  (sn - 0.01))):     s = app_strings.time_diff_str((sn - ct), "solar noon")  ## before solar noon
            elif ((ct >= (sn - 0.01)) and (ct <= (sn + 0.01))):     s = "solar noon"                                        ## solar noon
            elif ((ct >  (sn + 0.01)) and (ct <= (sn + 0.06))):     s = app_strings.time_diff_str((sn - ct), "solar noon")  ## after solar noon
            elif ((ct >  (sn + 0.06)) and (ct <  (ss - 0.01))):     s = app_strings.time_diff_str((ss - ct), "sunset")      ## before sunset
            elif ((ct >= (ss - 0.01)) and (ct <= (ss + 0.01))):     s = "sunset"                                            ## sunset
            elif ((ct >  (ss + 0.01)) and (ct <= (ss + 0.03))):     s = "twilight"                                          ## twilight
            elif ((ct >  (ss + 0.03)) and (ct <= 1.000)):           s = app_strings.time_diff_str((ss - ct), "sunset")      ## after sunset
        return (s)
    
    
    ## Display the phase of the moon.
    
    def message_algo_moon (self, coord):
        a = app_numeric.get_moon_phase(coord.lat, coord.lon, coord.ltc)     ## fetch the phase of the moon
        b = a * 29.53                                                       ## justify as a fraction of the total lunation in days
        s = "under a "                                                      ## init the string
        if   (b <  1.84):   s = s + "new"                                   ## add the phase information
        elif (b <  5.53):   s = s + "waxing crescent"
        elif (b <  9.22):   s = s + "first quarter"
        elif (b < 12.91):   s = s + "waxing gibbous"
        elif (b < 16.61):   s = s + "full"
        elif (b < 20.30):   s = s + "waning gibbous"
        elif (b < 23.99):   s = s + "third quarter"
        elif (b < 27.68):   s = s + "waning crescent"
        elif (b < 29.54):   s = s + "new"
        else:               return ("")                                     ## return null if phase is invalid
        self.data.bg_img = 'mun'
        return (s + " moon")
    
    
    ## Write the current julian date (local time) as a text integer to the working string in the form: julian day two million
    ## four hundred fifty nine thousand five hundred seventy six. 
    
    def message_algo_julian (self, coord):
        s  = "julian day two million "                  ## init the working string
        jd = app_numeric.get_julian_date(coord.utc)     ## fetch the current julian day, drop the fraction, and add one
        j  = int(math.floor(jd)) - 2000000 + 1
        s  = s + app_strings.num_to_text(j)             ## convert to text and add to the string
        return (s)


    ## Write the distance to an extra-solar object (Voyager, Pioneer, etc.)
    
    def message_algo_extrasol (self, coord, thing = 0):
        s  = "the "                                     ## init the working string
        jd = app_numeric.get_julian_date(coord.utc)     ## fetch the current julian day, drop the fraction, and add one
        j  = int(math.floor(jd)) + 1
        r  = app_numeric.arand(1, 1, 50)                ## roll the dice for the object
        if (thing > 0): r = thing                       ## force choice in debug mode

        if (r < 10):                                    ## voyager 1
            ns = "voyager one"                                  ## object name
            js = 2456172                                        ## position start julian date = 2012-09-01
            ps = 1.12e10                                        ## distance (miles) at start date
            ss = 10.59                                          ## speed (miles/sec) at start date
        if ((r >= 10) and (r < 20)):                    ## voyager 2
            ns = "voyager two"                                  ## object name
            js = 2458428                                        ## position start julian date = 2018-11-05
            ps = 1.11e10                                        ## distance (miles) at start date
            ss = 9.534                                          ## speed (miles/sec) at start date
        if ((r >= 20) and (r < 30)):                    ## pioneer 10
            ns = "pioneer ten"                                  ## object name
            js = 2460463                                        ## position start julian date: 2024-06-01
            ps = 1.27e10                                        ## distance (miles) at start date
            ss = 7.65                                           ## speed (miles/sec) at start date
        if ((r >= 30) and (r < 40)):                    ## pioneer 11
            ns = "pioneer eleven"                               ## object name
            js = 2460486                                        ## position start julian date: 2024-06-24
            ps = 1.06e10                                        ## distance (miles) at start date
            ss = 6.93                                           ## speed (miles/sec) at start date
        if (r >= 40):                                   ## new horizons
            ns = "new horizons"                                 ## object name
            js = 2459322                                        ## position start julian date: 2021-04-17
            ps = 4.6e9                                          ## distance (miles) at start date
            ss = 8.5                                            ## speed (miles/sec) at start time
        
        cd = ((j - js) * 86400 * ss) + ps               ## Compute current distance = (days * (sec / day) * speed) + starting
        cd = cd / 1e9                                   ## Convert the current distance to "billions of miles"
        ci = int(math.floor(cd))                        ## convert to an integer and drop the floor for "billions"
        cf = int((cd - ci) * 1000)                      ## take the remainder, mult by 1000, and drop the floor for "millions"
        
        ## string assembly
        
        s  = s + ns + " spacecraft is approximately " + app_strings.num_to_text(ci, False) + " billion "
        if (cf > 0):
            s = s + app_strings.num_to_text(cf, False) + " million "
        s  = s + "miles from the sun"
        if (s != ""): self.data.bg_img = 'pbd'
        return (s)
            
    
    ## Determine the western zodiac information from the current date/location and write it to the working string.
    
    def message_algo_zodiac (self, coord, thing = 0):
        t = (coord.ltc.month * 100) + coord.ltc.day     ## combine month and day for easy comparison: t = mmdd
        s = "under the "                                ## init the working string
        r = app_numeric.arand(1, 1, 50)                 ## roll the dice for the sign scenario
        if (thing > 0): r = thing                       ## force choice in debug mode
        if (r < 10):
            s = app_numeric.return_planet_ephem(coord.utc, r)
        elif (r < 20):
            s = s + "tropical sign of "
            if   ((t >=  321) and (t <  420)):  s = s + "aries"
            elif ((t >=  420) and (t <  521)):  s = s + "taurus"
            elif ((t >=  521) and (t <  621)):  s = s + "gemini"
            elif ((t >=  621) and (t <  723)):  s = s + "cancer"
            elif ((t >=  723) and (t <  823)):  s = s + "leo"
            elif ((t >=  823) and (t <  923)):  s = s + "virgo"
            elif ((t >=  923) and (t < 1023)):  s = s + "libra"
            elif ((t >= 1023) and (t < 1122)):  s = s + "scorpius"
            elif ((t >= 1122) and (t < 1222)):  s = s + "sagittarius"
            elif ((t >= 1222) or  (t <  120)):  s = s + "capricornus"
            elif ((t >=  120) and (t <  219)):  s = s + "aquarius"
            elif ((t >=  219) and (t <  321)):  s = s + "pices"
            else:                               return ("")
        elif (r < 30):
            s = s + "sidreal sign of "
            if   ((t >=  415) and (t <  516)):  s = s + "aries"
            elif ((t >=  516) and (t <  616)):  s = s + "taurus"
            elif ((t >=  616) and (t <  716)):  s = s + "gemini"
            elif ((t >=  716) and (t <  816)):  s = s + "cancer"
            elif ((t >=  816) and (t <  916)):  s = s + "leo"
            elif ((t >=  916) and (t < 1016)):  s = s + "virgo"
            elif ((t >= 1016) and (t < 1117)):  s = s + "libra"
            elif ((t >= 1117) and (t < 1216)):  s = s + "scorpius"
            elif ((t >= 1216) or  (t <  115)):  s = s + "sagittarius"
            elif ((t >=  115) and (t <  215)):  s = s + "capricornus"
            elif ((t >=  215) and (t <  315)):  s = s + "aquarius"
            elif ((t >=  315) and (t <  415)):  s = s + "pices"
            else:                               return ("")
        elif (r < 40):
            s = s + "constellation of "
            if   ((t >=  419) and (t <  514)):  s = s + "aries"
            elif ((t >=  514) and (t <  620)):  s = s + "taurus"
            elif ((t >=  620) and (t <  721)):  s = s + "gemini"
            elif ((t >=  721) and (t <  810)):  s = s + "cancer"
            elif ((t >=  810) and (t <  916)):  s = s + "leo"
            elif ((t >=  916) and (t < 1031)):  s = s + "virgo"
            elif ((t >= 1031) and (t < 1123)):  s = s + "libra"
            elif ((t >= 1123) and (t < 1130)):  s = s + "scorpius"
            elif ((t >= 1130) and (t < 1218)):  s = s + "ophiuchus"
            elif ((t >= 1218) or  (t <  119)):  s = s + "sagittarius"
            elif ((t >=  119) and (t <  215)):  s = s + "capricornus"
            elif ((t >=  215) and (t <  312)):  s = s + "aquarius"
            elif ((t >=  312) and (t <  419)):  s = s + "pices"
            else:                               return ("")
        else:
            s = s + "star "
            if   ((t >=  419) and (t <  514)):  s = s + "hamal"
            elif ((t >=  514) and (t <  620)):  s = s + "aldebaran"
            elif ((t >=  620) and (t <  721)):  s = s + "pollux"
            elif ((t >=  721) and (t <  810)):  s = s + "al tarf"
            elif ((t >=  810) and (t <  916)):  s = s + "regulus"
            elif ((t >=  916) and (t < 1031)):  s = s + "spica"
            elif ((t >= 1031) and (t < 1123)):  s = s + "zubeneschamali"
            elif ((t >= 1123) and (t < 1130)):  s = s + "antares"
            elif ((t >= 1130) and (t < 1218)):  s = s + "rasalhague"
            elif ((t >= 1218) or  (t <  119)):  s = s + "kaus australis"
            elif ((t >=  119) and (t <  215)):  s = s + "deneb algedi"
            elif ((t >=  215) and (t <  312)):  s = s + "sadalsuud"
            elif ((t >=  312) and (t <  419)):  s = s + "alpherg"
            else:                               return ("")
        if (s != ""): self.data.bg_img = 'zod'
        return (s)
    
    
    ## Return the current date in the system of the unified Islamic (Kuwati) calendar.  This information is in the r_yyyy.txt
    ## file.  Islamic calendar information starts at byte zero and runs through byte 7 with the format: ddmmyyyy.
    
    k_islam_m = ["""al-muharram""",     """safar""",                """rabi al-'awwal""",  """rabi ath-thani""",
                 """jumada al-'ula""",  """jumada ath-thaniyah""",  """rajab""",           """sha'ban""",
                 """ramadan""",         """shawwal""",              """du al-qa'dah""",    """du al-hijjah""" ]
    
    def message_algo_islam (self, coord, line, thing = 0):
        dd = int(line[0:2])                                             ## fetch day, month, year
        mm = int(line[2:4]) - 1
        yy = int(line[4:])
        d  = "the " + app_strings.num_to_text(dd, True) + " day of"     ## convert to strings for each
        m  = "the month of " + self.k_islam_m[mm]
        y  = "in the " + app_strings.num_to_text(yy, True) + " year"
        s  = ""
        r  = app_numeric.arand(1, 1, 40)                                ## roll the dice for assembly options
        if (thing == 1):    r = 999                                     ## force to assemble for debug
        if   (r < 10):      s = d + " " + m
        elif (r < 20):      s = m
        elif (r < 30):      s = m + " " + y
        else:               s = d + " " + m + " " + y
        if (s != ""): self.data.bg_img = 'isl'
        return (s)
        
    
    ## Return the current date in the system of the Chinese national calendar.  This information is in the r_yyyy.txt
    ## file.  Chinese calendar information starts at byte 9 and runs through byte 17 with the format: ddmmyyyyY.
    ##
    ## Assembly of the sexagenary year in the part buffer from the year designation character.  Designation characters 
    ## are according to the following table:
    ##    1  wood rat           D  fire rat         P  earth rat        b  metal rat        n  water rat
    ##    2  wood ox            E  fire ox          Q  earth ox         c  metal ox         o  water ox
    ##    3  fire tiger         F  earth tiger      R  metal tiger      d  water tiger      p  wood tiger
    ##    4  fire rabbit        G  earth rabbit     S  metal rabbit     e  water rabbit     q  wood rabbit
    ##    5  earth dragon       H  metal dragon     T  water dragon     f  wood dragon      r  fire dragon
    ##    6  earth snake        I  metal snake      U  water snake      g  wood snake       s  fire snake
    ##    7  metal horse        J  water horse      V  wood horse       h  fire horse       t  earth horse
    ##    8  metal goat         K  water goat       W  wood goat        i  fire goat        u  earth goat
    ##    9  water monkey       L  wood monkey      X  fire monkey      j  earth monkey     v  metal monkey
    ##    A  water rooster      M  wood rooster     Y  fire rooster     k  earth rooster    w  metal rooster
    ##    B  wood dog           N  fire dog         Z  earth dog        l  metal dog        x  water dog
    ##    C  wood pig           O  fire pig         a  earth pig        m  metal pig        y  water pig
    ##
    ## The string is assembled by indexing the arrays k_ChinX (for the elements) and k_ChinY (for the animals), with the character
    ## providing an index to the mapping array k_ChinM.  The elements in the array are equal to (x+1) + (10 * (y+1)); with x being
    ## the index to the element array and y being the index to the animal array, as follows:
    ##    x = 1 [0] wood  (jia, yi)         y = 10 [0] rat    (xi)          y =  70 [ 6] horse   (wu)
    ##    x = 2 [1] fire  (bing, ding)      y = 20 [1] ox     (chou)        y =  80 [ 7] goat    (wei)
    ##    x = 3 [2] earth (wu, ji)          y = 30 [2] tiger  (rin)         y =  90 [ 8] monkey  (shen)
    ##    x = 4 [3] metal (geng, xin)       y = 40 [3] rabbit (mao)         y = 100 [ 9] rooster (you)
    ##    x = 5 [4] water (ren, gui)        y = 50 [4] dragon (chen)        y = 110 [10] dog     (xu)
    ##                                      y = 60 [5] snake  (si)          y = 120 [11] pig     (hai)
    ## The ChiCX and ChiCY arrays are similar, but with pinyin words in place of english.  The exception is that the element array
    ## (ChiCX) has 10 elements rather than five, arranged in pairs for the first v second heavenly element. If the m index is even
    ## (or zero) then the first of the pair is chosen; the second is chosen if m is odd.  The parameter p, if non-zero, designates
    ## that we're using pinyin rather than english terms.
    
    k_ChinX = [ "wood", "fire", "earth", "metal", "water" ]
    k_ChiCX = [ "jia",  "yi",   "bing",  "ding",  "wu", 
                "ji",   "geng", "xin",   "rin",   "gui"   ]
    k_ChinY = [ "rat", "ox",   "tiger", "rabbit", "dragon", "snake", "horse", "goat", "monkey", "rooster", "dog", "pig" ]
    k_ChiCY = [ "zi",  "chou", "yin",   "mao",    "chen",   "si",    "wu",    "wei",  "shen",   "you",     "xu",  "hai" ]
    k_ChiMM = [ "zhengyue", "eryue",   "sanyue", "siyue",  "wuyue",  "liuyue", "qiyue",  "bayue",  "jiuyue", "shiyue", "dongyue", "layue"   ]
    k_ChiMT = [ "zouyue",   "xingyue", "taoyue", "meiyue", "liuyue", "heyue",  "lanyue", "guiyue", "juyue",  "luyue",  "jaiyue",  "bingyue" ]
    
    k_ChinM = [ 11, 21, 32, 42, 53, 63, 74, 84, 95, 105, 111, 121,
                12, 22, 33, 43, 54, 64, 75, 85, 91, 101, 112, 122,
                13, 23, 34, 44, 55, 65, 71, 81, 92, 102, 113, 123,
                14, 24, 35, 45, 51, 61, 72, 82, 93, 103, 114, 124, 
                15, 25, 31, 41, 52, 62, 73, 83, 94, 104, 115, 125 ]
    
    def message_algo_china (self, coord, line, thing = 0):
        aY = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxy"     ## sexagenary year key to index
        dd = int(line[0:2])                                                     ## fetch day, month, year
        mm = int(line[2:4]) - 1
        yy = int(line[4:8])
        try:
            Y  = aY.index(line[8])                  ## fetch the sexagenary year and convert to element and animal
        except:
            return ("")
        ni = self.k_ChinM[Y]                        ## go from the character index to the year matrix
        ye = (ni % 10) - 1                          ## index of the year element
        ya = (int(math.floor(ni / 10))) - 1         ## index of the year animal
        
        d  = "the " + app_strings.num_to_text(dd, True) + " day of"             ## convert to strings for each
        m  = "the month of "
        r  = app_numeric.arand(1, 1, 100)                                       ## roll the dice for traditional v modern month
        if (r <= 50): m  = m + self.k_ChiMT[mm]
        else:         m  = m + self.k_ChiMM[mm]
        
        y  = "in the year of "
        r  = app_numeric.arand(1, 1, 100)                                       ## roll the dice for english v chinese year
        if (thing == 1): r = 0                                                  ## pick english in debug mode
        if (r <= 50): y = y + "the " + self.k_ChinX[ye] + " " + self.k_ChinY[ya]
        else:         y = y + self.k_ChiCX[ye] + " " + self.k_ChiCY[ya]
        
        s  = ""
        r  = app_numeric.arand(1, 1, 50)            ## roll the dice for assembly options
        if (thing == 1):    r = 999                 ## force to assemble for debug
        if   (r < 10):      s = d + " " + m
        elif (r < 20):      s = m
        elif (r < 30):      s = m + " " + y
        elif (r < 40):      s = y
        else:               s = d + " " + m + " " + y
        if (s != ""):   self.data.bg_img = 'chn'    ## set the background image if all went well
        return (s)
        
    
    ## Return the current date in the system of the standard Hebrew calendar. This information is in the r_yyyy.txt file.
    ## Hebrew calendar information starts at byte 19 and runs through byte 26 with the format: ddmmyyyy.   Months greater
    ## than twenty take place in a year with 13 months (rather than 12). The month name array (k_HebM) indexes the months
    ## as follows: {1, 2, 3, 4, 5,... The 6th month name is in the 6th position, but is only valid in 12-month years. The
    ## 6th and 7th month for years with leap months are in the 7th and 8th positions in the array.  Months start again at
    ## position 9 for the 7th month in a non-leap year or 8th month in a leap year.  
    ## So for a leap year, the month names are:  { 1,  2,  3,  4,  5,  -,  6,  7,  8,  9, 10, 11, 12, 13}
    ## For a non-leap year, the month names are: { 1,  2,  3,  4,  5,  6,  -,  -,  7,  8,  9, 10, 11, 12}
    
    k_HebM  = [ "tishrei",   "cheshvan", "kislev", "tevet", "shevat", "adar", "adar alef", 
                "adar beit", "nissan",   "iyar",   "sivan", "tamuz",  "av",   "elul" ]
    
    def message_algo_hebrew (self, coord, line, thing = 0):
        dd = int(line[0:2])                                 ## fetch day, month, year
        mm = int(line[2:4])
        yy = int(line[4:])
        if (mm > 20):                                       ## correct for leap months
            mm = mm - 21
            leap = True
        else:
            mm = mm - 1
            leap = False
        if ((mm > 5) and (leap == True)):  mm = mm + 1;     ## if we're in a leap year, fix the month accordingly
        if ((mm > 6) and (leap == False)): mm = mm + 2;     ## if not in a leap year, then fix the month to that
        
        d  = "the " + app_strings.num_to_text(dd, True) + " day of"     ## convert to strings for each
        m  = "the month of " + self.k_HebM[mm]
        y  = "in the " + app_strings.num_to_text(yy, True) + " year"
        s  = ""
        r  = app_numeric.arand(1, 1, 40)                    ## roll the dice for assembly options
        if (thing == 1):    r = 999                         ## force to assemble for debug
        if   (r < 10):      s = d + " " + m
        elif (r < 20):      s = m
        elif (r < 30):      s = m + " " + y
        else:               s = d + " " + m + " " + y
        if (s != ""): self.data.bg_img = 'heb'
        return (s)
    
    
    ## Return the current date in the system of the mesoamerican long count calendar.  This information is in the r_yyyy.txt
    ## file.  Long count information start at byte 28 and runs through byte 38 with the format: kkwwttKKKbb, whereas...
    ##     kk  = k'in      =      1 day
    ##     ww  = winal     =     20 days
    ##     tt  = tun       =    360 days
    ##     KKK = k'atun    =   7200 days
    ##     bb  = b'ak'tun  = 144000 days (the 13th b'ak'tun runs from 2012-12-21 to 2407-03-26)
    
    def message_algo_mayan (self, coord, line, thing = 0):
        kk  = int(line[0:2])                                    ## fetch date components
        ww  = int(line[2:4])
        tt  = int(line[4:6])
        KKK = int(line[6:9])
        bb  = int(line[9:])
        
        s   = "in the "                                         ## convert to strings
        k   = app_strings.num_to_text(kk, True) + """ k'in"""
        w   = app_strings.num_to_text(ww, True) + " winal"
        t   = app_strings.num_to_text(tt, True) + " tun"
        KK  = app_strings.num_to_text(KKK, True) + """ k'atun"""
        b   = """in the thirteenth b'ak'tun"""
        
        r = app_numeric.arand(1, 1, 120)                        ## roll the dice for assembly options
        if (thing == 1):    r = 25                              ## force to assemble for debug
        if   (r < 10):  s = s + k
        elif (r < 20):  s = s + k + " of the " + w
        elif (r < 30):  s = s + k + " of the " + w + " in the " + t
        elif (r < 40):  s = s + w
        elif (r < 50):  s = s + w + " of the " + t
        elif (r < 60):  s = s + w + " of the " + t + " in the " + KK
        elif (r < 70):  s = s + t
        elif (r < 80):  s = s + t + " of the " + KK
        elif (r < 90):  s = s + t + " of the " + KK + " " + b
        elif (r < 100): s = s + KK
        elif (r < 110): s = s + KK + " " + b
        else:           s = b
        if (s != ""): self.data.bg_img = 'myn'
        return (s)
    
    
    ## Return the current date in the system of the Indian national calendar. This information is in the r_yyyy.txt file
    ## with the structure documented in the message_process_year function. Indian calendar information starts at byte 40
    ## and runs through byte 47 with the format: ddmmyyyy.
    
    k_IndM = [ "chaitra", "vaisakha", "jyeshtha",   "ashadha", "shraavana", "bhadrapada",
               "ashvin",  "kartika",  "agrahayana", "pausha",  "magha",     "phalguna"  ]
    
    def message_algo_indian (self, coord, line, thing = 0):
        dd = int(line[0:2])                                             ## fetch day, month, year
        mm = int(line[2:4]) - 1
        yy = int(line[4:])
        d  = "the " + app_strings.num_to_text(dd, True) + " day of"     ## convert to strings for each
        m  = "the month of " + self.k_IndM[mm]
        y  = "in the " + app_strings.num_to_text(yy, True) + " year"
        s  = ""
        r  = app_numeric.arand(1, 1, 40)                                ## roll the dice for assembly options
        if (thing == 1):    r = 999                                     ## force to assemble for debug
        if   (r < 10):  s = d + " " + m
        elif (r < 20):  s = m
        elif (r < 30):  s = m + " " + y
        else:           s = d + " " + m + " " + y
        if (s != ""): self.data.bg_img = 'ind'
        return (s)
        
    
    ## Return the current date in the system of the Coptic calendar. This information is in the r_yyyy.txt 
    ## file.  Coptic calendar information starts at byte 49 and runs through byte 56 with the
    ## format: ddmmyyyy.
    
    k_CopM = [ "thout",    "paopi",   "hathor", "koiak", "tobi",   "meshir", "paremhat",
               "parmouti", "pashons", "paoni",  "epip",  "mesori", "pi kogi enavot"  ]
    
    def message_algo_coptic (self, coord, line, thing = 0):
        dd = int(line[0:2])                                             ## fetch day, month, year
        mm = int(line[2:4]) - 1
        yy = int(line[4:])
        d  = "the " + app_strings.num_to_text(dd, True) + " day of"     ## convert to strings for each
        m  = "the month of " + self.k_CopM[mm]
        y  = "in the " + app_strings.num_to_text(yy, True) + " year"
        s  = ""
        r  = app_numeric.arand(1, 1, 40)                                ## roll the dice for assembly options
        if (thing == 1):    r = 999                                     ## force to assemble for debug
        if   (r < 10):  s = d + " " + m
        elif (r < 20):  s = m
        elif (r < 30):  s = m + " " + y
        else:           s = d + " " + m + " " + y
        if (s != ""): self.data.bg_img = 'cop'
        return (s)
        
    
    ## Return the current martian sol and time.
    
    def message_algo_mars (self, coord, thing = 0):
        mars = app_numeric.get_mars_time(coord.utc)                     ## fetch the martian time as [sol, hh, mm]
        if (mars[0] == 0): return ("")
        s = "sol " + app_strings.num_to_text(mars[0])
        r = app_numeric.arand(1, 1, 40)                                 ## roll the dice for assembly options
        if (thing == 1):    r = 999                                     ## force to assemble for debug
        if (r > 20):
            s = s + " coordinated mars time "
            s = s + app_strings.num_to_text(mars[1]) + " "
            if (mars[2] < 10): s = s + "oh "
            s = s + app_strings.num_to_text(mars[2])
        if (s != ""): self.data.bg_img = 'mrs'
        return (s)
        
    
    
    ## Compute the months and days until the next Burning Man events for either gate opening, man burn, or
    ## temple burn.  This is based on the labor day dictionary.  This will not be active past August 20 of
    ## the year in question.
    
    ld_dic = {  2024: "09-02",  2025: "09-01",  2026: "09-07",  2027: "09-06",  2028: "09-04",  2029: "09-03",  2030: "09-02",
                2031: "09-01",  2032: "09-06",  2033: "09-05",  2034: "09-04",  2035: "09-03",  2036: "09-01",  2037: "09-07",
                2038: "09-06",  2039: "09-05",  2040: "09-03",  2041: "09-02",  2042: "09-01",  2043: "09-07",  2044: "09-05",
                2045: "09-04",  2046: "09-03",  2047: "09-02",  2048: "09-07",  2049: "09-06",  2050: "09-05",  2051: "09-04",
                2052: "09-02",  2053: "09-01",  2054: "09-07",  2055: "09-06",  2056: "09-04",  2057: "09-03",  2058: "09-02",
                2059: "09-01",  2060: "09-06",  2061: "09-05",  2062: "09-04",  2063: "09-03",  2064: "09-01",  2065: "09-07",
                2066: "09-06",  2067: "09-05",  2068: "09-03",  2069: "09-02",  2070: "09-01",  2071: "09-07",  2072: "09-05",
                2073: "09-04",  2074: "09-03",  2075: "09-02",  2076: "09-07",  2077: "09-06",  2078: "09-05",  2079: "09-04",
                2080: "09-02",  2081: "09-01",  2082: "09-07",  2083: "09-06",  2084: "09-04",  2085: "09-03",  2086: "09-02",
                2087: "09-01",  2088: "09-06",  2089: "09-05",  2090: "09-04",  2091: "09-03",  2092: "09-01",  2093: "09-07",
                2094: "09-06",  2095: "09-05",  2096: "09-03",  2097: "09-02",  2098: "09-01",  2099: "09-07",  2100: "09-06"  }
    
    def message_algo_burn (self, coord, thing = 0):
        if (coord.ltc.year > 2100): return ("")                             ## bail if we don't have the labor day data
        if (coord.ltc.month > 8): return ("")                               ## doesn't work for september or later
        if ((coord.ltc.month == 8) and (coord.ltc.day > 19)): return ("")   ## also not for later than august 19th
        target = str(coord.ltc.year) + '-' + self.ld_dic[coord.ltc.year]    ## build the target date string
        tdate  = datetime.datetime.strptime(target, "%Y-%m-%d")             ## and convert to a date
        
        temple = tdate - datetime.timedelta(days=1)                         ## find dates of temple burn, man burn, and gate
        man    = tdate - datetime.timedelta(days=2)
        gate   = tdate - datetime.timedelta(days=8)
        r      = app_numeric.arand(1, 1, 120)                               ## roll the dice for event options
        if (thing > 0): r = thing                                           ## force to assemble for debug
        
        if (r < 40):    ddif = relativedelta.relativedelta(temple, coord.ltc)       ## option - temple burn
        elif (r < 80):  ddif = relativedelta.relativedelta(man, coord.ltc)          ## option - man burn
        else:           ddif = relativedelta.relativedelta(gate, coord.ltc)         ## option - gate opening
        
        mm   = ddif.months                                                  ## mm months...
        if (mm == 0):   s = ""
        elif (mm == 1): s = "one month "
        else:           s = app_strings.num_to_text(mm) + " months "
        
        dd   = ddif.days                                                    ## dd days...
        if (dd == 0):   s = s + "until "
        elif (dd == 1): s = s + "one day until "
        else:           s = s + app_strings.num_to_text(dd) + " days until "
        if (r < 40):    s = s + "the temple burns"                          ## add back the event string
        elif (r < 80):  s = s + "the man burns"
        else:           s = s + "the gates open"
        if (s != ""): self.data.bg_img = 'brc'                              ## and the brc background
        return (s)
        

## ------------------------------------------------------------------------------------------------- FUNCTIONS

## As a test, return absolutely everything possible for the current date/time and default location

def return_everything ():
    ltc = datetime.datetime.now()                   ## init the times
    utc = datetime.datetime.now(datetime.UTC)
    lat = 47.434765                                 ## Port Orchard, Washington, USA, Earth
    lon = -122.668934
    tz  = 134                                       ## time zone: north america/los angeles
    tzo = -700                                      ## offset: PDT = -700, PST = -800
    c   = coordinate(ltc, utc, lat, lon, tz, tzo)   ## setup the coordinate structure
    p   = Parser()
    
    print (p.message_algo_sun(c, 1))
    print ("moon phase:        " + p.message_algo_moon(c) )
    print ("julian date:       " + p.message_algo_julian(c) )
    print ("martian time:      " + p.message_algo_mars(c, 1) )
    print ("burning man times: ")
    print ("  " + p.message_algo_burn(c, 20) )
    print ("  " + p.message_algo_burn(c, 60) )
    print ("  " + p.message_algo_burn(c, 100) + "\n")
    
    print ("zodiac signs: ")
    print ("  " + p.message_algo_zodiac(c, 1)  )
    print ("  " + p.message_algo_zodiac(c, 2)  )
    print ("  " + p.message_algo_zodiac(c, 3)  )
    print ("  " + p.message_algo_zodiac(c, 4)  )
    print ("  " + p.message_algo_zodiac(c, 5)  )
    print ("  " + p.message_algo_zodiac(c, 6)  )
    print ("  " + p.message_algo_zodiac(c, 7)  )
    print ("  " + p.message_algo_zodiac(c, 8)  )
    print ("  " + p.message_algo_zodiac(c, 9)  )
    print ("  " + p.message_algo_zodiac(c, 15) )
    print ("  " + p.message_algo_zodiac(c, 25) )
    print ("  " + p.message_algo_zodiac(c, 35) )
    print ("  " + p.message_algo_zodiac(c, 45) + "\n")
    
    fname = app_files.dir_r_year + "r_" + str(ltc.year) + ".txt"                    ## generate the target file name from the year
    lnum = ltc.timetuple().tm_yday                                                  ## line number is the day of the year
    line = app_files.file_read_line(fname, lnum, app_files.k_LEN_R_20xx)
        
    print ("islamic calendar:  " + p.message_algo_islam(c, line[0:8], 1) )          ## islamic calendar date (look up table)
    print ("chinese calendar:  " + p.message_algo_china(c, line[9:18], 1) )         ## chinese calendar date or zodiac information
    print ("hebrew calendar:   " + p.message_algo_hebrew(c, line[19:27], 1) )       ## hebrew calendar date (look up table)
    print ("mayan calendar:    " + p.message_algo_mayan(c, line[28:39], 1) )        ## mayan long-count calendar (look up table)
    print ("hindu calendar:    " + p.message_algo_indian(c, line[40:48], 1) )       ## indian national calendar date (look up table)
    print ("coptic calendar:   " + p.message_algo_coptic(c, line[49:57], 1) + "\n") ## coptic calendar date (look up table)
    
    print ("extra-solar objects:")
    print ("    " + p.message_algo_extrasol(c, 5) )
    print ("    " + p.message_algo_extrasol(c, 15) )
    print ("    " + p.message_algo_extrasol(c, 25) )
    print ("    " + p.message_algo_extrasol(c, 35) )
    print ("    " + p.message_algo_extrasol(c, 45) )
    
    print ("high priority:     " + p.fetch_high_priority(c) )
    print ("special days for today:")
    s = p.fetch_year_based(c, 1)
    daylist = s.split(";")
    for ss in daylist:
        if (ss != ""): print("  " + app_markup.process_me(ss, c) )
    
    print ("")
    print ("time-based entries for right now:")
    s = p.fetch_time_based(c, 1)
    daylist = s.split(";")
    for ss in daylist:
        if (ss != ""): print("  " + app_markup.process_me(ss, c) )
    
    print ("")
    print ("conditional entries for right now:")
    flen = app_files.file_get_lines(app_files.file_cond, app_files.k_LEN_R_ANYS)
    for i in range(1, flen):
        s = app_files.file_read_line(app_files.file_cond, i, app_files.k_LEN_R_ANYS)
        try:                        ## get rid of any eol flags
            eos = s.index('~')
            s   = s[:(eos-1)]
        except:
            s   = s.strip()
        s = app_markup.process_me(s, c)
        if (s != ""): print("  " + s)
    
    print ("")
    for i in range(10):
        s = p.fetch_res_based(c, 'brc')
        s = app_markup.process_me(s, c)
        sa = p.data.bg_img
        if (sa == ""): sa = "   "
        sb = "    "
        if (p.data.attrib > 0): sb = "{0:04}".format(p.data.attrib)
        if (s != ""): print ("random brc " + str(i) + ":  [" + sb + "][" + sa + "] " + s)
    print ("")
    for i in range(10):
        s = p.fetch_res_based(c, 'any')
        s = app_markup.process_me(s, c)
        sa = p.data.bg_img
        if (sa == ""): sa = "   "
        sb = "    "
        if (p.data.attrib > 0): sb = "{0:04}".format(p.data.attrib)
        if (s != ""): print ("random any " + str(i) + ":  [" + sb + "][" + sa + "] " + s)
    print ("")
    for i in range(10):
        s = p.fetch_res_based(c, 'any')
        s = app_markup.process_me(s, c)
        sa = p.data.bg_img
        if (sa == ""): sa = "   "
        sb = "    "
        if (p.data.attrib > 0): sb = "{0:04}".format(p.data.attrib)
        if (s != ""): print ("random any " + str(i + 10) + ": [" + sb + "][" + sa + "] " + s)
    print ("")
    for i in range(10):
        s = p.fetch_res_based(c, 'any')
        s = app_markup.process_me(s, c)
        sa = p.data.bg_img
        if (sa == ""): sa = "   "
        sb = "    "
        if (p.data.attrib > 0): sb = "{0:04}".format(p.data.attrib)
        if (s != ""): print ("random any " + str(i + 20) + ": [" + sb + "][" + sa + "] " + s)
        

def return_particular ():
    s = "practice radical self-reliance ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ $p04"
    ref = app_strings.get_reference_num(s)      ## find any reference numbers or reference images
    img = app_strings.get_reference_image(s)
    if (img == ""): img = "   "
    sb = "    "
    if (ref > 0): sb = "{0:04}".format(ref)
        
    try:                                        ## get rid of any eol flags
        eos = s.index('~')
        s   = s[:(eos-1)]
    except:
        s   = s.strip()
    
    print ("[" + sb + "][" + img + "]  " + s)
    

#### return_everything()
#### return_particular()
