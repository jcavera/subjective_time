#include <stdio.h>      // used in main() only
#include <stdint.h>
#include <stdlib.h>
#include <time.h>       // used in main() only

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

uint16_t string_get_ref_pic (char *s, char *p)
{
    uint16_t r = 0, i = k_MAX_LEN - 1, j = 0;
    p[0] = 0x20; p[1] = 0x20; p[2] = 0x20; p[3] = 0;
    
    while (s[i] < 0x20) i--;
    if ((s[i] == ']') && (s[i-4] == '[')) { // there is an embed picture reference
        p[2] = s[i-1];  p[1] = s[i-2];  p[0] = s[i-3];
        for (j=k_MAX_LEN-1; j>i-6; j--) s[j] = 0;
        return (0);
    }
    if ((s[i] >= '0') && (s[i] <= '9') && (s[i-3] != '$')) { // if there is a reference
        r = (s[i] - '0') + (10 * (s[i-1] - '0')) + (100 * (s[i-2] - '0')) + (1000 * (s[i-3] - '0'));
        for (j=i; j>i-4; j--) s[j] = 0;
        i = j-1;
    }
    if (s[i-3] == '$') {  // if there is an image
        p[2] = s[i];  p[1] = s[i-1];  p[0] = s[i-2];
        for (j=i; j>i-4; j--) s[j] = 0;
    }
    for (i=k_MAX_LEN-1; i>0; i--) {
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

uint16_t rand_0toN (uint16_t N)
{
    if (N == 0) return (0);
    return ((uint16_t) ((float)rand() / ((float)RAND_MAX + 1.0) * (N + 1)));
}

uint16_t choose_between (char* s, char delim, char* out)
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
    r = string_get_ref_pic(aline, pic);  printf("[%s][%04d] %s. \n", pic, r, aline); // [   ][9012] this is a test with a reference.
    r = string_get_ref_pic(bline, pic);  printf("[%s][%04d] %s. \n", pic, r, bline); // [   ][0000] this is a test without a reference or picture.
    r = string_get_ref_pic(cline, pic);  printf("[%s][%04d] %s. \n", pic, r, cline); // [qst][4567] this is a test with ref and pic.
    r = string_get_ref_pic(dline, pic);  printf("[%s][%04d] %s. \n", pic, r, dline); // [q01][0000] this is a test with pic only.
    r = string_get_ref_pic(eline, pic);  printf("[%s][%04d] %s. \n", pic, r, eline); // [   ][0000] this one goes all the way to the end with no spce.
    r = string_get_ref_pic(fline, pic);  printf("[%s][%04d] %s. \n", pic, r, fline); // [   ][0000] and this one goes all the way to the end w space.
    r = string_get_ref_pic(gline, pic);  printf("[%s][%04d] %s. \n", pic, r, gline); // [p03][0000] this is what it looks like for an embed pic.

    char astr[k_MAX_LEN] = "part 1;part 2;part 3;part 4;part 5;part 6;part 7\r\n";
    char ostr[k_MAX_LEN] = "";
    srand(time(NULL));
    for (i=0; i<20; i++) {
        for (r=0; r<k_MAX_LEN; r++) ostr[r] = 0;
        r = choose_between(astr, ';', ostr);
        printf("[%3d] %d: %s \n", i, r, ostr);
    }
    return 0;
}

