#include <stdint.h>
#include <types.h>

#define k_MAX 256

typedef struct {                // specification for a single file (size = 20 B)
    uint8_t     isDir;          // 1 if directory, 0 if file
    uint8_t     line_s;         // size of a single line (number of characters)
    uint16_t    file_s;         // number of lines in the file
    char        name[16];       // file name or path (if directory)
} file_spec, *file_spec_ptr;

typedef struct {                // specifications for all files and directories used (size = 320 B)
    file_spec   d_image;        // 00 dir  - default for image files
    file_spec   d_data;         // 01 dir  - data files
    file_spec   d_hyear;        // 02 dir  - high-priority daily event files by year
    file_spec   d_ryear;        // 03 dir  - normal daily event files by year
    file_spec   d_tzone;        // 04 dir  - time zone data by region id
    file_spec   attrib;         // 05 file - system readme and attributions
    file_spec   config;         // 06 file - configuration
    file_spec   tz_rgn;         // 07 file - time zone region information
    file_spec   tz_idx;         // 08 file - time zone index to the map
    file_spec   tz_map;         // 09 file - time zone compressed map
    file_spec   macros;         // 10 file - macro definitions for daily events
    file_spec   time;           // 11 file - lines for specific times of day
    file_spec   brc;            // 12 file - lines for use on the playa
    file_spec   cond;           // 13 file - lines with only conditional statements
    file_spec   any;            // 14 file - lines that are valid for any time
    file_spec   str;            // 15 file - string constants and macros indexed by line
} file_list, *file_list_ptr;

typedef struct {                // configuration as stored in the config file (size = 52 B)
    float       lat;            // f: last known latitude
    float       lon;            // f: last known longitude
    uint16_t    tz;             // u: last known timezone index
    int16_t     tz_off;         // i: last known timezone offset (hhmm)
    uint8_t     debug;          // b: flag - start in debug mode (update 10 sec)
    uint8_t     playa;          // b: flag - show on-playa messages
    uint8_t     use_gps;        // b: flag - use gps timing/position
    uint8_t     use_day;        // b: flag - use daytime display mode
    uint8_t     use_lux;        // b: flag - use light sensor for day/night mode
    uint8_t     use_mag;        // b: flag - use magnetic sensor for heading
    uint8_t     use_ink;        // b: flag - display is an e-ink type (b&w and/or unlit)
    uint8_t     line_c;         // u: number of chars in a single line
    uint8_t     line_n;         // u: number of message lines to display
    float       arc_s;          // f: degree location of message arc start
    float       arc_e;          // f: degree location of message arc end
    uint16_t    arc_pix;        // u: number of pixels between message arcs
    char        font[16];       // t: displayed message font
    uint8_t     f_size;         // u: font size of outermost message arc
    uint8_t     f_next;         // u: points that font is reduced for arc
    uint8_t     f_face;         // u: displayed message font style
    uint16_t    f_color;        // x: displayed message font color (night)
} config, *config_ptr;

typedef struct {                // the current location and time (28 B)
    time_t      ltc;            // local time at the current location (64b on ESP32)
    time_t      utc;            // UTC time at the current location (64b on ESP32)
    float       lat;            // current latitude
    float       lon;            // current longitude
    uint16_t    tz;             // current timezone index
    int16_t     tz_off;         // current timezone offset (hhmm)
} here, *here_ptr;

typedef struct {                // all globals in the system (size = 664 B)
    file_list   f;              // list of all files used (size = 320 B)
    config      c;              // configuration from config file (size = 52 B)
    here        h;              // current location (size = 28 B)
    char        msg[k_MAX];     // last message created (size = 256 B <k_MAX>)
    char        img[4];         // backround image file name (size = 4 B)
    uint16_t    ref;            // attribution reference number (size = 2 B)
    uint8_t     update;         // periodic update counter (size = 1 B)
    uint8_t     mode;           // mode flags to save (size = 1 B)
} globals, *globals_ptr;

typedef struct {                // placeholder strings (size = 5 * k_MAX B)
    char        a[k_MAX];       // placeholders a, b, and c are "normal" sized
    char        b[k_MAX];       //    buffers used for regular string assembly
    char        c[k_MAX];       //    operations.
    char        d[2 * k_MAX];   // placeholder d is "double-wide" for big strings
} placeholders, *placeholders_ptr;
