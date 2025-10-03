# Subjective Time

This is the code for the Subjective Time art project.  Originally brought to the playa in 2009, then ported to Pebble in 2012.  Then
shelved for a good eight years before being revived, completely re-thought and re-written, and then brought BACK to Burning Man in
2025.  The goal for this project (as of 2025-09) is to come up with an implementation for ESP32-based open-source smart watches.

The python code is rough (this was my 2020, I-need-to-learn-python project) but should be sufficiently documented.  For any future
implementation, I want to use the same common set of data files.  Do NOT mess with the format of the data files.  They're pretty
sensitive to modification, since everything's adderessed by counting bytes.

For a better explanation of the project in general, refer to the /data/attrib.txt file.  This serves as an embedded readme file that
is to travel with the code and provide an expanation of the references for the called-out lines in the data files.  Individual sub-
directories may have their own readmes in order to explain the file formats.  Also of course, read the code comments.

And if you want to contribute to the code or data, please for the love of all that is holy, make your own fuckin' branch.  Thanks!

## General rules for all data files

- Only ASCII encoding is allowed.  The system cannot render UTF-anything characters.  Sorry/not-sorry.
- All messages are to be displayed using ONLY lowercase characters (the silly exception: CAPSLOCK DAY).
- Only the following punctuation is allowed in messages: "?", "!", "-", "'", "..." (3 periods, not a single-character elipsis).
- Use the forward-slash ("/") to force a line-break in a message.
- If punctuation is at the end of a line, use a space and force-break (" /") after it.  Even if it's the last thing in the string.
- Note the line length limitations of each file.  Use a tilde ("~") as a null character to pad to that length.
- Follow all of the rules in the READMEs in each of the data file directories.

## Python code construction and use

This is python to this is an easy one.  First you'll need a python 3.10 (or later) environment on whatever machine you use.  I've
tested this on Windows 10/11 and Ubuntu 24.x.  It should be fine anywhere since there's nothing particularly platform dependant
in the code.  The potential exception to what I just said: I do make use of Tkinter for graphics and that may not be appropriate
if you're wanting to run this in an embedded system.  All of the graphics calls are isolated to the App class in app_main.  So
that said, fter you have a python environment installed...

- Download the entire project and uncompress it to wherever you want it.
- Make sure that the directory structure is just like it appears in this repository.
- Make sure that the values in the init file (/data/config.ini) look good to you, particularly:
  - lat = 40.78611 (this should be set to your current latitude)
  - lon = -119.204595 (and this one to your current longitude)
  - tz = 134 (the one-based line number of your current timezone in the /data/all_rgn.txt file)
  - tz_off = -700 (the current time offset from GMT in <+/->HHMM format)
  - debug = True (if true, then the message changes ever 10 seconds for debugging)
  - playa = True (if true, then Burning Man messages are displayed)
  - img_dir = image_1920_45/ (pick out the directory that matches your screen)
- To start the clock, go to a console in the project directory and type "python __init.py__".
- There will likely be some errors and some missing libraries, so fix those.
- For Windows, there's an auto-run batch file.  To have this run on startup, put a link to that file in the startup directory.

That's about it.  If you are passingly familiar with python, it should be straightforward.  If not... then do that first I guess?
