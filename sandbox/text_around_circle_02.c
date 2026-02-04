// This demo works on Wokwi.com, using the ESP32 "joke machine" example.  Replace all of the
// code in that example .ino file with this code, and get rid of the JSON library as well as
// the button.  It takes about 14-ish seconds to go through the steps of writing the string,
// warping the text, and downsampling it to the screen.   The text is pretty much unreadable
// (hopefully) because the screen size is so small (240 pix).   I'm going to try this out on
// physical hardware with a much larger screen size.  My hope is that it looks better (or at
// least readable) on an 800x800 pix screen.
//
// Version 02: This is modularized so that we can (in theory) call the drawing routines more
//             than once.  Just so long as we only init and de-init once, of course.  Also I
//             edited the display string to be a bit more representational of characters and
//             symbols that the final system will use.

#include <math.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>   // 320x240 pixel screen from Wokwi
#include <Fonts/FreeMono18pt7b.h>

char sometext[5][60] = { "the quick brown fox jumped over the lazy dog sir! sphynx of",
                         "black quartz judge my vow? the quick brown fox jumped over ",
                         "the lazy dog sir? sphynx of black quartz judge my vow!! the",
                         "quick brown fox jumped over the lazy dog again -- sphynx of",
                         "black quartz judge my vow! the quick brown fox jumped over?"  };

#define mpi     (3.14159265359) /* pi                                       */
#define r_to_d  (57.2957795131) /* convert radians to degrees (180 / pi)    */

#define scr_w   (320)           /* screen width                             */
#define scr_h   (240)           /* screen height                            */
#define sx      (1260)          /* source width (w. default font = 360)     */
#define sy      (200)           /* source height (               =  60)     */
#define as      (2.356194)      /* starting angle = 135 deg                 */
#define ae      (0.785398)      /* ending angle   =  45 deg                 */
#define margin  (8)             /* margin width around all the sides        */

#define TFT_DC  2               /* control lines for the TFT screen         */
#define TFT_CS  15

#define dx      (464)           /* destination canvas size (square based on smallest screen = (min(scr_w, scr_h) - margin) * 2; */
#define dy      (464)           /*   dimension and then doubled for oversampling)           = dx;                               */
#define cx      (232)           /* destination center co-ordinates                          = dx / 2;                           */
#define cy      (232)           /*                                                          = dy / 2;                           */
#define ro      (231)           /* outer radius based on the canvas size                    = floor(((float) dx - 1) * 0.50);   */
#define ri      (115)           /* inner radius as a fraction of the outer                  = floor(ro * 0.50);                 */
#define xstart  (1)             /* starting x = center - outer radius                       = cx - ro;                          */
#define xend    (463)           /* ending   x = center + outer radius                       = cx + ro;                          */
#define ystart  (1)             /* starting y = center - outer radius                       = cy - ro;                          */
#define yend    (396)           /* ending   y = center - outer exclusion radius             = cy + int(0.7071 * ro) + 1;        */
#define exrad   (81)            /* exclusion radius (inner)                                 = int(0.7071 * ri);                 */
#define xex_s   (152)           /* x location of the inner exclusion zone starting point    = cx - exrad + 1;                   */
#define xex_e   (312)           /* x location of the inner exclusion zone ending point      = cx + exrad - 1;                   */
#define yex_s   (152)           /* y location of the inner exclusion zone starting point    = cy - exrad + 1;                   */
#define ddx     (232)           /* downsampled canvas size                                  = dx / 2;                           */
#define ddy     (232)           /*                                                          = dy / 2;                           */
#define rrange  (116.000000)    /* radial range (float)                                     = ro - ri;                          */
#define arange  (4.71238898)    /* full angular range (3/4ths of a circle)                  = (mpi * 1.5);                      */
#define off_x   (44)            /* x-axis offset from the rendering canvas to the screen    = (scr_w - ddx) / 2;                */
#define off_y   (4)             /* y-axis offset from the rendering canvas to the screen    = (scr_h - ddy) / 2;                */
#define attr_x  (150)           /* x position of the attribution text                       = (scr_w / 2) - 10;                 */
#define attr_y  (220)           /* y position of the attribution text                       = scr_h - 20;                       */

Adafruit_ILI9341   tft   = Adafruit_ILI9341(TFT_CS, TFT_DC); // set up the screen and rotation
static GFXcanvas1  *src;        // 1b source drawing area and print the strings
static GFXcanvas1  *dest;       // destination 1b drawing area, oversampled to 2x screen
static GFXcanvas16 *rend;       // rendering drawing area

// Initialize the offscreen canvases, allowing for reuse and multiple calls to the drawing functions
void draw_init (void) {
    tft.begin();                             // initilize and set-up the TFT display
    tft.setRotation(1);
    src  = new GFXcanvas1(sx, sy);           // set up 1b source drawing area and print the strings
    dest = new GFXcanvas1(dx, yend);         // set up destination 1b drawing area, oversampled to 2x screen
    rend = new GFXcanvas16(ddx, ddy);        // set up rendering drawing area
}

// Draw the text to the first everything-in-line canvas
void draw_text (void) {
    src->fillScreen(0);
    src->setCursor(10, 30);
    src->setFont(&FreeMono18pt7b);
    for (int x=0; x<5; x++) src->println(sometext[x]);    
}

// Warp the text from the first canvas to the warp canvas (still 1b)
void draw_warp (void) {
    uint16_t x, y;
    uint16_t src_x, src_y;                                      // derived <x,y> location in the source bitmap
    float    r      = 0.00;                                     // radius of point <x,y> from <cx,cy>
    float    theta  = 0.00;                                     // angle of point <x,y> from <cx,cy>
    float    a, b, aa, bb;

    dest->fillScreen(0);
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
            if (src->getPixel(src_x, src_y)) dest->drawPixel(x, y, 0xF);  // if non-zero, draw pixel to the destination
skip:
            // Point was invalid so we skip to the next one.  And yes, I used "goto's".  It was expedient and
            // I thought I might need to do something here, so I didn't use "break".  I know.  Shut up.
        }
    }
}

// Downsize the warped canvas to the rendering canvas and colorize based on the number of filled-in pixels
void draw_down (void) {
    uint16_t x, y;
    uint16_t pix    = 0x0000;                                   // single pixel color of rendering canvas
    rend->fillScreen(0x0000);
    // <--- draw the background image here (if there is one)
    for (x=0; x<dx; x=x+2) {                                    // step through all x,y in the dest area by twos
        for (y=0; y<yend+2; y=y+2) {
            pix = 0x0000;                                       // re-init pix value
            if (dest->getPixel(x, y))      pix++;               // sum up the four adjacent pixels
            if (dest->getPixel(x+1, y))    pix++;
            if (dest->getPixel(x, y+1))    pix++;
            if (dest->getPixel(x+1, y+1))  pix++;
            switch (pix) {                                      // set the color based on the number
                case 1:   pix = 0x0200; break;                  // of filled pixels allowing us to be
                case 2:   pix = 0x0600; break;                  // a little bit non-linear - just play
                case 3:   pix = 0x0B00; break;                  // with this until it looks good
                case 4:   pix = 0x0F00; break;
                default:  pix = 0x0000; break;
            }
            if (pix > 0) rend->drawPixel((x/2), (y/2), pix);    // on non-zero, draw the downsampled pixel
        }
    }
}

// Copy the downsized rendering buffer to the screen and add attribution
void draw_copy (uint32_t a) {
    tft.fillScreen(0x0000);                                         // erase the old stuff
    tft.drawRGBBitmap(off_x, off_y, rend->getBuffer(), ddx, ddy);   // copy the render canvas to the screen
    tft.setCursor(attr_x, attr_y);                                  // set the cursor for the attribution text
    tft.setTextColor(0x07E0, 0x0000);                               // set text color to med. green (black background)
    tft.print(a);                                                   // draw the sample attribution text
}

// Delete the off-screen drawing areas
void draw_delete (void) {
    if (rend) { delete rend; rend = 0; }
    if (dest) { delete dest; dest = 0; }
    if (src)  { delete src;  src  = 0; }
}

void setup() {
    uint32_t t0 = millis();                             // starting time
    draw_init();                                        // initialize the off-screen canvases
    tft.println("rendering text...");   draw_text();    // draw the text to the first canvas
    tft.println("warping...");          draw_warp();    // warp the text from the first to the second canvas
    tft.println("downsampling...");     draw_down();    // downsize the warp to the rendering canvas and colorize
    draw_copy(millis() - t0);                           // copy the downsized rendering buffer to the screen
    draw_delete();
}

void loop() {
  delay(100);
}


