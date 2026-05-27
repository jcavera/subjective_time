#include <stdint.h>
#include <stdlib.h>

#define sNAN        ((float)  0x8fc00000)
#define dNAN        ((double) 0x7ff8000000000000)
#define k_MAX_LEN   256

// ------------------------------------------------------------------------------------------------------- FUNCTION PROTOTYPES

uint16_t    str_get_ref_pic     (char *s, char *p);                                                 // Return an embedded or appended image and a reference number, if either exists.
uint16_t    choose_between      (char *s, char *out, char delim);                                   // Return a randomly selected sub-string from a string containing a delimited list.
uint16_t    append_wo_eos       (char *a, char *b, char c);                                         // Append a string (b) to an input string (b) with an optional character in between.
int16_t     find_in_str         (char *s, char *t, uint16_t startat);                               // Return the position of a sub-string (if found) in the input string.
int16_t     replace_in_str      (char *in, char *find, char *repl, char *out, uint16_t out_len);    // Replace the first instance of a sub-string (if found) with a new string.
int16_t     replace_c_in_str    (char *in, char  find, char *repl, char *out, uint16_t out_len);    // Replace the first instance of a character (if found) with a new string.
uint16_t    word_len            (char *a, uint16_t i);                                              // Return the length of the first word in the string.
uint16_t    strip_eol           (char *a);                                                          // Strip off everything at the end of a line that is not displayed.
uint16_t    trim_string         (char *s);                                                          // Trim any leading and/or trailing spaces from the input string.

float       return_single_end   (char *s, uint16_t i);                                              // From the end of a string, return the first single-precision float found.
double      return_double_end   (char *s, uint16_t i);                                              // From the end of a string, return the first double-precision float found.
uint16_t    return_hex_end      (char *s, uint16_t i);                                              // From the end of a string, return the first unsigned 16b hex integer found.
int16_t     return_int_end      (char *s, uint16_t i);                                              // From the end of a string, return the first signed 16b integer found.
uint16_t    return_uint_end     (char *s, uint16_t i);                                              // From the end of a string, return the first unsigned 16b integer found.
uint16_t    return_str_end      (char *s, uint16_t i, char *p);                                     // From the end of a string, return a string parameter.

uint16_t    pattern_yearsub     (char *s);                                                          // Find the first instance of the pattern (<abo>-n(...)).
int32_t     pattern_numsub      (char *s);                                                          // Find the first instance of the pattern #n(...).
int16_t     pattern_macrosub    (char *s);                                                          // Find the first instance of the pattern _<m>.

int32_t     get_info_timezone   (char *s, char *z);                                                 // Return the timezone information from a formatted line in the all_rgn.txt file.
