// Functions Included:
//      markup_proc_single      Process a single markup element of the form <tag.....
//      markup_subproc_sel      Process the <? (selection) tag.

// Required to use: string manipulation functions in the string_functions_01.c file

#include <stdio.h>      // used in main() only for printf calls
#include <stdint.h>
#include <stdlib.h>
#include <string.h>     // used for strlen
#include <time.h>       // used for random number seeding

#define k_MAX_LEN 256

char    markup_sub[k_MAX_LEN];
char    placehold_a[k_MAX_LEN];
char    placehold_b[k_MAX_LEN];

uint16_t markup_subproc_sel (char *s);                      // make a random choice between a list of items delimited by (|)


// Process the first algorithmic markup tag (<) found in the incoming string.  If none are found, return
// zero.  Otherwise return the character of the processed tag.

uint16_t markup_proc_single (char *s)
{
    uint16_t i = 0, j = 0, isr = 0;
    while ((s[i] != '<') && (s[i] >= 0x20)) i++;            // find the first instance of a markup delimiter
    if (s[i] == 0) return (0);                              // if we end without finding one, return null flag
    for (j=0; j<k_MAX_LEN; j++) markup_sub[j] = 0;          // erase the markup sub-string
    
    j = 0; isr = i;                                         // copy the markup part to the markup sub-string
    while ((s[i] != 0x20) && (s[i] != '\n') && (s[i] != '\r') && (s[i] != '/') && (s[i] != '~')) {
        markup_sub[j] = s[i];
        j++; i++;
    }   i = isr;
    
    switch (markup_sub[1]) {    // parse by tag type
        case 'A':           break;                          // latitude-longitude coordinates rendered as the nearest whole number
        case 'B':           break;                          // Benedryl Cucumber's birthday (yeah, just look at the associated function in app_markup.py)
        case 'C':           break;                          // ordinal century
        case 'D':           break;                          // day of the week
        case 'G':           break;                          // distance and/or direction from the specified GPS coordinates
        case 'H':           break;                          // current hour (24 hour format, GMT)
        case 'M':           break;                          // current month of the year
        case 'N':           break;                          // a random month of the year
        case 'O':           break;                          // random distance and/or direction
        case 'P':           break;                          // random on-playa location (for Burning Man related messages)
        case 'R':           break;                          // random number
        case 'S':           break;                          // the current season of the year
        case 'W':           break;                          // a random day of the week
        case 'Y':           break;                          // the current year
        case 'Z':           break;                          // the name of the current timezone
        case 'd':           break;                          // the ordinal date of the month
        case 'e':           break;                          // on-playa event classification (yeah, this is a weird one too)
        case 'g':           break;                          // geomagnetic orientation (currently unsupported, but reserved for future use)
        case 'h':           break;                          // current hour (24 hour format, local time)
        case 'i':           break;                          // the current hour (12 hour format)
        case 'm':           break;                          // the current minutes (in local time)
        case 'n':           break;                          // the current minutes (in GMT)
        case 'p':           break;                          // the current am or pm string
        case 'r':           break;                          // random number in ordinal form
        case 's':           break;                          // a substitution for the current hemisphere (south | north)
        case 't':           break;                          // another randomizer: time to | just about time to | a good time to | ...
        case 'y':           break;                          // the current ordinal day of the year
        case '?':   i = markup_subproc_sel(s);  break;      // make a random choice between a list of items delimited by (|)
        default:            break;
    }
    return (markup_sub[1]);     // return the tag type processed
}


uint16_t markup_subproc_sel (char *s)
{
    uint16_t i = 0, r = 0;
    for (i=0; i<k_MAX_LEN; i++) {  placehold_a[i] = 0;  placehold_b[i] = 0;  }  // erase the placeholder strings
    r = choose_between(markup_sub+2, placehold_a, '|');                         // choose one thing from the list
    replace_in_str(s, markup_sub, placehold_a, placehold_b, k_MAX_LEN);         // replace markup with chosen thing
    for (i=0; i<k_MAX_LEN; i++) s[i] = placehold_b[i];                          // and copy placeholder back to the string
    return (r);                                                                 // return the chosen item's index
}


int main()
{
    srand(time(NULL));
    char s[k_MAX_LEN] = "this has a random <?kiwi|biscuit|soda|wombat in it";
    uint16_t i = markup_proc_single(s);
    printf("%d : %s. \n", i, s);
    return 0;
}
