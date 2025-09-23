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

    !A>62000,A<76000,M<3,h>20 under the aurora borealis ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    !M=1,d=30 happy yodel at your neighbor day ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    !Y=2026,M=10,d=24 pythagorean theorem appreciation day ~~~~~~~~~~~~~~~~~~~~~~~~

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

    _% nativity fast              _& moon                       _* since
    _, of the                     _. night                      _0 midnight
    _1 somewhere                  _2 sometime                   _3 getting
    _4 approaching                _5 in the evening             _6 at night
    _7 your                       _8 month                      _9 week
    _: the feast of               _@ festival                   _A the discovery of
    _B almost                     _C around                     _D nearly
    _E o'clock                    _F about                      _G approximately
    _H half past                  _I until                      _J before
    _K after                      _L last                       _M year
    _N years                      _O months                     _P days
    _Q hours                      _R minutes                    _S seconds
    _T right now                  _U anniversary                _V quarter
    _W in the morning             _X top of the hour            _Y bottom of the hour
    _Z in the afternoon           _[ awareness month            _] the invention of
    _` paces                      _a time to                    _b a.m.
    _c p.m.                       _d hundred hours              _e noon
    _f time for                   _g straight up                _h just after
    _i just before                _j appreciation day           _k awareness day
    _l at the start of            _m remembrance                _n the end of
    _o the beginning of           _p the birth of               _q the death of
    _r the founding of            _s first                      _t day
    _u international              _v birthday                   _w national
    _x saint                      _y the publication of         _z chocolate
    _{ in the                     _} until

As an example of macro use, the lines:

    _B seven _E _5
    _w llama _j
    the _@ of _x cedric

Would render as, respectively:

    almost seven o'clock in the evening
    national llama appreciation day
    the festival of saint cedric

Number substitution can be used for turning numbers into their text equivalent.  A number is preceeded by the number sign (#),
and when the message is displayed, that number is rendered as text.  As a case in point, the line:

    _G #5300 _N since _] the lathe

Would render as:

    approximately five thousand three hundred years since the invention of the lathe

Finally, a "less than" symbol (<) denotes a computed substitution.  These are substitutions that require an algorithm to figure
out, either because they are date/time dependant, they are location dependant, or they are otherwise too complex for a simple
look-up table to easily handle.  Allowed computed substitutions are as follows:

    <A  latitude-longitude coordinates rendered as the nearest whole number
    <B  Benedryl Cucumber's birthday (yeah, just look at the associated function)
    <C  ordinal century
    <D  day of the week
    <G  distance and/or direction from the specified GPS coordinates
    <H  current hour (24 hour format, GMT)
    <M  current month of the year
    <N  a random month of the year
    <O  random distance and/or direction
    <P  random on-playa location (for Burning Man related messages)
    <R  random number
    <S  the current season of the year
    <Y  the current year
    <Z  the name of the current timezone
    <d  the ordinal date of the month
    <e  on-playa event classification (yeah, this is a weird one too)
    <h  current hour (24 hour format, local time)
    <i  the current hour (12 hour format)
    <m  the current minutes (in local time)
    <n  the current minutes (in GMT)
    <p  the current am or pm string
    <r  random number in ordinal form
    <s  a substitution for the current hemisphere (south | north)
    <t  another randomizer: time to | just about time to | a good time to | ...
    <y  the current ordinal day of the year
    <?  make a random choice between a list of items delimited by (|)

In all cases, you can look at the associated function in the app_markup file to see how those are handled.  Many of them
stand alone (e.g.: <D always just gives the current day of the week), but a number of them have required or optional
parameters after the tag (e.g.: <R=100-1000 gives a random number between 100 and 1000).

All of these are best seen by example, so here's one of each in turn, and how it might render as a message (note that the
data for current date, time, and location is just made up):

| the line in the resource file        | could render as 
| -------                              | -------
| close to <A                          | close to one hundred seven degrees west by forty seven degrees north
| happy birthday to <B                 | happy birthday to bandicoot coloringbook
| in the <C century                    | in the twenty first century
| just a normal <D                     | just a normal tuesday
| <G=+45957,+010297 val camonica       | nine thousand two hundred miles west by northwest of val camonica
| <H hours gmt                         | fifteen hundred hours gmt
| a day in <M                          | a day in september
| don't forget her birthday in <N      | don't forget her birthday in december
| <O=100-1000 a strange portal         | five hundred twenty six kilometers south of a strange portal
| go to <P and kiss a stranger         | go to five o'clock and esplanade and kiss a stranger
| <R=20-100 minutes until they realize | forty seven minutes until they realize
| generally <S                         | generally winter
| a random day in <Y                   | a random day in two thousand twenty five
| in the timezone of <Z                | in the timezone of los angeles
| the <d of the month                  | the twenty second of the month
| time for the event about <e to start | time for the event about transhumanism to start
| <h hours local time                  | seven hundred hours local time
| close to <i o'clock                  | close to three o'clock
| <h hours <m minutes                  | twenty hundred hours fifty seven minutes
| <H hours <n minutes gmt              | thirteen hundre hours forty two minutes gmt
| nearly <i <p                         | nearly two p.m.
| their <r=5-15 anniversary            | their seventh anniversary
| happy <s=spring\|fall equinox        | happy fall equinox
| <t take a chance                     | a good time to take a chance
| the <y day of the year               | the two hundred thirtieth day of the year
| call me <?maybe\|later\|now          | call me maybe

## File formats for the r_macr.txt file
