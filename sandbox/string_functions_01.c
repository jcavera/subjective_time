// Functions Included:
//      str_get_ref_pic     Return an embedded or appended image and a reference number, if either exists.
//      choose_between      Return a randomly selected sub-string from a string containing a delimited list.
//      append_wo_eos       Append a string (b) to an input string (b) with an optional character in between.
//      find_in_str         Return the position of a sub-string (if found) in the input string.
//      replace_in_str      Replace the first instance of a sub-string (if found) with a new string.
//      word_len            Return the length of the first word in the string.
//      strip_eol           Strip off everything at the end of a line that is not displayed.

#include <stdio.h>      // used in main() only for printf calls
#include <stdint.h>
#include <stdlib.h>
#include <string.h>     // used for strlen
#include <time.h>       // used for random number seeding

#define k_MAX_LEN 256

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
//      00000000001111111111222222222233333333334444444444555
//      01234567890123456789012345678901234567890123456789012
//      this is a test with a reference ~~~~~~~~~~~~ 9012\\
//      this is a test without a reference or picture ~~~\\
//      this is a test with ref and pic ~~~~~~~ $qst 4567\\
//      this is a test with pic only ~~~~~~~~~~~~~~~ $q01\\
//      this one goes all the way to the end with no spce\\
//      and this one goes all the way to the end w space \\
//      this is what it looks like for an embed pic [p03]\\

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
    if ((delim <= 0x20) || (delim > 0x7e)) return (0);
    uint16_t r = 0, i = 0, j = 0;
    while ((s[i] >= 0x20) && (i < k_MAX_LEN)) { // count number of delimiters
        if (s[i] == delim) r++;
        i++;
    }
    if (r == 0) return (0);                     // return if no delimiters found
    r = rand_0toN(r);                           // select a random item (0..<# of delims>)
    j = r + 1; i = 0;
    while ((s[i] >= 0x20) && (r > 0)) {         // go to the rth delimiter
        if (s[i] == delim) r--;                 //  decrement r on hitting a delimiter
        i++;
    }
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
    for (i=alen, j=0; j<blen; i++, j++) {
        if (b[j] == '~') break;
        a[i] = b[j];
    }
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

// In the input string (in) eplace the first instance of a substring (find) with a new string
// (repl).  If any of the input strings have a length of zero, then return error. If the find
// string is not found, then return zero. The output string (out) must be pre-allocated to be
// large enough to store the result of the replace operation. The output string is cleared to
// null on entry to the function.   This is not an in-place operation and the output must not
// be the same string as any of the inputs.
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
    result = find_in_str(in, find, 0);                                      // find the first instance of (find) in (in)
    if (result == -1) return (0);                                           // return zero if (find) is not found
    for (i=0; i<out_len; i++) out[i] = 0;                                   // clear the output string
    
    k = result + find_len;
    for (i=0; i<result; i++) out[i] = in[i];                                // copy over the first part of (in)
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


int main()
{
    char     aline[k_MAX_LEN] = "this is a test with a reference ~~~~~~~~~~~~ 9012\r\n";
    char     bline[k_MAX_LEN] = "this is a test without a reference or picture ~~~\r\n";
    char     cline[k_MAX_LEN] = "this is a test with ref and pic ~~~~~~~ $qst 4567\r\n";
    char     dline[k_MAX_LEN] = "this is a test with pic only ~~~~~~~~~~~~~~~ $q01\r\n";
    char     eline[k_MAX_LEN] = "this one goes all the way to the end with no spce\r\n";
    char     fline[k_MAX_LEN] = "and this one goes all the way to the end w space \r\n";
    char     gline[k_MAX_LEN] = "this is what it looks like for an embed pic [p03]\r\n";
    char     pic[4] = "";
    uint16_t r = 0, i = 0;
                                                                                     // expected output:
    r = str_get_ref_pic(aline, pic);  printf("[%s][%04d] %s. \n", pic, r, aline); // [   ][9012] this is a test with a reference.
    r = str_get_ref_pic(bline, pic);  printf("[%s][%04d] %s. \n", pic, r, bline); // [   ][0000] this is a test without a reference or picture.
    r = str_get_ref_pic(cline, pic);  printf("[%s][%04d] %s. \n", pic, r, cline); // [qst][4567] this is a test with ref and pic.
    r = str_get_ref_pic(dline, pic);  printf("[%s][%04d] %s. \n", pic, r, dline); // [q01][0000] this is a test with pic only.
    r = str_get_ref_pic(eline, pic);  printf("[%s][%04d] %s. \n", pic, r, eline); // [   ][0000] this one goes all the way to the end with no spce.
    r = str_get_ref_pic(fline, pic);  printf("[%s][%04d] %s. \n", pic, r, fline); // [   ][0000] and this one goes all the way to the end w space.
    r = str_get_ref_pic(gline, pic);  printf("[%s][%04d] %s. \n", pic, r, gline); // [p03][0000] this is what it looks like for an embed pic.

    char astr[k_MAX_LEN] = "part 1;part 2;part 3;part 4;part 5;part 6;part 7\r\n";
    char ostr[k_MAX_LEN] = "";
    srand(time(NULL));
    for (i=0; i<20; i++) {
        for (r=0; r<k_MAX_LEN; r++) ostr[r] = 0;
        r = choose_between(astr, ostr, ';');
        printf("[%3d] %d: %s \n", i, r, ostr);
    }
    return 0;
}

