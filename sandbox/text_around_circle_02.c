// This demo works on Wokwi.com, using the ESP32 "joke machine" example.  Replace all of the
// code in that example .ino file with this code, and get rid of the JSON library as well as
// the button.  It takes about 10-ish seconds to go through the steps of writing the string,
// warping the text, and downsampling it to the screen.   The text is pretty much unreadable
// (hopefully) because the screen size is so small (240 pix).   I'm going to try this out on
// physical hardware with a much larger screen size.  My hope is that it looks better (or at
// least readable) on an 800x800 pix screen.
//
// For the v_02 version: separate this out into different drawing functions and make the gfx
// stuff globally available.  This will test the called-multiple-times scenario, so we don't
// constantly allocate memory for the canvasas.

#include <math.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>   // 320x240 pixel screen from Wokwi
#include <Fonts/FreeMono18pt7b.h>

#define mpi     (3.14159265359) /* pi                                       */
#define r_to_d  (180.0 / mpi)   /* convert radians to degrees               */

#define scr_w   (320)           /* screen width                             */
#define scr_h   (240)           /* screen height                            */
#define sx      (1260)          /* source width (default font = 360 x 60)   */
#define sy      (200)           /* source height                            */
#define as      (2.356194)      /* starting angle = 135 deg                 */
#define ae      (0.785398)      /* ending angle   =  45 deg                 */

#define TFT_DC  2
#define TFT_CS  15

// Normally these are computed based on the above constants, but we're defining them
// here, since they're used by multiple functions.  In practice, we'll want to do this
// anyways, in order to get the best look on whatever screen we're using.

#define dx     (468)             /* destination canvas size (square based on the smallest screen: (min(scr_w, scr_h) - 6) * 2    */
#define dy     (468)             /*   dimension and then doubled for oversampling)                                               */
#define ddx    (234)             /* downsampled canvas size                                                                      */
#define ddy    (234)
#define cx     (234)             /* destination center co-ordinates: dx / 2, dy / 2                                              */
#define cy     (234)
#define ro     (233)             /* outer radius based on the canvas size: floor(((float) dx - 1) * 0.50)                        */
#define ri     (116)             /* inner radius based on the outer: floor(ro * 0.50)                                            */
#define xstart (1)               /* starting x = center - outer radius                                                           */
#define xend   (467)             /* ending   x = center + outer radius                                                           */
#define ystart (1)               /* starting y = center - outer radius                                                           */
#define yend   (399)             /* ending   y = center - outer exclusion radius: cy + int(0.7071 * ro) + 1                      */
#define exrad  (82)              /* exclusion radius (inner): int(0.7071 * ri)                                                   */
#define xex_s  (153)             /* x location of the inner exclusion zone starting point: cx - exrad + 1                        */
#define xex_e  (315)             /* x location of the inner exclusion zone ending point: cx + exrad - 1                          */
#define yex_s  (153)             /* y location of the inner exclusion zone starting point: cy - exrad + 1                        */
#define rrange (117)             /* radial range: ro - ri                                                                        */
#define arange (4.71238898)      /* full angular range (3/4ths of a circle, or 3pi/2)                                            */

char sometext[5][60] = { "00000000011111111112222222222333333333344444444445555555555",
                         "12345678901234567890123456789012345678901234567890123456789",
                         "this is a line of sample text with fifty nine characters in",
                         "it, rendered using a mono-spaced font at 18 point size then",
                         "wrapped around a circle with the test algorithm given below"  };

GFXcanvas1  src(sx, sy);         // 1b source drawing area for the un-warped text lines
GFXcanvas1  dest(dx, yend);      // 1b destination drawing area for the warped text
GFXcanvas16 rend(ddx, ddy);      // 16b RGB rendering drawing area

void draw_text (void) {
    src.fillScreen(0);
    src.setCursor(10, 30);
    src.setFont(&FreeMono18pt7b);
    for (int x=0; x<5; x++) src.println(sometext[x]);
}

void draw_warp (void) {
    uint16_t x, y;
    uint16_t src_x, src_y;                                      // derived <x,y> location in the source bitmap
    float    r      = 0.00;                                     // radius of point <x,y> from <cx,cy>
    float    theta  = 0.00;                                     // angle of point <x,y> from <cx,cy>
    float    a, b, aa, bb;

    dest.fillScreen(0);                                        // erase the destination canvas
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
            // Point was invalid so we skip to the next one.  And yes, I used "goto's".  It was expedient and
            // I thought I might need to do something here, so I didn't use "break".  I know.  Shut up.
        }
    }
}

void draw_final (void) {
    uint16_t x, y;
    uint16_t pix    = 0x0000;                                   // single pixel color of rendering canvas
    rend.fillScreen(0x0000);                                    // erase the drawing area
    // <--- draw the background image here (if there is one)
    for (x=0; x<dx; x=x+2) {                                    // step through all x,y in the dest area by twos
        for (y=0; y<yend+2; y=y+2) {
            pix = 0x0000;                                               // re-init pix value
            if (dest.getPixel(x, y))      pix++;                        // sum up the four adjacent pixels
            if (dest.getPixel(x+1, y))    pix++;
            if (dest.getPixel(x, y+1))    pix++;
            if (dest.getPixel(x+1, y+1))  pix++;
            switch (pix) {                                              // set the color based on the number
                case 1:   pix = 0x0200; break;                          // of filled pixels allowing us to be
                case 2:   pix = 0x0600; break;                          // a little bit non-linear - just play
                case 3:   pix = 0x0B00; break;                          // with this until it looks good
                case 4:   pix = 0x0F00; break;
                default:  pix = 0x0000; break;
            }
            if (pix > 0) rend.drawPixel((x/2), (y/2), pix);             // on non-zero, draw the downsampled pixel
        }
    }
}

void setup() {
    uint32_t t0 = millis();
    Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);    // set up the screen and rotation
    tft.begin();
    tft.setRotation(1);
    tft.fillScreen(0x0000);

    draw_text();        // draw text to the 1b port
    draw_warp();        // draw the warped text
    draw_final();       // downsample
    tft.drawRGBBitmap((scr_w - ddx) / 2, (scr_h - ddy) / 2, rend.getBuffer(), ddx, ddy);
    tft.setCursor(((scr_w / 2) - 10), (scr_h - 20));            // set the cursor for the attribution text
    tft.setTextColor(0x07E0, 0x0000);                           // set text color to med. green (black background)
    tft.print(millis() - t0);                                   // draw the sample attribution text
}

void loop() {
  delay(100);
}
