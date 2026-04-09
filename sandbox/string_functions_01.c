#include <stdio.h>
#include <stdint.h>

#define k_MAX_LEN 256

char aline[k_MAX_LEN] = "this is a test with a reference ~~~~~~~~~~~~ 9012";
char bline[k_MAX_LEN] = "this is a test without a reference or picture ~~~";
char cline[k_MAX_LEN] = "this is a test with ref and pic ~~~~~~~ $qst 4567";
char dline[k_MAX_LEN] = "this is a test with pic only ~~~~~~~~~~~~~~~ $q01";

// Extract the reference number from the end of the string; return 0 if not found.  String
// is truncated to the first space or non-number character after the reference.

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

int main()
{
    uint8_t i    = 0;                                               // expected output:
    printf("ref a = %04d : %s \n", string_get_ref(aline), aline);   //    ref a = 9012 : this is a test with a reference ~~~~~~~~~~~~
    printf("ref b = %04d : %s \n", string_get_ref(bline), bline);   //    ref b = 0000 : this is a test without a reference or picture ~~~
    printf("ref c = %04d : %s \n", string_get_ref(cline), cline);   //    ref c = 4567 : this is a test with ref and pic ~~~~~~~ $qst
    printf("ref d = %04d : %s \n", string_get_ref(dline), dline);   //    ref d = 0000 : this is a test with pic only ~~~~~~~~~~~~~~~ $q01
    return 0;
}
