#include <stdio.h>
#include <stdint.h>

#define k_MAX_LEN 256

// Extract the reference number from the end of the string; return 0 if not found. Extract
// the image string from the end of the string if found.  String is truncated to the first
// non-space, non-tilde character before the reference and/or image, as appropriate. The p
// parameter must be 4 characters; and the s parameter, k_MAX_LEN characters.

// Test strings (\\ at the end are actually \r\n):
//      00000000001111111111222222222233333333334444444444555
//      01234567890123456789012345678901234567890123456789012
//      this is a test with a reference ~~~~~~~~~~~~ 9012\\
//      this is a test without a reference or picture ~~~\\
//      this is a test with ref and pic ~~~~~~~ $qst 4567\\
//      this is a test with pic only ~~~~~~~~~~~~~~~ $q01\\
//      this one goes all the way to the end with no spce\\
//      and this one goes all the way to the end w space \\

uint16_t string_get_ref_pic (char *s, char *p)
{
    uint16_t r = 0, i = k_MAX_LEN - 1, j = 0;
    p[0] = 0x20; p[1] = 0x20; p[2] = 0x20; p[3] = 0;
    
    while (s[i] < 0x20) i--;
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


int main()
{
    char     aline[k_MAX_LEN] = "this is a test with a reference ~~~~~~~~~~~~ 9012\r\n";
    char     bline[k_MAX_LEN] = "this is a test without a reference or picture ~~~\r\n";
    char     cline[k_MAX_LEN] = "this is a test with ref and pic ~~~~~~~ $qst 4567\r\n";
    char     dline[k_MAX_LEN] = "this is a test with pic only ~~~~~~~~~~~~~~~ $q01\r\n";
    char     eline[k_MAX_LEN] = "this one goes all the way to the end with no spce\r\n";
    char     fline[k_MAX_LEN] = "and this one goes all the way to the end w space \r\n";
    char     pic[4] = "";
    uint16_t r = 0;
                                                                                     // expected output:
    r = string_get_ref_pic(aline, pic);  printf("[%s][%04d] %s. \n", pic, r, aline); // [   ][9012] this is a test with a reference.
    r = string_get_ref_pic(bline, pic);  printf("[%s][%04d] %s. \n", pic, r, bline); // [   ][0000] this is a test without a reference or picture.
    r = string_get_ref_pic(cline, pic);  printf("[%s][%04d] %s. \n", pic, r, cline); // [qst][4567] this is a test with ref and pic.
    r = string_get_ref_pic(dline, pic);  printf("[%s][%04d] %s. \n", pic, r, dline); // [q01][0000] this is a test with pic only.
    r = string_get_ref_pic(eline, pic);  printf("[%s][%04d] %s. \n", pic, r, eline); // [   ][0000] this one goes all the way to the end with no spce.
    r = string_get_ref_pic(fline, pic);  printf("[%s][%04d] %s. \n", pic, r, fline); // [   ][0000] and this one goes all the way to the end w space.
    return 0;
}
