## Module:      app_files
## Description: Functions for doing things with files (duh).
## Contains:    file_read_uint          Read the next uint32_t from a file
##              file_read_line          Read a single line from a text file (one-based)
##              file_get_size           Fetch the on-disk size of a file
##              file_get_lines          Fetch the number of lines in the file
##              file_read_random_line   Just what it says on the tin

import os
import struct
import app_numeric

## ------------------------------------------------------------------------------------------------- CONSTANT DEFINITIONS
##      file         line len  num lines
## ---------------- ---------  ---------
##  all_rgn.txt         54 +2    ???? (indexed directly based on the time zone number)
##  config.txt          40 +2    ???? (hard-coded index)
##  r_anys.txt         134 +2    ???? (counted at power-up and stored as a static variable: count = file size / line len)
##  r_macr.txt         134 +2    ???? (not counted but directly accessed via the @ line-number macro)
##  r_time.txt         134 +2     288 (this is based on ((hour * 12) + (minute / 12)))
##  h_20xx.txt         101 +2    ???? (all lines are stepped through when needed and lf-cr is used as a break)
##  r_20xx.txt         110 +2     365 (or 366 for leap years, equal to the days in the year
##  z_xxx.txt           58 +2      77 (indexed directly based on the current year-2023, up to the year 2100)
##  k_macro.txt         25 +2    ???? (not counted but directly accessed in code)
## Note: line lengths are increased by two to account for line-feeds and carriage returns.

k_LEN_ALL_RG =  56      ## file - all_rgn.txt
k_LEN_CONFIG =  42      ## file - config.txt
k_LEN_R_ANYS = 136      ## file - r_anys.txt (also works for r_brc.txt and r_cond.txt)
k_LEN_R_MACR = 136      ## file - r_macr.txt
k_LEN_R_TIME = 136      ## file - r_time.txt
k_LEN_H_20xx = 103      ## file - h_<current year>.txt
k_LEN_R_20xx = 112      ## file - r_<current year>.txt
k_LEN_Z_xxxx =  60      ## file - z_<current timezone>.txt
k_LEN_K_MACR =  27      ## file - k_macro.txt

## File and directory locations set up as environment variables

dir_top         = ""                                ## top level directory relative to this fileyt

dir_images      = dir_top + "image_1920_45/"        ## directory - default for image files (on playa use "image_1920_45")
dir_data        = dir_top + "data/"                 ## directory - data files
dir_h_year      = dir_top + "h_year/"               ## directory - high-priority daily event files by year
dir_r_year      = dir_top + "r_year/"               ## directory - normal daily event files by year
dir_z_time      = dir_top + "z_timezone/"           ## directory - time zone data by region id

file_attrib     = dir_data + "attrib.txt"           ## file - system readme and attributions
file_config     = dir_data + "config.ini"           ## file - configuration
file_all_rgn    = dir_data + "all_rgn.txt"          ## file - time zone region information
file_tz_index   = dir_data + "all_tz.idx"           ## file - time zone index to the map
file_tz_map     = dir_data + "all_tz.map"           ## file - time zone compressed map

file_macro      = dir_data + "r_macr.txt"           ## file - macro definitions for daily events
file_time       = dir_data + "r_time.txt"           ## file - lines for specific times of day
file_brc        = dir_data + "r_brc.txt"            ## file - lines for use on the playa
file_cond       = dir_data + "r_cond.txt"           ## file - lines with only conditional statements
file_any        = dir_data + "r_anys.txt"           ## file - lines that are valid for any time


## ------------------------------------------------------------------------------------------------- FUNCTIONS

## Read four bytes and then assemble in big-endian order to a u32.

def file_read_uint (fin):
    r = struct.unpack('>i', fin.read(4))
    return (r[0])


## Read a single line from a text file, assuming that every line is the same length as specified by the
## linelen parameter.  It is assumed that all lines are delimited by [CR][LF] characters and that those
## two characters are not to be a part of the returned data.  It is also specified that the line number
## parameter is one-based (not zero-based).   File line lengths common to this application are given as
## constants at the start of this file.

def file_read_line (fname, linenum, linelen):
    f = open(fname, "r")                        ## open the file and skip to the needed line
    f.seek((linenum - 1) * linelen)
    s = f.read(linelen - 2)                     ## read the line then close the file
    f.close()
    return (s)
    

## Fetch the on-disk size of a file.

def file_get_size (fname):
    f = open(fname, 'r')                        ## open the file as read-only
    f.seek(0, 2)                                ## move to the end of file
    stop = f.tell()                             ## get the byte offset
    f.close()                                   ## close the file
    return (stop)
 
 
## Fetch the size of the files as a number of lines, assuming that every line in the file has the
## same length.
 
def file_get_lines (fname, linelen):
    a = file_get_size(fname)
    return (int(a / linelen))


## Read a single RANDOM line from a text file, assuming that every line is the same length as specified
## by the linelen parameter. It is assumed that all lines are delimited by [CR][LF] characters and that
## those two characters are not to be a part of the returned data. File line lengths common to this app 
## are given as constants at the start of this file.

def file_read_random_line (fname, linelen = k_LEN_R_ANYS):
    f = open(fname, 'r')                        ## open the file as read-only
    f.seek(0, 2)                                ## move to the end of file
    stop = f.tell()                             ## get the byte offset
    lines = int(stop / linelen)                 ## compute the number of lines
    
    r = app_numeric.arand(2, 0, (lines - 1))    ## pick out a random line
    f.seek(r * linelen)                         ## jump to that line
    s = f.read(linelen - 2)                     ## read the line then close the file and return the line
    f.close()
    return (s)
    

