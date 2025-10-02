# Time Zone File format

The time zone files are named as "z_" followed by a three-digit integer representing the time zone index
(which corresponds to the one-based line number in the /data/all_rgn.txt file).  All share the same format,
as follows:

    000000000011111111112222222222333333333344444444445555555555
    012345678901234567890123456789012345678901234567890123456789

    2029:+0100;01-14;+0000;02-18;+0100;12-30;+0000 ~~~~~~~~~~~~

    Bytes 00..03:  four digit year
    Bytes 05..09:  the offset in <+/->hhmm from GMT at the start of the year
    Bytes 11..15:  the MM-DD of the first changeover, occuring at 0100 local time
    Bytes 17..21:  the offset in <+/->hhmm from GMT after the first changeover
    Bytes 23..27:  the MM-DD of the second changeover, occuring at 0100 local time
    Bytes 29..33:  the offset in <+/->hhmm from GMT after the second changeover
    Bytes 35..39:  the MM-DD of the third changeover, occuring at 0100 local time
    Bytes 41..45:  the offset in <+/->hhmm from GMT after the third changeover
    Bytes 47..51:  the MM-DD of the fourth changeover, occuring at 0100 local time
    Bytes 52..57:  the offset in <+/->hhmm from GMT after the fourth changeover

Lines are < CR >< NL > delimited, and fixed in length, with tilde characters used as null filler.  Each line 
can support up to four changes from GMT to the local time.  To determine the local time, the line corresponding 
to the current year is retrieved from the file, and then the line parsed until the current date is less than 
the changeover date.  Once that is found, the most recent changeover offset is applied to the current GMT time.

A line in the file may have as few as one offset (at bytes 05..09) or as many as four offsets (ending at bytes
52..57).  Following the last offset, tilde characters ("~") are used to pad the line to the appropriate length.
The last offset given is valid through the end of the calendar year.
