// Functions Included:
//      str_get_ref_pic         Return an embedded or appended image and a reference number, if either exists.
//      choose_between          Return a randomly selected sub-string from a string containing a delimited list.
//      append_wo_eos           Append a string (b) to an input string (b) with an optional character in between.
//      find_in_str             Return the position of a sub-string (if found) in the input string.
//      replace_in_str          Replace the first instance of a sub-string (if found) with a new string.
//      replace_c_in_str        Replace the first instance of a character (if found) with a new string.
//      word_len                Return the length of the first word in the string.
//      strip_eol               Strip off everything at the end of a line that is not displayed.
//      trim_string             Trim any leading and/or trailing spaces from the input string.
//
//      return_single_end       From the end of a string, return the first single-precision float found.
//      return_double_end       From the end of a string, return the first double-precision float found.
//      return_hex_end          From the end of a string, return the first unsigned 16b hex integer found.
//      return_int_end          From the end of a string, return the first signed 16b integer found.
//      return_uint_end         From the end of a string, return the first unsigned 16b integer found.
//      return_str_end          From the end of a string, return a string parameter.
//
//      pattern_yearsub         Find the first instance of the pattern (<abo>-n(...))
//      pattern_numsub          Find the first instance of the pattern #n(...)
//      pattern_macrosub        Find the first instance of the pattern _<m>
//
//      get_info_timezone       Return the timezone information from a formatted line in the all_rgn.txt file

#include <stdint.h>
#include <stdlib.h>
#include "string_functions.h"

// Extract the reference number from the end of the string; return 0 if not found. Extract
// the image string from the end of the string if found.  String is truncated to the first
// non-space, non-tilde character before the reference and/or image, as appropriate. The p
// parameter must be 4 characters; and the s parameter, k_MAX_LEN characters.
//
// Embedded image strings are always (a) at the end of the string and (b) in square braces
// like "[img]". If there is an embedded image string, extract it, set the reference id to
// zero, and return. If there is no embedded image string then look for a reference number
// at the end of the string. These are always four digits in length. If found, extract the
// reference number and look for an image string before it. Those image strings will start
// with a dollar sign ($). If there is one then extract it and return it and the reference
// number.  If there is both an image reference (not an embedded image, but a regular one)
// AND a reference number, then the reference number MUST be after the embedded image. See
// the test strings below for valid examples.
// 
// Test strings (\\ at the end are actually \r\n):
//      0000000000111111111122222222223333333333444444444455   ref#  image  resulting string
//      0123456789012345678901234567890123456789012345678901  ------ ----- --------------------------
//      this is a test with a reference ~~~~~~~~~~~~ 9012\\    9012         this is a test with a reference
//      this is a test without a reference or picture ~~~\\    0000         this is a test without a reference or picture
//      this is a test with ref and pic ~~~~~~~ $qst 4567\\    4567   qst   this is a test with ref and pic
//      this is a test with pic only ~~~~~~~~~~~~~~~ $q01\\    0000   q01   this is a test with pic only
//      this one goes all the way to the end with no spce\\    0000         this one goes all the way to the end with no spce
//      and this one goes all the way to the end w space \\    0000         and this one goes all the way to the end w space
//      this is what it looks like for an embed pic [p03]\\    0000   p03   this is what it looks like for an embed pic

uint16_t str_get_ref_pic (char *s, char *p)
{
    uint16_t r = 0, i = k_MAX_LEN - 1, j = 0;
    p[0] = 0x20; p[1] = 0x20; p[2] = 0x20; p[3] = 0;
    
    while (s[i] < 0x20) i--;                                    // walk backwards to the last character
    if ((s[i] == ']') && (s[i-4] == '[')) {                     // there is an embed picture
        p[2] = s[i-1];  p[1] = s[i-2];  p[0] = s[i-3];
        for (j=k_MAX_LEN-1; j>i-6; j--) s[j] = 0;
        return (0);                                             // if an embedded pic, no reference number
    }
    if ((s[i] >= '0') && (s[i] <= '9') && (s[i-3] != '$')) {    // if there is a reference number
        r = (s[i] - '0') + (10 * (s[i-1] - '0')) + (100 * (s[i-2] - '0')) + (1000 * (s[i-3] - '0'));
        for (j=i; j>i-4; j--) s[j] = 0;
        i = j-1;
    }
    if (s[i-3] == '$') {                                        // if there is an image
        p[2] = s[i];  p[1] = s[i-1];  p[0] = s[i-2];
        for (j=i; j>i-4; j--) s[j] = 0;
    }
    for (i=k_MAX_LEN-1; i>0; i--) {                             // wipe to the end of the real line
        if ((s[i] == '~') || (s[i] <= 0x20)) s[i] = 0;
        if (s[i] > 0x20) break;
    }
    return r;
}


// Return a random sub-string given that the input string is a list of strings separated
// by a delimiting character.   If the input string has no delimiters then a zero result
// is returned and the output string is empty.  Otherwise, the randomly selected item in
// the list is copied to the output string and the 1-based index of the item is returned
// as a result. The input string is assumed to be valid and of length k_MAX_LEN, and the
// output string is assumed to be of length k_MAX_LEN and initialized to null. Delimiter
// character is assumed to be printable ascii. Also note that the input string must have
// one LESS delimiter than there are choices.  I.e.: don't end the string with the delim
// character!
// 
// Test strings (\\ at the end are actually \r\n):
//      00000000001111111111222222222233333333334444444444555
//      01234567890123456789012345678901234567890123456789012
//      part 1;part 2;part 3;part 4;part 5;part 6;part 7\r\n

uint16_t rand_0toN (uint16_t N)     // random number generator from 0..N
{
    if (N == 0) return (0);
    return ((uint16_t) ((float)rand() / ((float)RAND_MAX + 1.0) * (N + 1)));
}

uint16_t choose_between (char* s, char* out, char delim)
{
    if ((delim <= 0x20) || (delim > 0x7e)) return (0);          // delimiter must be a displayable char
    uint16_t r = 0, i = 0, j = 0;
    while (s[i] >= 0x20) {  if (s[i] == delim) r++;  i++;  }    // count delimiters
    if (r == 0) return (0);                                     // return if no delimiters found
    r = rand_0toN(r);                                           // select a random item (0..<# of delims>)
    j = r + 1; i = 0;
    while ((s[i] >= 0x20) && (r > 0)) {  if (s[i] == delim) r--;  i++;  }    // jump to rth delimiter
    while ((s[i] >= 0x20) && (s[i] != delim)) { // copy everything from the delimiter to
        out[r] = s[i];                          //  the next one or to the end of the string
        r++; i++;                               //  whichever comes first
    }
    return (j);
}


// Append a string (b) to an input string (a) with a character (c) in between them.  If the
// in-between character is null, it is ignored.  On exit, return the length of the complete
// string.   The original and appended string is contained in the (a) input, and so it must
// have sufficient allocated space to contain both strings a and b; an in-between character
// and an ending null character (i.e.: alen + blen + 2).

uint16_t append_wo_eos (char *a, char *b, char c)
{
    uint16_t alen = strlen(a);
    uint16_t blen = strlen(b);
    uint16_t i = 0, j = 0, isr = 0;
    
    if (blen == 0) return (alen);
    if (c >= 0x20) {  a[alen] = c;  alen++;  }  // append the in-between character if there is one
    for (i=alen, j=0; j<blen; i++, j++) {  if (b[j] == '~') break;  a[i] = b[j];  }
    if (a[i] == 0x20) {  a[i] = 0;  i--;  }     // remove a trailing space if there is one
    return (i++);
}


// Find the position of a substring (t) within an input string (s).  If the substring is not
// found within the input string, return a -1. The position is the index in (s) of the first
// character in the test string (t) of the first match.  Only the first match is returned --
// searching stops when it is found.

int16_t find_in_str (char *s, char *t, uint16_t startat)
{
    uint16_t slen = strlen(s);
    uint16_t tlen = strlen(t);
    uint16_t i = 0, j = 0, isr = 0;
    
    if ((slen == 0) || (tlen == 0)) return (-1);    // return if s or t is null
    if (slen < tlen) return (-1);                   // return if t is larger than s
    for (i=startat; i<slen; i++) {
        isr = i;
        for (i,j=0; j<tlen; j++,i++) {
            if (s[i] != t[j]) break;
            if (j == tlen - 1) return (isr);
        }
        i = isr;
    }
    return (-1);
}


// In the input string (in) replace the first instance of a substring (find) with a new string
// (repl).  If any of the input strings have a length of zero, then return error.  If the find
// string is not found, then return zero.  The output string (out) must be pre-allocated to be
// large enough to store the result of the replace operation.  The output string is cleared to
// null on entry to the function.   Note that this is NOT an in-place operation and the output
// must not be the same string as any of the inputs. The related function, replace_c_in_str is
// optimized for the use case of a single character being searched for.
// 
// Test strings:
//        00000000001111111111222222222233333333334444444444555
//        01234567890123456789012345678901234567890123456789012
// in:    replace a thing in this
// find:  a thing
// repl:  another something else
// out:   replace another something else in this

int16_t replace_in_str (char *in, char *find, char *repl, char *out, uint16_t out_len)
{
    uint16_t in_len     = strlen(in);                                       // lengths of incoming strings
    uint16_t find_len   = strlen(find);
    uint16_t repl_len   = strlen(repl);
    int16_t  result     = 0;
    uint16_t i = 0, j = 0, k = 0;
    
    if ((in_len == 0) || (find_len == 0) || (repl_len == 0)) return (-1);   // return error if any input is null
    if (find_len > in_len) return (-1);                                     // return error if find string is bigger than input
    result = find_in_str(in, find, 0);                                      // find the first instance of (find) in (in)
    if (result == -1) return (0);                                           // return zero if (find) is not found
    if ((in_len - find_len + repl_len) >= out_len) return (-1);             // return error if not enough space in output
    for (i=0; i<out_len; i++) out[i] = 0;                                   // clear the output string
    
    k = result + find_len;
    for (i=0; i<result; i++) out[i] = in[i];                                // copy over the first part of (in)
    for (i,j=0; j<repl_len; i++,j++) out[i] = repl[j];                      // copy over the replacement part
    while (in[k]) {  out[i] = in[k];  i++;  k++;  }                         // copy over the last part of (in)
    return (i);                                                             // return length of output string
}

// Test strings:
//        00000000001111111111222222222233333333334444444444555
//        01234567890123456789012345678901234567890123456789012
// in:    replace a _ in this
// find:  _
// repl:  macro substitution
// out:   replace a macro substitution in this

int16_t replace_c_in_str (char *in, char find, char *repl, char *out, uint16_t out_len)
{
    uint16_t in_len     = strlen(in);                                       // lengths of incoming strings
    uint16_t repl_len   = strlen(repl);
    uint16_t i = 0, j = 0, k = 0, r = 0;
    
    if ((in_len == 0) || (find == 0) || (repl_len == 0)) return (-1);       // return error if any input is null
    while ((in[r] >= 0x20) && (in[r] != find)) r++;                         // jump to the first instance of find char
    if (in[r] < 0x20) return (-1);                                          // return error on character not found
    if ((in_len + repl_len - 1) >= out_len) return (-1);                    // return error if not enough space in output
    for (i=0; i<out_len; i++) out[i] = 0;                                   // clear the output string
    
    k = r + 1;
    for (i=0; i<r; i++) out[i] = in[i];                                     // copy over the first part of (in)
    for (i,j=0; j<repl_len; i++,j++) out[i] = repl[j];                      // copy over the replacement part
    while (in[k]) {  out[i] = in[k];  i++;  k++;  }                         // copy over the last part of (in)
    return (i);                                                             // return length of output string
}


// Determine the length of a word given that word delimiters can be a space character,
// a newline character, a carriage return character, a forward slash, or a tilde. This
// starts at the start of the input and continues until the end-of-word conditions are
// met.   If there are multiple words in the input string, it finds the length of only
// the first one, starting at position (i).

uint16_t word_len (char *a, uint16_t i)
{
    while ((a[i] != 0x20) && (a[i] != '\n') && (a[i] != '\r') && (a[i] != '/') && (a[i] != '~')) i++;
    return (i);
}


// Strip off everything at the end of a line that is not displayed.  This inlcudes trailing
// spaces, carriage returns, newlines, and tilde characters.  This is an in-place operation
// and the new string length is returned.

uint16_t strip_eol (char *a)
{
    uint16_t i = 0;
    while (a[i]) i++;                                                   // advance to the end of the string
    while ((a[i] <= 0x20) || (a[i] == '~')) {  a[i] = 0;  i--;  }       // reverse through it and delete bad chars
    return (i++);
}


// Remove both the leading and trailing spaces of a string along with trailing carriage returns
// and newlines (or any other unprintable at the end).  This is an in-place operation such that
// the original string is modified without making a copy.   This function returns the length of
// the modified string. Note that this also includes unprintables (cr, lf, etc.) as well as the
// tilde character (used as line length filler) from the end of the string.

uint16_t trim_string (char *s)
{
    uint16_t i = 0, j = 0;
    while (s[i] == 0x20)  i++;
    while (s[i] >= 0x20) { s[j] = s[i]; i++; j++; }
    while ((s[i] <= 0x20) || (s[i] == '~')) { s[i] = 0; i--; }
    return (i++);
}


// ============ The following functions read and return a parameter from the END of a string.  Used in reading
// ============ data from the configuration file, or stuff formatted similarly.

// Read and return a floating point number. The index (i) is on the LAST digit of the number
// and the number must be of the form: (+|-)nnn.nnnnnn.   On an invalid number, the function
// returns a NaN. Note that, because this is a single precision float, the smallest three or
// so digits of the result are not guaranteed to be an exact match to the string.  The other
// function returns a double, which likely will match everything in the input string. You'll
// want to use whichever makes more sense for the processor and application.

float return_single_end (char *s, uint16_t i)
{
    float r = 0.000000;
    float d = 0.000001;
    if ((s[i] < '0') || (s[i] > '9')) return sNAN;
    while ((((s[i] >= '0') && (s[i] <= '9')) || (s[i] == '.') || (s[i] == '+') || (s[i] == '-')) && (i > 0)) {
        if ((s[i] >= '0') && (s[i] <= '9')) {  r = r + (d * ((float) (s[i] - '0')));  d = d * 10.0;  }
        if (s[i] == '-') r = r * -1.00;
        i--;
    }
    return (r);
}

double return_double_end (char *s, uint16_t i)
{
    double r = 0.000000;
    double d = 0.000001;
    if ((s[i] < '0') || (s[i] > '9')) return dNAN;
    while ((((s[i] >= '0') && (s[i] <= '9')) || (s[i] == '.') || (s[i] == '+') || (s[i] == '-')) && (i > 0)) {
        if ((s[i] >= '0') && (s[i] <= '9')) {  r = r + (d * ((double) (s[i] - '0')));  d = d * 10.0;  }
        if (s[i] == '-') r = r * -1.00;
        i--;
    }
    return (r);
}


// Read and return an unsigned integer (16b) represented as a hexadecimal number. The index (i)
// is on the LAST digit of the number and the number must be of the form: (#|x)nn(..)n  with an
// up-to-4 character restriction on the length.   The processing stops when anything outside of
// the valid hex range (0..9aA..fF) is reached.  If the number is invalid, return zero.

uint16_t return_hex_end (char *s, uint16_t i)
{
    uint16_t r = 0x0;
    uint16_t d = 0x00000001;
    uint16_t j = 1;
    while ( ((s[i] >= '0') && (s[i] <= '9')) || ((s[i] >= 'a') && (s[i] <= 'f')) || ((s[i] >= 'A') && (s[i] <= 'F')) ) {
        if ((s[i] >= '0') && (s[i] <= '9')) {  r = r + (d * (s[i] - '0'));  d = d * 16;  }
        if ((s[i] >= 'a') && (s[i] <= 'f')) {  r = r + (d * (s[i] - 'a' + 10));  d = d * 16;  }
        if ((s[i] >= 'A') && (s[i] <= 'F')) {  r = r + (d * (s[i] - 'A' + 10));  d = d * 16;  }
        j++; if (j > 4) break;
        i--;
    }
    return (r);
}


// Read and return an integer (16b signed or unsigned) represented as a decimal number.   The
// index (i) is on the LAST digit of the number and the number is variable length and must be
// of the form: (+/-)nn(...)n with an up-to-4 character restriction on the length. Processing
// stops when anything outside of the valid character range (0..9+-) is reached.   If reading
// gives an invalid number, return zero.

int16_t return_int_end (char *s, uint16_t i)
{
    int16_t  r = 0;
    int16_t  d = 1;
    uint16_t j = 1;
    if ((s[i] < '0') || (s[i] > '9')) return 0;
    while ((((s[i] >= '0') && (s[i] <= '9')) || (s[i] == '+') || (s[i] == '-')) && (i > 0)) {
        if ((s[i] >= '0') && (s[i] <= '9')) {  r = r + (d * (s[i] - '0'));  d = d * 10;  }
        if (s[i] == '-') r = r * -1;
        j++; if (j > 4) break;
        i--;        
    }
}

uint16_t return_uint_end (char *s, uint16_t i)
{
    uint16_t r = 0;
    uint16_t d = 1;
    uint16_t j = 1;
    if ((s[i] < '0') || (s[i] > '9')) return 0;
    while ((((s[i] >= '0') && (s[i] <= '9'))) && (i > 0)) {
        if ((s[i] >= '0') && (s[i] <= '9')) {  r = r + (d * (s[i] - '0'));  d = d * 10;  }
        j++; if (j > 4) break;
        i--;        
    }
}


// Read and return a string from the end of the string to the first "filler" character (i.e. a
// tilde and possibly a space after that.  Do this by finding the last instance of a tilde and
// then advancing to the next non-space character and capturing everything to the (i) position
// in the initial string.  On success, return the length of the found string parameter.  If it
// fails, return zero.

uint16_t return_str_end (char *s, uint16_t i, char *p)
{
    uint16_t r = 0;
    uint16_t j = i;
    while ((s[i] != '~') && (i >= 0)) i--;      // jump to the last tilde character
    i++;  while (s[i] && (s[i] <= 0x20)) i++;   // the to the next non-space character after
    while (s[i] && (s[i] >= 0x20) && (i <= j))  {  p[r] = s[i];  i++;  r++;  }
    if (p[0] == 0) return (0);
    return (r);
}

// ============ The following functions are used in pattern matching and exist because regex's in C are a
// ============ complete pain in the ass and take up way too much memory anyway.  These are used in the
// ============ various markup functions to do things like year- and macro-substitution.

// Find the first instance in the input string of the pattern (<abo>-n<n<n<n>>>).  If no match
// is found, return zero.  On a match of (a-nnnn), return the number 1nnnn.  On a match of the
// pattern (b-nnnn) return the number 2nnnn.  On a match of (o-nnnn) return the number 3nnnn.

uint16_t pattern_yearsub (char *s)
{
    uint16_t t = 0, r = 0, d = 1;
    uint16_t i = 0;
    while ((s[i] >= 0x20) && (s[i] != '(')) i++;    // find the first instance of (
    if (s[i] < 0x20) return (0);                    // return null if none found
    i++;  switch (s[i]) {                           // parse by the type character <abo>
        case 'a':   t = 10000;  break;              //      sub = (a...
        case 'b':   t = 20000;  break;              //      sub = (b...
        case 'o':   t = 30000;  break;              //      sub = (o...
        default:    return (0);                     //      sub = (<not valid>
    }
    i++;  if (s[i] != '-') return (0);              // error if next character is not a dash
    while ((s[i] != ')') && (s[i] > 0x20)) i++;     // advance to the ) character
    do {
        i--;
        if ((s[i] < '0') || (s[i] > '9')) break;    // a non-number was found - return 0
        r = r + ((s[i] - '0') * d);  d = d * 10;    // add the number to the result
    } while (s[i] != '-');
    return (t + r);
}


// Find the first instance of the number substitution pattern in the input string: #n(..).
// If there is no such pattern found, return -1.  If a number is found, return that number
// and delete the number representation from the string except for the # character.   That
// remaining # character may be used to make a text substitution later on.
//
// Test string:         this has a #123456 in it
// Return number:       123456
// Remaining string:    this has a # in it

int32_t pattern_numsub (char *s)
{
    int32_t  r = 0;
    uint16_t i = 0, isr = 0;
    while ((s[i] >= 0x20) && (s[i] != '#')) i++;    // find the first # character
    if (s[i] < 0x20) return (-1);                   // return -1: nothing found
    isr = i; i++;
    while ((s[i] >= '0') && (s[i] <= '9')) {        // get the number
        r = (10 * r) + (s[i] - '0');
        i++;
    }
    while (s[i])    { s[isr] = s[i]; isr++; i++; }  // remove (in-place) the number
    while (isr < i) { s[isr] = 0; isr++; }
    return (r);
}


// Find the first instance of the macro substitution pattern in the input string: _<m>. If
// there is no such pattern, return -1.  If a macro is found, return the character <m> and
// delete the character from the string leaving only the _ character. That _ character may
// be used to make a text substitution later on.
//
// Test string:         this has a _m in it
// Return number:       int('m') = 109
// Remaining string:    this has a _ in it

int16_t pattern_macrosub (char *s)
{
    int32_t  r = 0;
    uint16_t i = 0;
    while ((s[i] >= 0x20) && (s[i] != '_')) i++;    // find the first _ character
    if (s[i] < 0x20) return (-1);                   // return -1: nothing found
    i++; r = (int16_t) s[i];                        // fetch the macro character
    while (s[i]) { s[i] = s[i+1]; i++; }            // remove the macro character
    return (r);
}


// From the incoming timezone string (see examples below) return the timezone name and the
// offset indicator.  For a static offset, the return type is signed four digits: (-)hhmm.
// For a zone file reference, the offset is the zone file number + 10000.  If an error has
// occured, the function returns -1.  Example lines (and the returned offset and name) are
// as follows:
//
//    00000000001111111111222222222233333333334444444444555555  offset  name
//    01234567890123456789012345678901234567890123456789012345  ------ ----------------
//    +04050,+009700;africa/douala ~~~~~~~~~~~~~~~~~~ +01:00     0100   douala
//    +27154,-013203;africa/el aaiun ~~~~~~~~~~~~~~~~ z_021.    10021   el aaiun
//    +08484,-013234;africa/freetown ~~~~~~~~~~~~~~~~~~~~~~~     0000   freetown
//
// The timezone name is returned in the parameter: z.  This must be pre-allocated in order
// to be used with a minimum string size of 32 characters.

int16_t get_info_timezone (char *s, char *z)
{
    int16_t i = 15, isr = 0, j = 0;                 // starting location at char 15
    while ((s[i] >= 0x20) && (s[i] != '~')) i++;    // find the first ~ character
    if (s[i] < 0x20) return (-1);                   // return error if not found
    isr = i - 1;
    while ((i > 15) && (s[i] != '/')) i--;          // then back up to the last '/' character
    if (i <= 15) return (-1);                       // return error if not found
    for (i; i<isr; i++, j++) z[j] = s[i];           // copy over the zone name
    
    switch (s[48]) {
        case '+': j =       ((s[49] - '0') * 1000) + ((s[50] - '0') * 100) + ((s[52] - '0') * 10) + (s[53] - '0');  break; 
        case '-': j = -1 * (((s[49] - '0') * 1000) + ((s[50] - '0') * 100) + ((s[52] - '0') * 10) + (s[53] - '0')); break;
        case 'z': j =                        10000 + ((s[50] - '0') * 100) + ((s[51] - '0') * 10) + (s[52] - '0');  break;
        case '~': j = 0;  break;
        default:  j = -1; break;
    }
    return (j);
}
