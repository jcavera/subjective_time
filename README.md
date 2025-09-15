# Subjective Time

This is the code for the Subjective Time art project.  Originally brought to the playa in 2009, then ported to Pebble in 2012.  Then
shelved for a good eight years before being revived, completely re-thought and re-written, and then brought BACK to Burning Man in
2025.  The goal for this project (as of 2025-09) is to come up with an implementation for ESP32-based open-source smart watches.

The python code is rough (this was my 2020, I-need-to-learn-python project) but should be sufficiently documented.  For any future
implementation, I want to use the same common set of data files.  Do NOT mess with the format of the data files.  They're pretty
sensitive to modification.

For a better explanation of the project in general, refer to the /data/attrib.txt file.  This serves as an embedded readme file that
is to travel with the code and provide an expanation of the references for the called-out lines in the data files.  Individual sub-
directories may have their own readmes in order to explain the file formats.  Also of course, read the code comments.

And if you want to contribute to the code or data, please for the love of all that is holy, make your own fuckin' branch.  Thanks!

## General rules for all data files

- Only ASCII encoding is allowed.  The system cannot render UTF-anything characters.  Sorry/not-sorry.
- All messages are to be displayed using ONLY lowercase characters (the silly exception: CAPSLOCK DAY).
- Only the following punctuation is allowed in messages: "...", "?", "!", "-"
- Use the forward-slash ("/") to force a line-break in a message.
- If punctuation is at the end of a line, use a force-break ("/") after it.
- Note the line length limitations of each file.  Use a tilde ("~") as a null character to pad to that length.
- Follow all of the rules in the READMEs in each of the data file directories.
