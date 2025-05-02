## Module:      app_strings
## Description: Global string functions specific to the application.
## Contains:    get_reference_num       return any reference number at the end of a line (if there is one)
##              get_reference_image     return any reference image at the end of a line (if there is one)
##              strip_eol               strip off all of the end of line (~) characters and return what's left
##              wordlen                 return the length of a given word
##              split_me                split a long string among multiple lines given a maximum line length
##              num_to_text             convert a number (range: 0 to 999,999) to a text representation
##              time_diff_str           compute the time (in day fraction) before/since
##              choose_between          choose between multiple text selection, given the delimiter character

import re
import app_numeric

## ------------------------------------------------------------------------------------------------- FUNCTIONS

## From the input string, find any reference number embedded in it or return zero if not found.  Reference
## numbers are four digits (with leading zeros as needed) and are always the last thing on a line prior to
## either the end of line or the [CR][LF] characters.

def get_reference_num (a):
	r = "[ ][0-9]{4}$"              ## regex: space + 4 digits at the end of the line
	try:
		s = re.findall(r, a)[0]     ## try to find them and if they exist
		i = int(s)                  ## extract the reference number
	except:
		i = 0                       ## otherwise null out the reference number
	return (i)


## From the input string, find any reference image embedded in it or return an empty string if not found.
## The reference image is a three character (A-Z)(a-z)(0-9) image file name, preceeded by a '$' character
## and is either the last thing in the line or is followed by the reference number.

def get_reference_image (a):
    s = ""
    i = a.find('$')                 ## find the position of the dollar sign character
    if (i >= 0):
        s = a[(i+1):(i+4)]          ## if it exists extract the following three characters
    return (s)


## From the imput string, strip off everything from the tilde character, including any leading or
## trailing spaces, and return what's left.

def strip_eol (a):    
    i = a.find('~')                 ## find the location of the tilde character
    if (i >= 0):
        a = a[:i]                   ## if there is one, get rid of everything from it onward
    return a.strip()                ## strip off leading and trailing spaces and return


## Global function to determine the length of a word given that word delimiters can be a space
## character, a newline character, a carriage return character, or a forward slash.

def wordlen (a):
    i = 0
    j = len(a)
    while ((i < j) and (a[i] != ' ') and (a[i] != '\n') and (a[i] != '\r') and (a[i] != '/')):
        i = i + 1
    return i


## Global function to split a long line among multiple lines.  The maximum length of the set
## of lines is given by the "breakat" parameter, with a default of 56 characters per line. A
## safety check is done to make sure that the incoming string is at least the same size as a
## single line.

def split_me (s_in, breakat = 56):
    a = [ "test" ]
    a.clear()
    for s in s_in.split("/"):
        w = 0 
        l = []
        for d in s.split():
            if ((w + len(d) + 1) <= breakat):
                l.append(d)
                w += len(d) + 1 
            else:
                a.append(" ".join(l))
                l = [d] 
                w = len(d)
        if (len(l)):
            a.append(" ".join(l))
    return (a)
    


## Convert a number to a string, either ordinal or normal. The function returns null if it is not possible to do so.
## Note that the destination string must be large enough to hold the generated word(s).  The range of the inputs are
## positive integers from one to either max(int) or 999,999; whichever is smaller.   The "is_ordinal" parameter used
## to choose between the normal or ordinal forms of the string.  It defaults to "False".
##
## For the purpose of planning string lengths, the longest string that can be built by this function is:
##      seven hundred seventy seven thousand seven hundred seventy seventh
## which is 66 characters in length (67 counting the end-of-string null).

## The following global arrays as uses as constants for the conversion process, but are kept outside of the function
## so that they can be reused as other string constants if needed.

k_Ones  = [ "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten" ]
k_Teen 	= [ "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen" ]
k_Tens 	= [ "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety" ]
k_Pows 	= [ "hundred", "thousand" ]

k_Ords 	= [ "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth" ]
k_TOrd 	= [ "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "ninteenth" ]
k_TenO 	= [ "twentieth", "thirtieth", "fortieth", "fiftieth", "sixtieth", "seventieth", "eightieth", "nintieth" ]
k_PowO 	= [ "hundredth", "thousandth" ]

def num_to_text (anum, is_ordinal = False):
    snum = ""
    i = False
    
    if ((anum > 999999) or (anum < 0)):         ## trap out-of-range errors
        return "oor"
    if (anum == 0):                             ## trap zero case
        if (is_ordinal):
            return ("zeroth")
        else:
            return ("zero")
    
    if (anum >= 100000):                        ## for numbers larger than 99,999
        b = int(anum / 100000)
        snum = k_Ones[b - 1] + ' ' + k_Pows[0]
        anum = anum - (b * 100000)
        i = True
        
    if (anum >= 20000):                         ## for remainders larger than 19,999
        b = int(anum / 10000)
        if (i):
            snum = snum + ' '
        snum = snum + k_Tens[b - 2]
        anum = anum - (b * 10000)
        i = True
    
    if (anum >= 10000):                         ## for remainders larger than 9,999
        b = int(anum / 1000)
        if (i):
            snum = snum + ' '
        snum = snum + k_Teen[b - 10]
        anum = anum - (b * 1000)
        i = True
    
    if (anum >= 1000):                          ## for remainders larger than 999
        b = int(anum / 1000)
        if (i):
            snum = snum + ' '
        snum = snum + k_Ones[b - 1]
        anum = anum - (b * 1000)
        i = True
        
    if (i):                                     ## if we've completed a string up to here
        if ((anum == 0) and (is_ordinal)):
            snum = snum + ' ' + k_PowO[1]
            return (snum)
        snum = snum + ' ' + k_Pows[1]
        
    if (anum >= 100):                           ## for remainders larger than 99
        b = int(anum / 100)
        if (i):
            snum = snum + ' '
        snum = snum + k_Ones[b - 1]
        anum = anum - (b * 100)
        if ((anum == 0) and (is_ordinal)):      ## if we stop here and it's an ordinal
            snum = snum + ' ' + k_PowO[0]
            return (snum)
        snum = snum + ' ' + k_Pows[0]
        i = True
        
    if (anum >= 20):                            ## for remainders larger than 19
        b = int(anum / 10)
        anum = anum - (b * 10)
        if ((anum == 0) and (is_ordinal)):
            snum = snum + ' ' + k_TenO[b - 2]
            return (snum)
        if (i):
            snum = snum + ' '
        snum = snum + k_Tens[b - 2]
        i = True
        
    if (anum >= 10):                            ## for remainders larger than 9
        if (is_ordinal):
            if (i):
                snum = snum + ' '
            snum = snum + k_TOrd[int(anum - 10)]
        else:
            if (i):
                snum = snum + ' '
            snum = snum + k_Teen[int(anum - 10)]
        return (snum)
    
    if (anum >= 1):                             ## for the ones digit if any
        if (is_ordinal):
            if (i):
                snum = snum + ' '
            snum = snum + k_Ords[int(anum - 1)]
        else:
            if (i):
                snum = snum + ' '
            snum = snum + k_Ones[int(anum - 1)]
    snum = snum.strip()
    return (snum)


## Compute the time (in day fraction) before/since and write the string to part.  Positive times are "before" or "until", nagative times
## are "after" or "since".  For instance, the input 0.01 should render as "fifteen minutes before".  The input value -0.06 should render
## as "one hour thirty minutes after".  If the input is exactly zero, only the event string will be returned.
## 
## Meaning if the current time is LESS than (i.e.: before) the time of the thing that you're interested in, the input parameter is gonna
## be POSITIVE and it should render as BEFORE.  If the current time is GREATER than (i.e.: after) the time of the thing that you are
## interested in, the input parameter is going to be NEGATIVE and it should render as AFTER.

def time_diff_str (d, event):
    m = 0                                                   ## mode (0 = nulll, 1 = before, 2 = after)
    if (d == 0.0): 
        return (event)                                      ## return the event string on a zero input
    if (d < 0.0):                                           ## if time is negative, set state to after
        d = d * (-1.0)
        m = 2
    else: 
        m = 1                                               ## otherwise set mode to before (m = 1)
    hh = int(24 * d)                                        ## find number of hours and minutes
    mm = int(1440 * d) - (hh * 60)
    s  = ""
    if (hh == 1):                                           ## for one hour exactly
        s = "one hour "
    if (hh > 1):                                            ## for multiple hours
        s = num_to_text(hh, False) + " hours "              ##     convert hours to text
    if (mm == 1):                                           ## for one minute exactly
        s = s + "one minute "
    if (mm > 1):                                            ## for multiple minutes
        s = s + num_to_text(mm, False) + " minutes "        ##     convert minutes to text
    
    if ((m == 1) and (mm < 30)): s = s + "until "           ## add "until"
    if ((m == 1) and (mm > 29)): s = s + "before "          ## add "before"
    if ((m == 2) and (mm < 30)): s = s + "after "           ## add "after"
    if ((m == 2) and (mm > 29)): s = s + "since "           ## add "since"
    return (s + event)


## Randomly choose between multiple text selection, given the delimiter character.

def choose_between (a, delim):
    if (a == ""): return ("")                                   ## safety check
    alist = a.split(delim)                                      ## split to a list along the delimiter
    alist = [x for x in alist if x.strip()]                     ## remove empty strings
    s     = alist[ app_numeric.arand(1, 0, len(alist) - 1) ]    ## return a random one
    return (s.strip())

