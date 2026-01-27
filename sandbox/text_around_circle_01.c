// This demo works on Wokwi.com, using the ESP32 "joke machine" example.  Replace all of the
// code in that example .ino file with this code, and get rid of the JSON library as well as
// the button.  It takes about 10-ish seconds to go through the steps of writing the string,
// warping the text, and downsampling it to the screen.   The text is pretty much unreadable
// (hopefully) because the screen size is so small (240 pix).   I'm going to try this out on
// physical hardware with a much larger screen size.  My hope is that it looks better (or at
// least readable) on an 800x800 pix screen.

#include <math.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>   // 320x240 pixel screen from Wokwi
#include <Fonts/FreeMono18pt7b.h>

char sometext[5][60] = { "00000000011111111112222222222333333333344444444445555555555",
                         "12345678901234567890123456789012345678901234567890123456789",
                         "this is a line of sample text with fifty nine characters in",
                         "it, rendered using a mono-spaced font at 18 point size then",
                         "wrapped around a circle with the test algorithm given below"  };

#define mpi     (3.14159265359) /* pi                                       */
#define r_to_d  (180.0 / mpi)   /* convert radians to degrees               */

#define scr_w   (320)           /* screen width                             */
#define scr_h   (240)           /* screen height                            */
#define sx      (1260)          /* source width (default font = 360 x 60)   */
#define sy      (200)           /* source height                            */
#define as      (2.356194)      /* starting angle = 135 deg                 */
#define ae      (0.785398)      /* ending angle   =  45 deg                 */

#define TFT_DC 2
#define TFT_CS 15

void setup() {
    uint16_t x, y;
    uint32_t t0 = millis();
    
    Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);    // set up the screen and rotation
    tft.begin();
    tft.setRotation(1);
    tft.fillScreen(0x0000);
    tft.println("rendering text...");
    
    GFXcanvas1 src(sx, sy);                                     // set up 1b source drawing area and print the strings
    src.fillScreen(0);
    src.setCursor(10, 30);
    src.setFont(&FreeMono18pt7b);
    for (x=0; x<5; x++) src.println(sometext[x]);
 
    uint16_t dx     = (min(scr_w, scr_h) - 6) * 2;              // destination canvas size (square based on the smallest screen
    uint16_t dy     = dx;                                       //   dimension and then doubled for oversampling)
    uint16_t cx     = dx / 2;                                   // destination center co-ordinates
    uint16_t cy     = dy / 2;
    float    ro     = floor(((float) dx - 1) / 2);              // outer radius based on the canvas size
    float    ri     = floor(ro * 0.50);
    uint16_t xstart = cx - ro;                                  // starting x = center - outer radius
    uint16_t xend   = cx + ro;                                  // ending   x = center + outer radius
    uint16_t ystart = cy - ro;                                  // starting y = center - outer radius
    uint16_t yend   = cy + int(0.7071 * ro) + 1;                // ending   y = center - outer exclusion radius
    uint16_t exrad  = int(0.7071 * ri);                         // exclusion radius (inner)
    uint16_t xex_s  = cx - exrad + 1;                           // x location of the inner exclusion zone starting point
    uint16_t xex_e  = cx + exrad - 1;                           // x location of the inner exclusion zone ending point
    uint16_t yex_s  = cy - exrad + 1;                           // y location of the inner exclusion zone starting point
    float    rrange = ro - ri;                                  // radial range
    float    arange = (mpi * 3.0) / 2.0;                        // full angular range (3/4ths of a circle)
    
    uint16_t src_x, src_y;                                      // derived <x,y> location in the source bitmap
    float    r      = 0.00;                                     // radius of point <x,y> from <cx,cy>
    float    theta  = 0.00;                                     // angle of point <x,y> from <cx,cy>
    float    a, b, aa, bb;

    GFXcanvas1 dest(dx, yend);                                  // set up destination 1b drawing area, oversampled to 2x screen
    dest.fillScreen(0);
    tft.println("warping...");
    for (x=xstart; x<xend; x++) {                               // step through all x,y in the destination area
        for (y=ystart; y<yend; y++) {
            if ((y > yex_s) && (x > xex_s) && (x < xex_e)) goto skip;   // break out of this iteration if in the exclusion zone
            a = ((float) x) - ((float) cx);                             // <a,b> = <x,y> position relative to center <cx,cy>
            b = ((float) y) - ((float) cy);
            r = sqrt((a * a) + (b * b));                                // compute the radius of point <x,y> relative to <cx,cy>
            if ((r < ri) || (r > ro)) goto skip;                        // break if radius is not in the allowed radial zone
            theta = atan2(b, a);                                        // compute the angle of the point <x, y> relative to <cx,cy>
            if ((theta > ae) && (theta < as)) goto skip;                // break if outside of the allowed angles
            
            // now that we have a valid radial and angular position within the limits, justify both
            aa = 1.0 - ((r - ri) / rrange);                             // fraction of radial range from outer to inner (0...1.0)
            // Determine the fraction of the angular range from astart to aend expressed as (0..1.0).
            bb = 225.0 + (r_to_d * theta);                              // convert to degrees in preparation for better mapping
            if (bb > 360.0) bb = (bb - 360.0);
            bb = bb / 270.0;
            src_x = round(bb * sx);                                     // derive the pixel location in the source bitmap
            src_y = round(aa * sy);
            if (src.getPixel(src_x, src_y)) dest.drawPixel(x, y, 0xF);  // if non-zero, draw pixel to the destination
skip:
            // point was invalid so we skip to the next one
        }
    }
    // downsampling to 1/2 size
    uint16_t ddx    = dx / 2;                                   // downsampled canvas size
    uint16_t ddy    = dy / 2;
    uint16_t pix    = 0x0000;                                   // single pixel color of rendering canvas
    
    GFXcanvas16 rend(ddx, ddy);                                 // set up rendering drawing area
    rend.fillScreen(0x0000);
    tft.println("downsampling...");
    // <--- draw the background image here (if there is one)
    for (x=0; x<dx; x=x+2) {                                    // step through all x,y in the dest area by twos
        for (y=0; y<yend+2; y=y+2) {
            pix = 0x0000;                                               // re-init pix value
            if (dest.getPixel(x, y))      pix = pix + 0x0300;           // sum up the four adjacent pixels
            if (dest.getPixel(x+1, y))    pix = pix + 0x0300;
            if (dest.getPixel(x, y+1))    pix = pix + 0x0300;
            if (dest.getPixel(x+1, y+1))  pix = pix + 0x0300;
            if (pix > 0x0700) pix = 0x0B00;                             // up the brightness if three are filled
            if (pix > 0x0B00) pix = 0x0F00;                             // max out the brightness if all are filled
            if (pix > 0) rend.drawPixel((x/2), (y/2), pix);             // on non-zero, draw the downsampled pixel
        }
    }
    tft.drawRGBBitmap((scr_w - ddx) / 2, (scr_h - ddy) / 2, rend.getBuffer(), ddx, ddy);
    tft.setCursor(((scr_w / 2) - 10), (scr_h - 20));            // set the cursor for the attribution text
    tft.setTextColor(0x07E0, 0x0000);                           // set text color to med. green (black background)
    tft.print(millis() - t0);                                   // draw the sample attribution text
}

void loop() {
  delay(100);
}
