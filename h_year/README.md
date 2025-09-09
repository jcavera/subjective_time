# High-priority Message file format

The files for high-priority messages are designated as "h_" plus the four-digit year and are in plain-text
format.  The file contents is formatted as follows:

    00000000001111111111222222222233333333334444444444555555555566666666667777777777888888888899999999990
    01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
    
    [02-07 1145][02-07 1215](-90.0000,-180.0000)(+90.0000,+180.0000) gauna jaya ekadashi ~~~~~~~~~~~~~~~~
    [03-25 2030][03-25 2130](-90.0000,-180.0000)(+90.0000,+180.0000) earth hour ~~~~~~~~~~~~~~~~~~~~~~~~~
    [04-06 1145][04-06 1215](-90.0000,-180.0000)(+90.0000,+180.0000) gauna kamada ekadashi ~~~~~~~~~~~~~~
    (07-06 1546)(07-06 2057)(-90.0000,-004.0000)(+90.0000,+176.0000) partial lunar eclipse ~~~~~~~~~~~~~~
    (07-08 1140)(07-08 1150)(-90.0000,-180.0000)(+90.0000,+180.0000) almost everyone is seeing the sun ~~
    [09-02 2000][09-02 2200](+40.6000,-119.0000)(+41.0000,-119.5000) time to burn ~~~~~~~~~~~~~~~~~~~~~~~

    Bytes 01..10  The starting date/time in MM-DD hhmm of the interval in which the message is valid
    Bytes 13..22  The ending date/time in MM-DD hhmm of the interval in which the message is valid

    If the interval date/time is in square braces, then the date/time is LOCAL.  Otherwise it is GMT.

    Bytes 25..42  The start of the lat/lon bounding box in which the message is valid
    Bytes 45..62  The end of the lat/lon bounding box in which the message is valid
    Bytes 65...   The message to display if both the current time and location fall within the interval

Lines are < CR >< NL > delimited, and fixed in length, with tilde characters used as null filler.  When checking
for high-priority messages, the appropriate h_ file is located based on the current year.  The lines are stepped
through and, if the time interval for the message contains the current time (local or GMT as appropriate) then
the current location is checked against the bounding box.  If the current location falls within the bounding box
then the high-priority message is displayed.

As a general rule, high-priority messages are only used for events that occur during a part of a single day (i.e.: 
in less than a 24-hour period) and are sufficiently noteworthy that it would be fun to almost always display the
message in the appropriate interval.
