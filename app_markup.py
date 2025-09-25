##	Module:			    app_markup
##	Description:	    Process all of the markup characters in a string for the app.
##  Primary:            process_me              Primary markup processor and (should be the) only interface
##  Helper Functions:   get_24_to_12h           Convert a 24-hour time to a 12-hour time
##                      get_season              Return the season given the current date-time
##  Sub-processors:     conditions              Check the conditional statements (if any)
##                      sub_year                Handle the case of (<a|b|o>-xxxx)
##                      sub_macro               Handle macro subsititutions (_<?>)
##                      sub_numeric             Handle numeric substitutions (#nnnn)
##                      sub_computed            Handle computed substitutions (<xxxxx...)
##  Sub-sub-processors: sub_subproc_A           lat-lon coordinates rendered as the nearest whole number
##                      sub_subproc_B           benedryl cucumber's birthday
##                      sub_subproc_C           ordinal century
##                      sub_subproc_D           day of the week
##                      sub_subproc_G           distance and/or direction from the specified gps coordinates
##                      sub_subproc_Hh          hour (24 hour format)
##                      sub_subproc_M           month of the year
##                      sub_subproc_N           random month of the year
##                      sub_subproc_O           random distance and/or direction
##                      sub_subproc_P           random on-playa location
##                      sub_subproc_Rr          random number
##                      sub_subproc_S           season of the year
##                      sub_subproc_W           random day of the week
##                      sub_subproc_Y           year
##                      sub_subproc_Z           name of the current timezone
##                      sub_subproc_d           ordinal date of the month
##                      sub_subproc_e           event classification (this is a weird one)
##                      sub_subproc_i           hour (12 hour format)
##                      sub_subproc_mn          minutes
##                      sub_subproc_p           am or pm string
##                      sub_subproc_s           substitution for the current hemisphere (south | north)
##                      sub_subproc_t           randomizer: time to | just about time to | a good time to | ...
##                      sub_subproc_y           ordinal day of the year
##                      sub_subproc_qq          random choice between multiple items in a list

from dataclasses import dataclass
import re
import datetime
import math
import time

import app_strings
import app_numeric
import app_files


## ------------------------------------------------------------------------------------------------- STRUCTURES

@dataclass
class coordinate:
    ltc:        datetime.datetime                           ## local date/time
    utc:        datetime.datetime                           ## universal date/time
    lat:        float       = 0.0                           ## current latitude
    lon:        float       = 0.0                           ## current longitude
    tz:         int         = 0                             ## current timezone identifier
    tz_off:     int         = 0                             ## current timezone offset (lct = utc + off) in <+|->hhmm

## ------------------------------------------------------------------------------------------------- PRIMARY FUNCTION

## Process the message from the working string to the line holding string.  By the time we get to this
## part the working string should have no trailing tildes or space characters, it should have a single
## selection (except for the <? options), and should have no trailing image file or attribution tags.
##
## Processing occurs in the following order:
##      1)  Check for any leading conditional statements.  Return a nullstring if those fail.
##      2)  Perform any year substitutions "(a-...), (b-...), (o-...)" in the string.
##      3)  Perform any k_macro substitutions "_..." in the string.
##      4)  Perform any number substitutions "#..." in the string.
##      5)  Perform any computed substitutions "<..." in the string.

def process_me (s, coord):
    s = conditions(s, coord)                        ## 1) check any conditional statements
    if (s == ""): return ("")                       ##      if conditions fail just pop out
    s = sub_year(s, coord)                          ## 2) perform year substitutions
    s = sub_macro(s)                                ## 3) perform k_macro subsititutions
    s = sub_numeric(s)                              ## 4) perform numeric subsititutions
    s = sub_computed(s, coord)                      ## 5) perform computed substitutions
    return (s)


## ------------------------------------------------------------------------------------------------- HELPER FUNCTIONS

## convert 24-hour time to 12-hour time

def get_24_to_12h (h):
    if (h > 12):    return (h - 12)
    else:           return (h)


## get season based on the current local time (spring = 1, summer = 2, autumn = 3, winter = 4)

def get_season (c):
    y = year = c.ltc.year
    if   (c.ltc < datetime.datetime(year=y, month=3, day=21)):    
        if (c.lat > 0): return (4)
        else:           return (2)
    elif (c.ltc < datetime.datetime(year=y, month=6, day=21)):    
        if (c.lat > 0): return (1)
        else:           return (3)
    elif (c.ltc < datetime.datetime(year=y, month=9, day=21)):    
        if (c.lat > 0): return (2)
        else:           return (4)
    elif (c.ltc < datetime.datetime(year=y, month=12, day=21)):   
        if (c.lat > 0): return (3)
        else:           return (1)
    else: 
        if (c.lat > 0): return (4)
        else:           return (2)
    

## ------------------------------------------------------------------------------------------------- SUB-PROCESSORS

## Check for and process any conditionals that are at the start of the string.  These are indicated if
## the working string start with a '!' character. Everything from that character until the first space
## character is a part of the conditional.  Separate conditionals are broken by commas, and if any one
## fails, then the conditional as a whole fails.  The r_macr, r_time, r_year, and h_yyyy files have no
## conditional statements that need checking.
## 
## Conditions that can be specified are as follows:
##      A   Geographic lAtitude in fractional degrees to three decimal places (ex: 33204)
##      D   day of week (1=Sunday..7=Saturday)
##      H   24-hour GMT clock (0..23)
##      I   12-hour GMT clock (1..12)
##      M   month (1..12)
##      O   Geographic lOngitude in fractional degrees to three decimal places (ex: -117418)
##      T   24-hour time in GMT in HHmm format (0000..2359)
##      Y   4-digit year
##      Z   one-based time zone index
##      d   date (1..31)
##      h   24-hour local clock (0..23)
##      i   12-hour local clock (1..12)
##      m   minutes (0..59)
##      s   seconds (0..59)
##      t   24-hour local time in hhmm format (0000..2359)
##      y   day of the year (1..366)
##      z   season (spring = 1, summer = 2, autumn = 3, winter = 4)
##
## Comparison operators recognized:
##      <   less than
##      =   equal to
##      >   greater than

def conditions (s, coord):
    if (s == ""): return ("")                       ## safety check
    if (s[0] != "!"):                               ## no conditions to check so automatically passes
        try:
            eos = s.index('~')                      ##      find the first eol character
            s   = s[:(eos - 1)]                     ##      strip off all the tildes and return
        except:
            s   = s.strip()
        return (s)
    eos  = s.index(' ')                             ## find the first space character
    rem  = s[(eos + 1):]
    s    = s[1:(eos + 1)]                           ## and get everything from after the '!' to before the ' '
    sset = s.split(',')                             ## then split along the conditional delimiter
    q    = 0
    res  = True
    for cond in sset:                               ## with each condition in the set...
        if   (cond[0] == 'A'):  q = int(coord.lat * 1000)
        elif (cond[0] == 'D'):  q = int(coord.ltc.strftime('%w')) + 1
        elif (cond[0] == 'H'):  q = coord.utc.hour
        elif (cond[0] == 'I'):  q = get_24_to_12h(coord.utc.hour)
        elif (cond[0] == 'M'):  q = coord.ltc.month
        elif (cond[0] == 'O'):  q = int(coord.lon * 1000)
        elif (cond[0] == 'T'):  q = (coord.utc.hour * 100) + coord.utc.minute
        elif (cond[0] == 'Y'):  q = coord.ltc.year
        elif (cond[0] == 'Z'):  q = coord.tz
        elif (cond[0] == 'd'):  q = coord.ltc.day
        elif (cond[0] == 'h'):  q = coord.ltc.hour
        elif (cond[0] == 'i'):  q = get_24_to_12h(coord.ltc.hour)
        elif (cond[0] == 'm'):  q = coord.ltc.minute
        elif (cond[0] == 's'):  q = coord.ltc.second
        elif (cond[0] == 't'):  q = (coord.ltc.hour * 100) + coord.ltc.minute
        elif (cond[0] == 'y'):  q = coord.ltc.timetuple().tm_yday
        elif (cond[0] == 'z'):  q = get_season(coord)
        else:                   return ("")
        v = int(cond[2:])                                   ## get the target quantity
        if   (cond[1] == '<'):  res = (res) and (q < v)     ## make the comparison specified
        elif (cond[1] == '='):  res = (res) and (q == v)
        elif (cond[1] == '>'):  res = (res) and (q > v)
        else:                   return ("")
    if (res):
        try:
            eos  = rem.index('~')                           ## find the first eol character
            rem  = rem[:(eos - 1)]
        except:
            rem = rem.strip()
        return (rem)
    else:
        return ""


## Perform any year substitutions "(a-...), (b-...), (o-...)" in the working string.  Note that there cannot
## be ANY other use of parens in the data strings aside from year substitutions.  Search for regex [(][^abo][^-]
## to verify that none are found.

def sub_year (s, coord):
    if (s == ""):   return (s)                          ## quick safety check
    match = "[(][abo][-][0-9]+[)]"                      ## regex to pick up the thing to substitute
    ys    = re.findall(match, s)                        ## get the set of matching things
    
    if (len(ys) == 0): return (s)                       ## bail if none are found
    cy    = coord.ltc.year
    for y in ys:                                        ## step through each one that is found
        i = y.index(')')                                ## find the closing paren
        n = int(y[3:i])                                 ## and extract the target year
        ord = False
        if (y[1] == 'a'):                               ## year is "AD" so find the difference
            n = cy - n
        elif (y[1] == 'b'):                             ## year is "BC" so find the sum (-1 because there's no year 0)
            n = cy + n - 1
        elif (y[1] == 'o'):                             ## year is "AD" and an ordinal
            n = cy - n
            ord = True
        if (abs(n) < 2): return ("")                    ## return a nullstring if less than two years
        b = app_strings.num_to_text(abs(n), ord)
        if ((y[1] == 'a') or (y[1] == 'b')):            ## for a non-ordinal
            r = app_numeric.arand(1, 1, 100)
            if (n < 0):                                 ## determine before or after
                if (r <= 50): a = " years before"
                else:         a = " years until"
            else:
                if (r <= 50): a = " years after"
                else:         a = " years since"
            b = b + a
        s = s.replace(y, b)
    return (s)


## Perform any k_macro substitutions "_..." in the working string.  Data files cannot use an underscore for any reason
## except for macro substitutions. All macro substitutions are a single underscore followed by a single character, and
## that followed by a single space or valid delimiter (~, ;, |, /).  Strings for macro subsititution, indexed by their
## related character set in the macro map...

k_macro = [ "nativity fast",    "moon",               "since",            "of the",           "night",              "midnight",         
            "somewhere",        "sometime",           "getting",          "approaching",      "in the evening",     "at night",      
            "your",             "month",              "week",             "the feast of",     "festival",           "the discovery of", 
            "almost",           "around",             "nearly",           """o'clock""",      "about",              "approximately", 
            "half past",        "until",              "before",           "after",            "last",               "year",     
            "years",            "months",             "days",             "hours",            "minutes",            "seconds", 
            "right now",        "anniversary",        "quarter",          "in the morning",   "top of the hour",    "bottom of the hour",
            "in the afternoon", "awareness month",    "the invention of", "paces",            "time to",            "a.m.",
            "p.m",              "hundred hours",      "noon",             "time for",         "straight up",        "just after",
            "just before",      "appreciation day",   "awareness day",    "at the start of",  "remembrance",        "the end of", 
            "the beginning of", "the birth of",       "the death of",     "the founding of",  "first",              "day",
            "international",    "birthday",           "national",         "saint",            "the publicaiton of", "chocolate",
            "in the",           "meteors"  ]

k_macro_map = [ "_%",           "_&",                 "_*",               "_,",               "_.",                 "_0",
                "_1",           "_2",                 "_3",               "_4",               "_5",                 "_6",
                "_7",           "_8",                 "_9",               "_:",               "_@",                 "_A",
                "_B",           "_C",                 "_D",               "_E",               "_F",                 "_G",
                "_H",           "_I",                 "_J",               "_K",               "_L",                 "_M",
                "_N",           "_O",                 "_P",               "_Q",               "_R",                 "_S",
                "_T",           "_U",                 "_V",               "_W",               "_X",                 "_Y",
                "_Z",           "_[",                 "_]",               "_`",               "_a",                 "_b",
                "_c",           "_d",                 "_e",               "_f",               "_g",                 "_h",
                "_i",           "_j",                 "_k",               "_l",               "_m",                 "_n",
                "_o",           "_p",                 "_q",               "_r",               "_s",                 "_t",
                "_u",           "_v",                 "_w",               "_x",               "_y",                 "_z",
                "_{",           "_}"     ]


def sub_macro (s):
    if (s == ""): return ("")                           ## safety check
    invalid = "[_].[^ ;|~/]"                            ## check for invalid use of the substitution characters
    bads    = re.findall(invalid, s)                    ## get the set of matching things
    if (len(bads) > 0): return ("")                     ## kill it if there are invalid things found
    l = len(k_macro_map)
    for i in range(l):                                  ## step through the macro map and subsitute everything
        s = s.replace(k_macro_map[i], k_macro[i])
    return (s)
    

## Perform any number substitutions "#..." in the working string.  Data files cannot use the hash symbol for any other
## reason.  All number substitutions are a hash symbol followed by one or more digits, and then followed by a space or
## other valid delimiter.  Use the regex [#][^0-9]+ to make sure that there are no other uses.

def sub_numeric (s):
    if (s == ""): return ("")                           ## safety check
    nums = re.findall("[#][0-9]+", s)                   ## find any instances of a number to expand
    if (len(nums) == 0): return (s)                     ## nothing found so just exit
    nums.sort(key=len, reverse=True)                    ## do the longest tag first
    for n in nums:                                      ## step through the unique number tokens
        a    = int(n[1:])                               ##      grab the integer
        astr = app_strings.num_to_text(a)               ##      convert it to a string
        s    = s.replace(n, astr)                       ##      and replace the appropriate tag
    return (s)
    

## Perform any computed substitutions "<..." in the working string.   This one is really freaking complicated so we have to
## break it in to sub-sub-processors for each possible case in the system. This is a total pain in the ass, but it's really 
## the only way to get good encapsulation in the function calls (at the expense of efficiency, but there we are).  And note
## that there's no other reason to use a less than (<) symbol, except for computed substitutions.   The exeption to this is 
## using in comparisons, when preceeded by a !(character) expression.   But by the time we get to this processing function,
## those should be cleared out.  To find invalid uses, use the regex [ ][<][^ACDGHMOPRSYZdghimnprsty?] on the data files.
## NOTE: Geomagnetic orientation is currently unsupported (until we get a compass in here).

def sub_computed (s, coord):
    if (s == ""): return ("")                           ## safety check
    valid = "[<][ABCDGHMNOPRSWYZdeghimnprsty?][^ ~/]*"  ## regex to find any valid substitution
    subs  = re.findall(valid, s)
    if (len(subs) == 0): return (s)                     ## pop out if nothing found
    for item in subs:                                   ## step through each thing to substitute
        t = item[1]                                                 ## do a thing by subsititution type...
        if   (t == 'A'): s = sub_subproc_A  (s, coord, item)        ## current lat-lon coordinates rendered as the nearest whole number
        elif (t == 'B'): s = sub_subproc_B  (s, coord, item)        ## bandersnatch curbstomp's birthday
        elif (t == 'C'): s = sub_subproc_C  (s, coord, item)        ## ordinal century (e.g.: twenty first)
        elif (t == 'D'): s = sub_subproc_D  (s, coord, item)        ## day (sunday = 1, monday = 2, ...)
        elif (t == 'G'): s = sub_subproc_G  (s, coord, item)        ## distance and/or direction from the specified gps coordinates
        elif (t == 'H'): s = sub_subproc_Hh (s, coord, item)        ## 24-hour GMT clock (0..23).
        elif (t == 'M'): s = sub_subproc_M  (s, coord, item)        ## month (1..12; january, february, ...)
        elif (t == 'N'): s = sub_subproc_N  (s, coord, item)        ## random month
        elif (t == 'O'): s = sub_subproc_O  (s, coord, item)        ## random distance and/or direction
        elif (t == 'P'): s = sub_subproc_P  (s, coord, item)        ## random playa co-ordinates
        elif (t == 'R'): s = sub_subproc_Rr (s, coord, item)        ## random number ranging from N..M
        elif (t == 'S'): s = sub_subproc_S  (s, coord, item)        ## season (spring | summer | fall;autumn | winter)
        elif (t == 'W'): s = sub_subproc_W  (s, coord, item)        ## random day of the week
        elif (t == 'Y'): s = sub_subproc_Y  (s, coord, item)        ## year (e.g: two thousand and fifteen)
        elif (t == 'Z'): s = sub_subproc_Z  (s, coord, item)        ## name of the current timezone
        elif (t == 'd'): s = sub_subproc_d  (s, coord, item)        ## ordinal date of the month (1..31; first, second, ...)
        elif (t == 'e'): s = sub_subproc_e  (s, coord, item)        ## event classification for random playa "events"
        elif (t == 'g'): s = ""                                     ## geomagnetic orientation (degrees and/or north, northeast, east, etc.)
        elif (t == 'h'): s = sub_subproc_Hh (s, coord, item)        ## 24-hour clock (0..23)
        elif (t == 'i'): s = sub_subproc_i  (s, coord, item)        ## 12-hour clock (1..12)
        elif (t == 'm'): s = sub_subproc_mn (s, coord, item)        ## minutes (0..59)
        elif (t == 'n'): s = sub_subproc_mn (s, coord, item)        ## minutes (0..59) GMT (no timezone correction)
        elif (t == 'p'): s = sub_subproc_p  (s, coord, item)        ## AM or PM local time (0 = AM, 1 = PM)
        elif (t == 'r'): s = sub_subproc_Rr (s, coord, item)        ## ORDINAL random number ranging from N..M
        elif (t == 's'): s = sub_subproc_s  (s, coord, item)        ## substitution based on the current hemisphere
        elif (t == 't'): s = sub_subproc_t  (s, coord, item)        ## substitute one of: time to | just about time to | a good time to |...
        elif (t == 'y'): s = sub_subproc_y  (s, coord, item)        ## day of the year (1..366) (add ^ for ordinal: <y^ = 1st...366th)
        elif (t == '?'): s = sub_subproc_qq (s, coord, item)        ## randomly choose between multiple words 
    return (s)

    
## ------------------------------------------------------------------------------------------------- COMPUTED SUBSTITUTION PROCESSORS

## The following are used as sub-processors for individual substitutions of the form "<'character'".  All are of
## the same form, taking as input parameters: original string, current coordinate set, and the item in question.

## Process current lat-lon coordinates rendered as the nearest whole number.  Start/end string data is unused.

def sub_subproc_A (s, coord, item):
    if (s == ""): return ("")                                       ## safety check
    las = app_strings.num_to_text(abs(int(round(coord.lat))))       ## convert latitude and longitude to strings
    los = app_strings.num_to_text(abs(int(round(coord.lon))))
    lad = " north"                                                  ## set north/south and east/west directions
    lod = " east"
    if (coord.lat < 0): lad = " south"
    if (coord.lon < 0): lod = " west"
    a = las + " degrees" + lad + " by " + los + " degrees" + lod
    s = s.replace(item, a)
    return (s)

## Return a random name for the actor "Benedict Cumberbatch".

k_BC = [ "bandicoot coloringbook",     "baritone choirboy",          "benedryl cucumber",            "benedict cumberbatch",         "benzedrine charcoal",
         "benefit carwash",            "ballpark centerfield",       "bellicose custardbath",        "beeinfested cucumberpatch",    "bumpercar crumplezone",
         "burlington coatfactory",     "benevolent computerglitch",  "buildingmaterial cinderblock", "braidedhair yogamat",          "birdfeeder climatechange",
         "beneficial cabbagepants",    "bumblebee cutiebutt",        "badfinger carebearstare",      "barbecue charcuterieboard",    "barrister tennismatch",
         "britishname cantgetitright", "bandersnoot cannabis",       "bustamove charlestondance",    "budapest lumberjack",          "backitup johnnycash",
         "backflipping corgidogs",     "boondoggle campaignmanager", "battlefield counterstrike",    "balancepole carryingcase",     "bathysphere cuttlefish",
         "butternut crinklefries",     "butterfried crunchwrap",     "bedridden catalepticman",      "butcherknife kitchenware",     "beachside contemplation",
         "bangladesh cricketmatch",    "beelzebubs carphonenumber",  "beneficial cholesterol",       "burningman centercamp",        "badminton concubine",
         "bangalore kryptonite",       "build-a-bear comewithme",    "barelylegal codename",         "burningdown campingspot",      "bucketboy compostbin",
         "buffalo cornerstone",        "barristerof collingswood",   "brambleberry creampie",        "berryflavored cookiebatch",    "burberry crochetpattern",
         "bakelite countertop",        "bentonite claycement",       "beachcomber cleanupcrew"       "bendystraw creamsodacup",      "broccolislaw carmelcorn", 
         "boogieman cantgetenough",    "borealis carringtonevent",   "beattheodds kesselrun",        "breakingnews kesslersyndrome", "beveryquiet chasingrabbits",
         "byzantine codedmessage",     "brocaded cummerbund",        "byzantium crusadeknight",      "bollywood cameracrew",         "beneficial cantonfood", 
         "butterfinger candybar",      "bootycall comeovertonight",  "barelynoticed catchphrase",    "balancingact catchersnet",     "baseball catchersmitt",
         "bernardino highwaycrash",    "billionaire casinowinner",   "broccolislaw cupofnoodles",    "bodywork cadillac",            "blacklight cameralens",
         "blackletter calligraphy",    "barcelona krispykreme",      "bossanova carhorn",            "baselessly convicted",         "beverly crushersghost" ]

def sub_subproc_B (s, coord, item):
    if (s == ""): return ("")                                       ## safety check
    r  = app_numeric.arand(1, 0, len(k_BC) - 1)                     ## random selection of the event type
    s = s.replace(item, k_BC[r])
    return (s)
    

## Process ordinal century (e.g.: twenty first). Start/end string data is unused. So this is kind of a cheat
## because there's no way in hell that this code will last until the year 2200.  Which means that we're safe
## with just two options: twenty-first and twenty-second.

def sub_subproc_C (s, coord, item):
    if (s == ""): return ("")                       ## safety check
    if (coord.ltc.year < 2100): a = "twenty first"
    else:                       a = "twenty second"
    s = s.replace(item, a)
    return (s)


## Process the current (local time) day (sunday = 1, monday = 2, ...).  Start/end string data is unused.

k_weekdays = [ "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday" ]

def sub_subproc_D (s, coord, item):
    if (s == ""): return ("")                       ## safety check
    i = coord.ltc.weekday()                         ## fetch the day of the week (monday = 0)
    s = s.replace(item, k_weekdays[i])
    return (s)


## Process the distance and/or direction from the specified gps coordinates.  Start/end designate 
## the '=+xxxxx,+yyyyyy' substring.  Full item is of the form: <G=+ddfff,+dddfff (lat, lon).

k_directions = [ "north", "north by northeast", "northeast", "east by northeast",  "east",
                          "east by southeast",  "southeast", "south by southeast", "south", 
                          "south by southwest", "southwest", "west by southwest",  "west",
                          "west by northwest",  "northwest", "north by northwest", "north" ]

def sub_subproc_G (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    la = float(item[4:6]) + (float(item[6:9]) / 1000.0)                 ## fetch target (lat, lon)
    if (item[3] == '-'): la = -1 * la
    lo = float(item[11:14]) + (float(item[14:]) / 1000.0)
    if (item[10] == '-'): lo = -1 * lo
    
    heading  = app_numeric.gps_dir_deg_rhumb(coord.lat, coord.lon, la, lo)  ## compute distance and direction from target (lat, lon)
    distance = app_numeric.gps_dist_km_rhumb(coord.lat, coord.lon, la, lo)
    if (distance < 25): return ("")                                         ## if too close to call, return null
    if (la < -87.000): heading = "north"
    if (la >  87.000): heading = "south"
    
    dir_idx = int(app_numeric.round_to_val(heading, 22.5) / 22.5)       ## convert direction to string
    dir_str = k_directions[dir_idx] + " of"
    
    r = app_numeric.arand(1, 1, 100)                                    ## 30% chance of converting km to miles
    dis_units = " kilometers"                                           ## convert distance to string
    if (r > 70): 
        distance = distance * 0.62137
        dis_units = " miles"
    dis_str = app_strings.num_to_text(distance) + dis_units
    
    r = app_numeric.arand(1, 1, 90)                                      ## figure out where to
    a = ""
    if   (r < 30):  a = dir_str
    elif (r < 60):  a = dis_str + " from"
    else:           a = dis_str + " " + dir_str
    s = s.replace(item, a)
    return (s)
    

## Process the current hour in 24 - hour GMT(0..23) form.  Start/end string data flag is a single optional
## character (').  If that character is present, then it means that we are parsing HOURS ONLY, i.e.: there
## is nothing following that and we should round to the NEAREST hour.   We use this same function for both
## UTC and LTC hours and just figure out if it's upper- or lower-case "H".

def sub_subproc_Hh (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    if (item[1] == "H"): atime = coord.utc                              ## uppercase H -- use UTC
    else:                atime = coord.ltc                              ## otherwise, use LTC
    hh = atime.hour
    if (len(item) == 3):
        if (item[2] == """'"""):                                        ## we use minutes to round
            if (atime.minute > 30): hh = hh + 1
    if (hh > 24): hh = hh - 24                                          ## make sure we don't overrun
    h  = app_strings.num_to_text(hh)                                    ## convert to string
    if ((hh < 10) and (hh > 0)): h = "oh " + h                          ## add "oh" as in "oh six hundred"
    s = s.replace(item, h)
    return (s)
    

## Process the current (local time) month (1..12; january, february, ...).  Start/end string data is unused.
## The "N" macro is to pick a random month.

k_months = [ "january", "february", "march",     "april",   "may",      "june",
             "july",    "august",   "september", "october", "november", "december" ]

def sub_subproc_M (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    a = k_months[coord.ltc.month - 1]
    s = s.replace(item, a)
    return (s)


def sub_subproc_N (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    mon = app_numeric.arand(2, 1, 12)                                   ## grab a random month
    s = s.replace(item, k_months[mon - 1])
    return (s)
    

## Generate a random distance and/or direction. Start/end designate the '=aaa-bbbb' substring. Note that the
## string in question is in the WORK string.  This is important as it's where we (a) get the random distance
## in the subproc_comp_random() call and (b) we check the string for a "do not display on the playa" flag.
## 
## This flag is in effect if the image to display is $nop.  If the current time zone == 452 AND the current
## image flag is not null, then we fail that test and return zero.   NOTE: This is not checked here, but in 
## the first function, in order to not waste clock cycles.

def sub_subproc_O (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    i        = item.index('-')                                          ## get the distance
    x        = int(item[3:i])
    y        = int(item[(i+1):])
    n        = 1                                                        ## random number size (1 = 0-255, 2 = 0-65535, ...)
    if (y > 255):   n = 2
    if (y > 65535): n = 3
    distance = app_numeric.arand(n, x, y)
    r = app_numeric.arand(1, 1, 100)                                    ## 30% chance of converting km to miles
    dis_units = " kilometers"                                           ## convert distance to string
    if (r > 70): 
        distance = distance * 0.62137
        dis_units = " miles"
    dis_str = app_strings.num_to_text(distance) + dis_units
    heading = k_directions[app_numeric.arand(1, 1, 16)]                 ## get the heading
    r = app_numeric.arand(1, 1, 120)                                    ## figure out where to
    a = ""
    if   (r < 40):  a = heading + " of"
    elif (r < 80):  a = dis_str + " from"
    else:           a = dis_str + " " + heading + " from"
    s = s.replace(item, a)
    return (s)


## Generate random playa co-ordinates.  Start/end string data is unused.

k_playa_loc    = [ "the esplanade",   "the nearest intersection",   "the man",                 "the temple",         "the nearest art project",
                   "the nearest bar", "the nearest sound camp",     "the nearest art car",     "the nearest camp",   "the nearest healing camp",
                   "dpw ghetto",      "the nearest porta potty",    "the nearest plaza",       "the lamplighters",   "the nearest coffee camp",
                   "the airport",     "the nearest science camp",   "the nearest food camp",   "center camp",        "the nearest performance space",
                   "the artery",      "the first camp you see",     "the closest camp to you", "bmir"  ]

k_playa_street = [ """ o'clock""", " fifteen", " thirty", " forty five" ] 
k_playa_letter = [ "esplanade", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j" ]

def sub_subproc_P (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    r = app_numeric.arand(1, 1, 100)                                    ## 40% chance of a direct result
    if (r < 40):
        a = k_playa_loc[app_numeric.arand(1, 0, len(k_playa_loc) - 1)]
    else:
        s1 = app_numeric.arand(1, 2, 10)
        s2 = app_numeric.arand(1, 0, len(k_playa_street) - 1)
        if (s1 == 10):  s2 = 0
        a  = app_strings.k_Ones[s1 - 1] + k_playa_street[s2] + " and "
        s3 = (app_numeric.arand(1, 1, 110)) % 11
        a = a + k_playa_letter[s3]
    s = s.replace(item, a)
    return (s)


## Generate a random number ranging from N..M.  Start/end designate the '=aaa-bbbb' substring. Upper
## case "R" is for the normal form, lower case is for the ordinal form. 

def sub_subproc_Rr (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    i  = item.index('-')                                                ## get the random range
    x  = int(item[3:i])
    y  = int(item[(i+1):])
    n        = 1                                                        ## random number size (1 = 0-255, 2 = 0-65535, ...)
    if (y > 255):   n = 2
    if (y > 65535): n = 3
    r  = app_numeric.arand(n, x, y)
    a  = app_strings.num_to_text(r, (item[1] == 'r'))
    s = s.replace(item, a)
    return (s)


## Process the (local time) season (spring | summer | fall;autumn | winter).  Start/end string data is unused.

k_seasons = [ "spring", "summer", "autumn", "winter" ]

def sub_subproc_S (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    a = k_seasons[get_season(coord) - 1]                                ## fetch the season and add
    s = s.replace(item, a)
    return (s)


## Process the random day of the week (just a shorthand for this: <?sunday|monday|tuesday...).

def sub_subproc_W (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    r  = app_numeric.arand(1, 1, 700)
    if   (r < 100): s = s.replace(item, "sunday")
    elif (r < 200): s = s.replace(item, "monday")
    elif (r < 300): s = s.replace(item, "tuesday")
    elif (r < 400): s = s.replace(item, "wednesday")
    elif (r < 500): s = s.replace(item, "thursday")
    elif (r < 600): s = s.replace(item, "friday")
    elif:           s = s.replace(item, "saturday")
    return (s)    
    

## Process the (local time) year (e.g: two thousand and fifteen).  Start/end string data is unused.

def sub_subproc_Y (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    r  = app_numeric.arand(1, 1, 100)
    if (r <= 50):                                                       ## 50% chance of "two thousand twenty four"
        a = app_strings.num_to_text(coord.ltc.year)
    else:                                                               ## 50% chance of "twenty twenty four"
        y1 = int( math.floor(coord.ltc.year / 100) )
        y2 = coord.ltc.year - (y1 * 100)
        a1 = app_strings.num_to_text(y1)
        a  = a1 + " " + app_strings.num_to_text(y2)
    s = s.replace(item, a)
    return (s)


## Process the name of the current timezone. Start/end string data is unused. Grabs the name of the timezone from
## the all_rgn.txt file, taking the line corresponding to the timezone index and grabbing the name after the last
## slash character and before the tilde character.  This makes use of the number string buffer, since we needed a
## buffer and we weren't using that for anything else.  Example line is as follows:
##      -12118,+096895;indian/the cocos islands ~~~~~~~ +06:30
## Note that there may be TWO dividers, as in the case:
##      -28467,-065783;america/argentina/catamarca ~~~~ -03:00
## Which means that we have to start from the tilde and work backward to find the last divider.

def sub_subproc_Z (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    tz_ln = app_files.file_read_line(app_files.file_all_rgn, coord.tz, app_files.k_LEN_ALL_RG)
    i = tz_ln.rfind('/')
    if (i < 0): return ("")
    j = tz_ln.index('~')
    if (j < 0): return ("")
    a = tz_ln[i+1:j-1]
    s = s.replace(item, a)
    return (s)


## Process the (local time) ordinal date of the month (1..31; first, second, ...).  

def sub_subproc_d (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    a = app_strings.num_to_text(coord.ltc.day, True)
    s = s.replace(item, a)
    return (s)


## Do a substitution for made-up playa events.  

k_event = [ "airplanes",    "alcohol",     "aliens",       "anthropology", "archery",       "architecture",         "art history",       "artificial intelligence",
            "astronomy",    "avionics",    "baking",       "biomimicry",   "blacksmithing", "bluegrass",            "body modification", "body painting",
            "bondage",      "braiding",    "burlesque",    "cephalopods",  "cooking",       "crafting",             "crystals",          "daoism",
            "dance",        "deep time",   "demolitions",  "drag queens",  "drugs",         "dungeons and dragons", "ecology",           "economics",
            "electronics",  "engineering", "fashion",      "fencing",      "filmmaking",    "finance",              "flogging",          "fly fishing",
            "food",         "forestry",    "furries",      "futurism",     "genomics",      "ghosts",               "gnosticism",        "group sex",
            "hacking",      "healing",     "hentai",       "herbalism",    "history",       "humanism",             "icelandic sagas",   "journaling",
            "kung fu",      "landscaping", "linguistics",  "magic",        "medicine",      "music theory",         "mysticism",         "networking",
            "nudity",       "opera",       "photography",  "physics",      "podcasting",    "poetry",               "politics",          "pornography",
            "psychology",   "recovery",    "religion",     "robotics",     "sailing",       "science",              "scrapbooking",      "security systems", 
            "sewing",       "sex",         "social media", "solar power",  "solarpunk",     "space travel",         "sportsmanship",     "steampunk",
            "stripping",    "survivalism", "tacos",        "tattoos",      "technology",    "time travel",          "transportation",    "witchcraft",        
            "yoga",         "zombies",     "zoology",      "zymurgy"  ]

def sub_subproc_e (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    while s.count(item) > 0:
        r  = app_numeric.arand(1, 0, len(k_event) - 1)                  ## random selection of the event type
        s = s.replace(item, k_event[r], 1)
    return (s)


## Process the current hour in 12 - hour Local(12..12) form. Start/end string data flag is a single optional
## character (').  If that character is present, then it means that we are parsing HOURS ONLY, i.e.: there
## is nothing following that and we should round to the NEAREST hour.

def sub_subproc_i (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    hh = coord.ltc.hour
    hh = get_24_to_12h(hh)
    if (len(item) == 3):
        if (item[2] == """'"""):                                        ## we use minutes to round
            if (coord.ltc.minute > 30): hh = hh + 1
    if (hh > 12): hh = hh - 12                                          ## make sure we don't overrun
    h  = app_strings.num_to_text(hh)                                    ## convert to string
    if (hh == 0): h = "midnight"
    s = s.replace(item, h)
    return (s)


## Process the (local time) minutes.  Start/end string data is unused.  For local time set
## the parameter to 'm'.  Use 'n' for GMT.

def sub_subproc_mn (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    if (item[1] == 'm'):  mm = coord.ltc.minute                         ## ltc vs utc
    else:                 mm = coord.utc.minute
    m  = app_strings.num_to_text(mm)                                    ## convert to string
    if (mm < 10):
        m = "oh " + m
    s = s.replace(item, m)
    return (s)


## Process the am/pm string (local time).  Start/end string data is unused.

def sub_subproc_p (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    if (coord.ltc.hour < 12): a = "a.m."
    else:                     a = "p.m."
    s = s.replace(item, a)
    return (s)


## Process a substitution based on the current hemisphere.  Item contains the '=northstring|southstring' substring.

def sub_subproc_s (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    i = item.index("|")
    a = item[3:i]                                                       ## init to northern choice
    if (coord.lat < 0.00): a = item[(i+1):]                             ## check based on latitude
    s = s.replace(item, a)
    return (s)


## Process a substitution based on the special string randomizer: time to | just about time to | a good time to | ...
## The "coord" parameter is unused.

def sub_subproc_t (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    a  = ""                                                             ## init substitution string
    r  = app_numeric.arand(1, 1, 100)
    if   (r < 10):  a = "time to"
    elif (r < 20):  a = "a good time to"
    elif (r < 30):  a = "just about time to"
    elif (r < 40):  a = "almost time to"
    elif (r < 50):  a = "approaching the time to"
    elif (r < 60):  a = "a time to"
    elif (r < 70):  a = "nearly time to"
    s = s.replace(item, a)
    return (s)


## Process the (local time) day of the year (1..366) (add ^ for ordinal: <y^ = 1st...366th).

def sub_subproc_y (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    doy = coord.ltc.timetuple().tm_yday                                 ## get the day of the year
    a = app_strings.num_to_text(doy, (len(item) > 2))                   ## ordinal if there are three chars in item
    s = s.replace(item, a)
    return (s)


## Process a random choice between multiple words.  Item contains the 'choice1|choice2|..|choiceN' substring.

def sub_subproc_qq (s, coord, item):
    if (s == ""): return ("")                                           ## safety check
    a = app_strings.choose_between(item[2:], '|')                       ## pick a random thing
    s = s.replace(item, a)
    return (s)
