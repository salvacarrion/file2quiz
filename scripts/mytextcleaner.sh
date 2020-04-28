#!/bin/bash
FILENAME=$1
OUTPUT=$2
TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")


#echo "Input file: $1"
#echo "Output file: $2"
#echo "Temp dir: $TEMP_DIR"

# Remove dithering
convert $FILENAME -colorspace Gray $TEMP_DIR/0_grayscale.tiff
convert $TEMP_DIR/0_grayscale.tiff -normalize -auto-level $TEMP_DIR/0_normalized.tiff
convert $TEMP_DIR/0_normalized.tiff -kuwahara 1 $TEMP_DIR/0_kuwahara.tiff
convert $TEMP_DIR/0_kuwahara.tiff -lat 40x40-5% $TEMP_DIR/1_lat.tiff

# Remove shadows and scratches
#convert $TEMP_DIR/1_lat.tiff -negate -morphology Erode Diamond:1 -negate $TEMP_DIR/2_erode.tiff
convert $TEMP_DIR/1_lat.tiff -statistic median 3x3 $TEMP_DIR/4_median.tiff
# convert 4_median.tiff -motion-blur 30x15+0 $TEMP_DIR/5_mblur.tiff
convert $TEMP_DIR/4_median.tiff -gaussian-blur 15x5 $TEMP_DIR/5_gblur.tiff
convert $TEMP_DIR/5_gblur.tiff -auto-threshold OTSU $TEMP_DIR/6_otsu.tiff
convert $TEMP_DIR/6_otsu.tiff -negate -morphology Dilate Octagon:20 -negate $TEMP_DIR/7_dilate.tiff
convert $TEMP_DIR/1_lat.tiff \( -clone 0 -fill white -colorize 100% \) $TEMP_DIR/7_dilate.tiff -compose over -composite $OUTPUT

# Remove scratches from lines
# convert $TEMP_DIR/8_clean.tiff -morphology Smooth Disk:1 $TEMP_DIR/9_smoothed.tiff
#convert $TEMP_DIR/7_smoothed.tiff -statistic median 3x3 $TEMP_DIR/8_median.tiff
#convert $TEMP_DIR/7_smoothed.tiff -auto-threshold OTSU $TEMP_DIR/9_otsu.tiff
# convert $TEMP_DIR/9_smoothed.tiff -define connected-components:area-threshold=15 -connected-components 8 -threshold 0 -negate $TEMP_DIR/10_connected.tiff
# convert $TEMP_DIR/10_connected.tiff -gaussian-blur 4x2 $TEMP_DIR/11_blur.tiff
# convert $TEMP_DIR/11_blur.tiff -auto-threshold OTSU $TEMP_DIR/12_otsu.tiff
# convert $TEMP_DIR/8_clean.tiff \( -clone 0 -fill white -colorize 100% \) $TEMP_DIR/12_otsu.tiff -compose over -composite $TEMP_DIR/13_clean.tiff
# convert $TEMP_DIR/13_clean.tiff -auto-threshold OTSU $OUTPUT
# convert 14_otsu.tiff -morphology Smooth Disk:1 $OUTPUT

# rm 0_grayscale.tiff 0_normalized.tiff 0_kuwahara.tiff 1_lat.tiff
# rm 2_erode.tiff 4_median.tiff 5_gblur.tiff 6_otsu.tiff 7_dilate.tiff 8_clean.tiff
# rm 9_smoothed.tiff 10_connected.tiff 11_blur.tiff 12_otsu.tiff 13_clean.tiff
