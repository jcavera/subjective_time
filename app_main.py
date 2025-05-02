##  Module:         app_main
##  Description:    Primary interface to the app.
##  Contains:       Config      Config file management
##                  App         Primary application

## Note: all text data files must have ONLY utf-8 characters in them.  To test for that, do a regex
## search in notepad++ with the following parameter: [^\n-~]  Anything not in the valid UTF-8 set will
## be highlighted.

import tkinter as tk
import numpy as np
from PIL import ImageTk, Image
import sys
import os
import signal
import platform
import configparser
from pathlib import Path

import datetime
import time
import app_parser
import app_strings
import app_numeric
import app_timezones
import app_files


## ------------------------------------------------------------------------------------------------- CONSTANT DEFINITIONS
## Global valid image set.  Any image names not in this set will not be used.

imgs = set( [ 'brc', 'brd', 'car', 'chn', 'cop', 'cyb', 'd20', 'gfb', 'heb', 'hrg',  
              'ich', 'ind', 'isl', 'key', 'kim', 'lnf', 'm8b', 'map', 'mar', 'max', 
              'mrs', 'mun', 'myn', 'one', 'p01', 'p02', 'p03', 'p04', 'p05', 'p06', 
              'p07', 'p08', 'p09', 'p10', 'p11', 'pbd', 'qst', 'run', 'scp', 'tfe', 
              'wnv', 'zil', 'zod'  ] )

## ------------------------------------------------------------------------------------------------- GLOBAL VARIABLES

ltc  = datetime.datetime.now()                      ## init the times
utc  = datetime.datetime.now(datetime.UTC)

## ------------------------------------------------------------------------------------------------- CLASS - Config
## Class for managing the configuration file read/writes

class Config:
    ## Initialization routine - set up class members and read the file.
    
    def __init__ (self):
        self.lat     = 47.434765                    ## Port Orchard, Washington, USA, Earth
        self.lon     = -122.668934
        self.tz      = 134                          ## time zone: north america/los angeles
        self.tz_off  = -700                         ## offset: PDT = -700, PST = -800
        self.debug   = False                        ## debug flag (used for setting sleepytime and other stuff)
        self.playa   = True                         ## display on-playa messages
        self.has_gps = False                        ## flag - GPS module is present in the system
        self.img_dir = app_files.dir_images         ## directory for image files
        
        self.l_chars = 56                           ## number of characters in a single line
        self.l_lines = 6                            ## maximum number of lines
        self.l_start = 222.5                        ## starting and ending angular position of a line
        self.l_end   = -47.5
        self.l_step  = 65                           ## amount to decrease radius for each line
        
        self.t_font  = "Courier New"                ## font for the line text
        self.t_size  = 38                           ## initial (outer ring) font size
        self.t_sstep = 5                            ## amount to decrease font size for each line
        self.t_style = 'bold'                       ## style for the display font
        self.t_color = "#4f4"                       ## color for the line text
        
        self.sec    = 'CONFIG'                      ## section name
        self.f_cfg  = app_files.file_config         ## configuration file location
        self.p      = configparser.ConfigParser()   ## set up a configuration parser
        f_path = Path(self.f_cfg)                   ## check that the configuration file exists
        exists = f_path.is_file()
        if (exists):    self.read()                 ## read the file to the globals if it does
        else:           self.write()                ## make the file with the defaults if it doesn't
    
    ## Read the configuration file and save off the values to the globals.
    
    def read (self):
        try:
            self.p.read(self.f_cfg)                 ## attempt to read the config file
        except:
            self.write()                            ## if an exception occured, try a write
            return                                  ## and bail out
        
        self.lat     = float(self.p[self.sec]['lat'])           ## read the default lat/lon
        self.lon     = float(self.p[self.sec]['lon'])
        self.tz      = int(self.p[self.sec]['tz'])              ## read the timezone and offset
        self.tz_off  = int(self.p[self.sec]['tz_off'])
        self.debug   = ('True' == self.p[self.sec]['debug'])    ## read the debug flag
        self.playa   = ('True' == self.p[self.sec]['playa'])    ## on playa flag (true | false)
        self.has_gps = ('True' == self.p[self.sec]['gps'])      ## gps module installed
        self.img_dir = self.p[self.sec]['img_dir']              ## image directory
        
        self.l_chars = int(self.p[self.sec]['l_chars'])         ## read character settings
        self.l_lines = int(self.p[self.sec]['l_lines'])
        self.l_start = float(self.p[self.sec]['l_start'])
        self.l_end   = float(self.p[self.sec]['l_end'])
        self.l_step  = int(self.p[self.sec]['l_step'])
        
        self.t_font  = self.p[self.sec]['t_font']               ## read font settings
        self.t_size  = int(self.p[self.sec]['t_size'])
        self.t_sstep = int(self.p[self.sec]['t_sstep'])
        self.t_style = self.p[self.sec]['t_style']
        self.t_color = self.p[self.sec]['t_color']
    
    ## Write the configuration file and save the current global values to it.
    
    def write (self):
        self.p[self.sec] = { 'lat':      self.lat,       'lon':      self.lon,       'tz':       self.tz,
                             'tz_off':   self.tz_off,    'debug':    self.debug,     'playa':    self.playa, 
                             'gps':      self.has_gps,   'img_dir':  self.img_dir,   'l_chars':  self.l_chars,
                             'l_lines':  self.l_lines,   'l_start':  self.l_start,   'l_end':    self.l_end, 
                             'l_step':   self.l_step,    't_font':   self.t_font,    't_size':   self.t_size, 
                             't_sstep':  self.t_sstep,   't_style':  self.t_style,   't_color':  self.t_color
        }
        cfgfile = open(self.f_cfg, 'w')
        self.p.write(cfgfile)
        cfgfile.close()
    

## ------------------------------------------------------------------------------------------------- CLASS - App
## Primary class for running the app

class App ():
    ## Perform the intialization of all app structures, systems and UI elements.  This includes the
    ## parser, the coordinate system, the config file, and the tkinter UI. Everything is dynamic to
    ## the size of the current screen.
    
    def __init__ (self):
        self.p          = app_parser.Parser()       ## make a new parser instance
        self.cfg        = Config()                  ## read the configuration file
        self.i          = 0                         ## iteration counter
        self.c          = app_parser.coordinate(ltc, utc, self.cfg.lat, self.cfg.lon, self.cfg.tz, self.cfg.tz_off)
        
        angle_start     = np.radians(self.cfg.l_start)      ## beginning angular position of the line
        angle_end       = np.radians(self.cfg.l_end)        ## ending angular position of the line
        
        self.root = tk.Tk()                                 ## set up the root window
        self.root.attributes('-fullscreen', True)           ##      use the full screen
        self.root.config(cursor="none")                     ##      get rid of the mouse cursor
        
        ## install handlers for events
        ## TODO: figure out how to read a button to shut down the system then add a handler for it
        
        self.root.bind("<Escape>", self.quit_me)            ## bind the quit method to the escape key
        signal.signal(signal.SIGTERM, self.quit_me)         ## add signal handlers for power-down
        
        self.w = self.root.winfo_screenwidth()      ## grab the screen width and height
        self.h = self.root.winfo_screenheight()
        center_x    = self.w / 2                    ## grab the center co-ordinates and compute radius
        center_y    = self.h / 2
        radius      = min(center_x, center_y) - 55
        
        ## set up the canvas and tag it to the window
        
        self.canvas = tk.Canvas(self.root, height=self.h, width=self.w, bg='black', highlightthickness=0)
        self.canvas.pack()
        self.imgB   = ImageTk.PhotoImage(Image.open(self.cfg.img_dir + "brd.jpg"))
        self.bgimg  = self.canvas.create_image(center_x, center_y, image=self.imgB, anchor='center', state='hidden')
        
        ## create each text box (one per character) as an array
        
        self.textboxes = [ [], [], [], [], [], [] ]
        angle_inc = (abs(angle_end - angle_start)) / self.cfg.l_chars
        for i in range(self.cfg.l_chars + 1):
            cangle = angle_start - (i * angle_inc)
            aangle = (np.degrees(cangle) - 90)
            for j in range(self.cfg.l_lines):
                textX = center_x + ((radius - (j * self.cfg.l_step)) * np.cos(cangle))
                textY = center_y - ((radius - (j * self.cfg.l_step)) * np.sin(cangle))
                next_font = (self.cfg.t_font, (self.cfg.t_size - (j * self.cfg.t_sstep)), self.cfg.t_style)
                self.textboxes[j].append(self.canvas.create_text(textX, textY, font=next_font, fill=self.cfg.t_color, angle=aangle ))
        clock_font = (self.cfg.t_font, self.cfg.t_size, self.cfg.t_style)
        self.clock_txt = self.canvas.create_text(center_x, self.h - 150, anchor="center", font=clock_font, fill="#040")
        
        self.update_me()                            ## update the UI elements
        self.root.mainloop()                        ## then enter the primary loop
    
    ## Do whatever needs to be done on application quit.  Including updating the config file if needed.
    
    def quit_me(self, event):
        self.cfg.write()
##      if (platform.system() == "Linux"): os.system("shutdown now -h")     ## uncomment when the shutdown button handler is enabled
        sys.exit()
    
    ## Update the background image with the given file name.  If no file name is specified, then hide
    ## the background image UI element.
    
    def update_background(self, fname):
        if (fname == ""):
            self.canvas.itemconfig(self.bgimg, state='hidden')                  ## hide the image if the name is blank
        else:
            self.imgB = ImageTk.PhotoImage(Image.open(fname))                   ## otherwise get the image and show it
            self.canvas.itemconfig(self.bgimg, image=self.imgB, state='normal')
    
    ## Update the contents of the string lines (concentric circles).  First, split the incoming string
    ## to individual lines as needed.  Then erase the previous elements by setting each element text
    ## to a nullstring.  Then add the new text by updating each element on a character-by-character
    ## basis.  If there are any lines that are less than the maximum single line length, then pad with
    ## spaces to make everything more-or-less lined up.
    
    def update_strings(self, aa):
        bb = app_strings.split_me(aa, self.cfg.l_chars)                     ## split the string in to lines as needed
        for j in range (0, self.cfg.l_lines):                               ## erase the previous string
            for i in range (0, self.cfg.l_chars):
                self.canvas.itemconfig(self.textboxes[j][i], text="")
        for j in range(min(self.cfg.l_lines, len(bb))):                     ## display the new string
            l = len(bb[j])
            if (l > 1) and (l < (self.cfg.l_chars - 1)):                    ## justify short lines as needed
                bb[j] = (" " * int((self.cfg.l_chars - l) / 2)) + bb[j]
            l = len(bb[j])
            if (l > 1):                                                     ## write line-by-line
                for i in range(min(self.cfg.l_chars, l)):
                    self.canvas.itemconfig(self.textboxes[j][i], text=bb[j][i])
    
    ## Perform whatever periodic maintenance may be needed.  This includes things like updating the GPS
    ## location and re-checking the timezone.  It only occurs once every hundred updates of the clock.  In
    ## seven second debug mode, this means once every 11 minutes or so.  In random sleepytime mode (which
    ## is nominally every 2.5 minutes) this is once every 4-ish hours (0:25 - 8:20).
    
    def periodic (self):
        alat = 0.000                                                            ## local lat/lon to try
        alon = 0.000
        atz  = 0                                                                ## local timezone to try
        ## ------------------ attempt to get lat, lon, utc from gps (if self.c.has_gps == True)
        ## ------------------ attempt to get timezone from lat, lon
        ## set tz to 'brc' if within the boundaries of black rock city region: 40.750, -118.900, 41.150, -119.450
        if ((alat > 40.750) and (alat < 41.150) and (alon > -119.450) and (alon < -118.900)): atz = 452
                
        ## ------------------ update the offset from utc to ltc
        ## ------------------ update the coordinate information
        self.i = 0                                                              ## reset the counter
        return (0)
    
    ## Update the current UI elements.  First, grab the new coordinate elements (LTC, UTC) and use those
    ## to fetch the next string to display.  Format the attribution text as needed, and grab the reference
    ## image if valid.  Use those three items to update the UI elements and then go to sleep for the next
    ## interval.
    
    def update_me (self):
        if ((self.i % 100) == 0): self.periodic()                               ## perform periodic updates
        self.i     = self.i + 1                                                 ## increment the counter
        self.c.ltc = datetime.datetime.now()                                    ## update the current time
        self.c.utc = datetime.datetime.now(datetime.UTC)
        on_playa   = (self.cfg.playa) or (self.c.tz == 452)
        a = self.p.fetch(self.c, on_playa)                                      ## fetch the next message
        
        img = a.bg_img                                                          ## set the background image
        if (img in imgs):
            self.update_background(self.cfg.img_dir + img + ".jpg")
        else:
            self.update_background("")
        att = "     "                                                           ## format the attribution line
        if (a.attrib > 0): att = "{0:05}".format(a.attrib)
        if (img == 'qst'): att = "quest"
        now = "[ " + att + " ]"
        
        self.canvas.itemconfig(self.clock_txt, text=now)                        ## update the attribution string
        
        #### debug strings - log every message with a date/time stamp
        sa = img
        if (sa == ""): sa = "   "
        print ('{date:%Y-%m-%d %H:%M:%S}'.format(date=datetime.datetime.now()) + " [" + att + "][" + sa + "] " + a.message)
        
        self.update_strings(a.message)                                          ## update the message string
        sleepytime = app_numeric.roll_dice("3d20") * 5000                       ## random sleepytime = 0:15 - 5:00 (nominally 2.5 minutes)
        if (self.cfg.debug): sleepytime = 8000                                  ## debug sleepytime = 8 seconds
        self.root.after(sleepytime, self.update_me)                             ## set the time for the next update
        


