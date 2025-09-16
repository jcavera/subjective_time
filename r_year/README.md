## Resource File format

The files for normal-priority,daily messages are designated as "r_" plus the four-digit year and are in 
plain-text format, with the line numbers corresponding to the day number in the given year. The file 
contents is formatted as follows:

    00000000001111111111222222222233333333334444444444555555555566666666667777777777888888888899999999990000000000111
    01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012
    -- A --- --- B --- -- C --- ---- D ---- -- E --- -- F --- ----- Z -------------------------------------- DATE
    ddmmyyyy;ddmmyyyyY;ddmmyyyy;kkwwttKKKbb;ddmmyyyy;ddmmyyyy;aaa;bbb;ccc;...

    26081448;28122026h;27255787;17051400013;15111948;27051743;035;638 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 02-04
    27081448;29122026h;28255787;18051400013;16111948;28051743;036;596;639;612 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 02-05
    28081448;01012027i;29255787;19051400013;17111948;29051743;037;637;640;380;433;888;932;950;479;490;409 ~~ 02-06
    29081448;02012027i;30255787;00061400013;18111948;30051743;038;566;479;490 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 02-07
    01091448;03012027i;01265787;01061400013;19111948;01061743;039;641;416;504;566 ~~~~~~~~~~~~~~~~~~~~~~~~~~ 02-08

    Bytes 00..07    A = Arabic date (via the Kuwati algorithm)
    Bytes 09..17    B = Chinese date (look up table, Y = year sign)
    Bytes 19..26    C = hebrew calendar date (look up table)
    Bytes 28..38    D = mesoamerican long count calendar date (computed)
    Bytes 40..47    E = inidan national calendar date (look up table)
    Bytes 49..56    F = coptic calendar date
    Bytes 58..103   Z = variable length, special events by 3 - digit number, separated by semicolons
    Bytes 105..109  Date field for sake of the convienence of the human editor (unused by the code)

Individual date components (A..F) are interpreted via the following functions:

    A: app_parser.message_algo_islam()
    B: app_parser.message_algo_china()
    C: app_parser.message_algo_hebrew()
    D: app_parser.message_algo_mayan()
    E: app_parser.message_algo_indian()
    F: app_parser.message_algo_coptic()

Following the date lookup information, the special events list is a set of 3-digit (zero-padded) numbers that refer
to one-based line numbers in the /data/r_macr.txt file.  In processing these, the following psudeo-coded steps are
taken:

- Extract the list of r_macr.txt line numbers for the current day
- Create an empty string as a day event placeholder
- For each line number in the list
  - Grab the corresponding line from the r_macr.txt file
  - Strip everything in the line from the first tilde ("~") character onward
  - Append a semicolon to the day event string
  - Append the stripped line to the day event string
- Once the day event string is complete, randomly select a day event from the semicolon-delimited list
- Process the selected day event for display

This process is handled by the various app_parser functions.
