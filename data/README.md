## File formats for the resource files

Resources are the files: r_anys.txt, r_brc.txt, and r_cond.txt.  The first (r_anys) consists of messages
that are (in general) always valid to display.  Some conditional statements apply, but those conditions
are broad (more than a single day in a year).

The second (r_brc) are meesages that are in some way related to Burning Man and are only shown when the
on-playa conditions are met.  The third (r_cond) consists entirely of conditional statements that are
purposefully narrow (e.g.: limited to a single day, a single location, a precice time, etc.).

All of the resource files are line-length limited to 134 characters, plus a carriage return and newline
(totaling 136 bytes per line).  All use a tilde (~) character to fill the length and indicate the end of
the line message content.  Lines may have two (optional) endings.  If the line end contains a dollar sign
($) followed by three characters, then those characters are to be used as a background image when the
message is displayed.  If the line ends with a four-digit (leading zero padded) number, then that number
indicates a reference in the attribution file (attrib.txt).  An attribution (if it exists) must be at the
end of the line, follwing an image (if that exists).  An example of this is the line:

    0000000000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999000000000011111111112222222222333333
    0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345

    a still more glorious song awaits ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ $pbd 0307

If the line begins with an exclamation point (!), then the line is one that is conditionally displayed,
with the conditions listed sequentially and comma-delimited, after the exclamation point.  All conditions
are AND-ed together such that all have to match in order to display the line.  Conditional tags are as
follows:

    A   Geographic lAtitude in fractional degrees to three decimal places (ex: 33204)
    D   day of week (1=Sunday..7=Saturday)
    H   24-hour GMT clock (0..23)
    I   12-hour GMT clock (1..12)
    M   month (1..12)
    O   Geographic lOngitude in fractional degrees to three decimal places (ex: -117418)
    T   24-hour time in GMT in HHmm format (0000..2359)
    Y   4-digit year
    Z   one-based time zone index
    d   date (1..31)
    h   24-hour local clock (0..23)
    i   12-hour local clock (1..12)
    m   minutes (0..59)
    s   seconds (0..59)
    t   24-hour local time in hhmm format (0000..2359)
    y   day of the year (1..366)
    z   season (spring = 1, summer = 2, autumn = 3, winter = 4)

Condition operators supported are limited to "equal to" (=), "greater than" (>), and "less than" (<).  Some
examples of a conditional lines are (from the r_cond file):

    !A>62000,A<76000,M<3,h>20 under the aurora borealis ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    !M=1,d=30 happy yodel at your neighbor day ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    !Y=2026,M=10,d=24 pythagorean theorem appreciation day ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the first example, the message is only displayed if the clock is currently between +62.000 and +76.000 degrees latitude, if the month
is less than three (January or February), and if the hour is greater than 20 (8 pm) local time.  In the second example, the message is
only displayed if the month is one (January) and the date is the 30th.  In the third, the message is only displayed if the year is 2026,
the month is ten (October) and the date is the 24th.

Lines in the resource files may contain year subsitutions.  These are computed based on the current year and the year given in the
subsitution string, in parentheses.  There are three possible computations for year substitution:
```
   (a-yyyy) Substitute the number of years since the year "yyyy" C.E.
   (b-yyyy) Substitute the number of years since the year "yyyy" B.C.E
   (o-yyyy) Substitute the ordinal number of years since the year "yyyy" C.E.
```
As an example of each (assuming that you're reading this in 2025), these messages:

    (a-2001) the first wikipedia edit
    (b-27) the founding of the roman empire
    the (o-2015) anniversary of when they first met

Would render as:

    twenty four years since the first wikipedia edit
    two thousand fifty one years since the founding of the roman empire
    the tenth anniversary of when they first met

Lines in the resource files may contain macro substitutions in order to compress the data just a little.  Note that I realize that, in
this project, I use the term "macro" a bit inconsistantly.  For this particular use, I do not mean "referencing the r_macr.txt file".
That's a different thing entirely.  Rather I mean that a two-character string (an underscore followed by another character) can be
replaced by a longer string.  Allowed substitutions are as follows:


