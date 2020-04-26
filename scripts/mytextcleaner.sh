#!/bin/bash
FILENAME=$1

echo "Input file: $1"

# Remove dithering
convert $FILENAME -colorspace Gray 0_grayscale.tiff
convert 0_grayscale.tiff -normalize -auto-level 0_normalized.tiff
convert 0_normalized.tiff -kuwahara 1 0_kuwahara.tiff
convert 0_kuwahara.tiff -lat 35x35-5% 1_lat.tiff

# Remove shadows and scratches
convert 1_lat.tiff -negate -morphology Erode Diamond:1 -negate 2_erode.tiff
convert 2_erode.tiff -statistic median 3x3 4_median.tiff
convert 4_median.tiff -motion-blur 30x15+0 5_mblur.tiff
convert 5_mblur.tiff -gaussian-blur 25x10 5_gblur.tiff
convert 5_gblur.tiff -auto-threshold OTSU 6_otsu.tiff
convert 6_otsu.tiff -negate -morphology Dilate Octagon:15 -negate 7_dilate.tiff
convert 1_lat.tiff \( -clone 0 -fill white -colorize 100% \) 7_dilate.tiff -compose over -composite 6_clean.tiff

# Remove scratches from lines
convert 6_clean.tiff -morphology Smooth Disk:1 7_smoothed.tiff
convert 7_smoothed.tiff -statistic median 3x3 8_median.tiff
convert 8_median.tiff -auto-threshold OTSU 9_otsu.tiff
convert 9_otsu.tiff -define connected-components:area-threshold=15 -connected-components 8 -threshold 0 -negate 10_connected.tiff
convert 10_connected.tiff -gaussian-blur 5x2 11_blur.tiff
convert 11_blur.tiff -auto-threshold OTSU 12_otsu.tiff
convert 6_clean.tiff \( -clone 0 -fill white -colorize 100% \) 12_otsu.tiff -compose over -composite 13_clean.tiff
convert 13_clean.tiff -auto-threshold OTSU 14_otsu.tiff
convert 14_otsu.tiff -morphology Smooth Disk:1 15_smoothed.tiff