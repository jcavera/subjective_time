#include <stdio.h>
#include <stdint.h>

#define k_MAX_LEN 256

// Extract the reference number from the end of the string; return 0 if not found.  String
// is truncated to the first space or non-number character before the reference.

uint16_t string_get_ref (char* s)
{
    uint16_t i = k_MAX_LEN - 1;        // start at the end of the string and work backwards
    uint16_t r = 0;                    // result: reference number or 0 if no reference found
    uint16_t a = 1;                    // order-of-magnitude multiplier
    while (s[i] < 0x20) i--;           // jump to the end of the string (last non-null char)
    if (s[i - 3] == '$') return 0;     // if third from last character is $, then pic only
    if (s[i - 3] == '~') return 0;     // if third from last character is ~, then no pic or ref
  
    while ((i > 0) && ((s[i] >= '0') || (s[i] <= '9') || (s[i] == 0))) {
        if ((s[i] >= '0') && (s[i] <= '9')) {
            r = r + ((s[i] - '0') * a);
            s[i] = 0;
            a = a * 10;
        }
        if (a == 10000) break;
        if (((s[i] > 0) && (s[i] < '0')) || (s[i] >= 'A')) break;
        i--;
    }
    if (s[i] == ' ') s[i] = 0;
    return (r);
}

// Extract the image string from the end of the string if found. String is truncated to the
// first non-space character before the reference.  This function is to be called after the
// function to get the reference number.  Otherwise, any reference number will be lost.

void string_get_pic (char* s, char* p)
{
    uint16_t i = k_MAX_LEN - 1;             // start at the end of the string and work backwards
    while ((i > 0) && (s[i] != '$')) i--;   // find the last instance of the dollar sign
    if (i > 1) {                            // if we found one...
        p[0] = s[i + 1];                        // copy the three characters after it
        p[1] = s[i + 2];
        p[2] = s[i + 3];
        if (s[i - 1] = ' ') s[i - 1] = 0;       // remove the space ahead of the dollar sign (if there)
        for (i; i < k_MAX_LEN; i++) s[i] = 0;   // and erase the dollar sign and what comes after
    }
}

int main()
{
    char aline[k_MAX_LEN] = "this is a test with a reference ~~~~~~~~~~~~ 9012";
    char bline[k_MAX_LEN] = "this is a test without a reference or picture ~~~";
    char cline[k_MAX_LEN] = "this is a test with ref and pic ~~~~~~~ $qst 4567";
    char dline[k_MAX_LEN] = "this is a test with pic only ~~~~~~~~~~~~~~~ $q01";
    
    char    pic[4] = "";
    uint8_t i      = 0;                                                                                      // expected output:
    printf("ref a = %04d : %s \n", string_get_ref(aline), aline);                                            //    ref a = 9012 : this is a test with a reference ~~~~~~~~~~~~
    printf("ref b = %04d : %s \n", string_get_ref(bline), bline);                                            //    ref b = 0000 : this is a test without a reference or picture ~~~
    printf("ref c = %04d : %s \n", string_get_ref(cline), cline);                                            //    ref c = 4567 : this is a test with ref and pic ~~~~~~~ $qst
    printf("ref d = %04d : %s \n", string_get_ref(dline), dline);                                            //    ref d = 0000 : this is a test with pic only ~~~~~~~~~~~~~~~ $q01
    printf("\n");
    for (i=0; i<4; i++) pic[i] = 0;  string_get_pic(aline, pic);  printf("pic a = %s : %s \n", pic, aline);  //    pic a =     : this is a test with a reference ~~~~~~~~~~~~
    for (i=0; i<4; i++) pic[i] = 0;  string_get_pic(bline, pic);  printf("pic b = %s : %s \n", pic, bline);  //    pic b =     : this is a test without a reference or picture ~~~
    for (i=0; i<4; i++) pic[i] = 0;  string_get_pic(cline, pic);  printf("pic c = %s : %s \n", pic, cline);  //    pic c = qst : this is a test with ref and pic ~~~~~~~
    for (i=0; i<4; i++) pic[i] = 0;  string_get_pic(dline, pic);  printf("pic d = %s : %s \n", pic, dline);  //    pic d = q01 : this is a test with pic only ~~~~~~~~~~~~~~~
    
    return 0;
}
