#!/bin/bash
FILENAME=$1

echo "Input file: $1"

convert $FILENAME -kuwahara 3 1_kuwahara.tiff
convert 1_kuwahara.tiff -lat 35x35-25% 2_lat.tiff
convert 2_lat.tiff -morphology Smooth Disk:1 3_smoothed.tiff  
convert 3_smoothed.tiff -auto-threshold OTSU 4_otsu.tiff
convert 4_otsu.tiff -define connected-components:area-threshold=50 -connected-components 4 -threshold 0 -negate 5_connected.tiff
convert 3_smoothed.tiff 5_connected.tiff -compose minus -composite 6_diff.tiff
convert 3_smoothed.tiff \( -clone 0 -fill white -colorize 100% \) 6_diff.tiff -compose over -composite 7_clean.tiff
convert 7_clean.tiff -auto-threshold OTSU 8_clean_otsu.tiff
convert 8_clean_otsu.tiff -morphology Smooth Disk:1 9_smooth.tiff
convert 9_smooth.tiff -statistic median 3x3 10_median.tiff
convert 10_median.tiff -morphology Smooth Disk:1 11_smoothed.tiff  
convert 11_smoothed.tiff -shave 200x350 12_shaved.tiff
convert 12_shaved.tiff -flatten -fuzz 5% -trim +repage 13_trimmed.tiff
convert 13_trimmed.tiff -bordercolor white -border 20 14_wb.tiff
convert 14_wb.tiff -bordercolor black -border 1 15_bb.tiff
convert 15_bb.tiff -units PixelsPerInch -density 300 final.tiff