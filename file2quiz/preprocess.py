import os

from file2quiz import utils

import numpy as np
from scipy.ndimage import interpolation as inter

from skimage import filters
from skimage import img_as_ubyte
from skimage.color import rgb2gray
from skimage import exposure
from skimage import io

from PIL import Image
from deskew import determine_skew


def preprocess_img_file(filename, savepath, crop=None, dpi=300, *args, **kwargs):
    # Read image
    img = imread(filename)

    # Pre-process image
    img = image_cleaner(img, crop=crop, **kwargs)

    # Save image
    imsave(img, savepath, dpi=dpi)
    return savepath


def image_cleaner(img, crop=None, deskew=False, **kwargs):
    # Crop
    if crop:
        crop_h, crop_w = crop
        img = img[crop_h:-crop_h, crop_w:-crop_w]

    # Convert to grayscale
    img = rgb2gray(img)

    # Normalize
    img = normalize(img)

    # Noise removal
    img = noise_removal(img)

    # Threshold
    img = binarize(img)

    # De-rotate (deskew)
    if deskew:
        img = skew_rotation(img)
    return img


def binarize(img, window_size=35):
    thresh = filters.threshold_sauvola(img, window_size)
    img = img > thresh
    img = np.array(img * 255, dtype=np.uint8)
    return img


def normalize(img):
    img = exposure.equalize_adapthist(img, clip_limit=0.03)
    img = np.array(img * 255, dtype=np.uint8)
    return img


def noise_removal(img, window_size=3):
    # import cv2
    #
    # # Denoising
    # cv_image = img_as_ubyte(img)
    # img = cv2.fastNlMeansDenoising(cv_image, None, window_size, 7, 21)

    # Median filtering
    img = filters.median(img)
    return img


def get_angle_text(img, method="hough", limit=5.0, step=1.0):
    if method == "hough":
        angle = determine_skew(img)
        if abs(angle) >= 90:  # Vertical lines detected
            angle = angle % 90
            angle -= 90
        if abs(angle) > 5:
            print("\t- [WARNING] Ignoring rotation. Maximum angle exceeded ({:.2f}º > +-{:2.f}º)".format(angle, limit))
            angle = 0.0
        return angle
    elif method == "projection":
        # Find rotation angle
        angles = np.arange(-limit, limit + step, step)
        scores = []
        for angle in angles:
            hist, score = find_score(img, angle)
            scores.append(score)
        best_score = max(scores)
        best_angle = angles[scores.index(best_score)]
        return best_angle


def skew_rotation(img, fillcolor='white', orientation='portrait'):
    # Rotate if needed
    h, w = img.shape
    if (orientation == "portrait" and h < w) or (orientation == "landscape" and h > w):
        img = img.T

    angle = get_angle_text(img, method="hough")
    print("\t- [INFO] Rotating image: {:.2f}º".format(angle))

    # Rotate and add custom background
    img = Image.fromarray(img)
    img = img.rotate(angle, resample=Image.BICUBIC, fillcolor=fillcolor)
    img = np.array(img)
    return img


def find_score(arr, angle):
    data = inter.rotate(arr, angle, reshape=False, order=0)
    hist = np.sum(data, axis=1)
    score = np.sum((hist[1:] - hist[:-1]) ** 2)
    return hist, score


def imread(filename):
    return io.imread(filename)


def imsave(img, savepath, dpi=300):
    img = Image.fromarray(img)
    img.save(savepath, dpi=(dpi, dpi))
