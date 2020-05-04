import os

from file2quiz import utils

import numpy as np
from scipy.ndimage import interpolation as inter

from skimage import filters
from skimage import img_as_ubyte
from skimage.color import rgb2gray
from skimage import exposure, morphology, io

from PIL import Image, ImageFilter
from deskew import determine_skew
import cv2


def preprocess_img_file(filename, savepath, page_i, crop=None, dpi=300, unpaper_args="", layout="single", *args, **kwargs):
    head, tail = utils.get_tail(savepath)
    fname, ext = utils.get_fname(head)

    # Read image
    #img = imread(filename)

    # Pre-process image
    # try:
    #     img = image_cleaner(img, crop=crop, **kwargs)
    # except ValueError as e:
    #     pass
    # # Save image
    # imsave(img, savepath, dpi=dpi)

    # Basic preprocessing
    # savepath_tmp1 = f"{tail}/{fname}.pgm"
    # program = os.path.abspath(os.path.join("../scripts/mytextcleaner.sh"))
    # cmd = f"{program} {filename} {savepath_tmp1}"
    # os.system(cmd)

    # Unpaper preprocessing
    savepath_tmp = f"{savepath}/{fname}_page{page_i}_%d.pgm"
    cmd = f'unpaper --overwrite {unpaper_args} "{filename}" "{savepath_tmp}"'
    os.system(cmd)


def image_cleaner(img, crop=None, deskew=False, **kwargs):
    # Crop
    if crop:
        crop_h, crop_w = crop
        img = img[crop_h:-crop_h, crop_w:-crop_w]

    # Convert to grayscale
    if img.ndim == 3:
        img = rgb2gray(img)
        img = np.array(img * 255, dtype=np.uint8)
    # Image.fromarray(img).show()

    # Normalize
    img = normalize(img)
    # Image.fromarray(img).show()

    # Noise removal
    img = noise_removal(img)
    # Image.fromarray(img).show()

    # Threshold
    img = binarize(img)
    # Image.fromarray(img).show()

    # Enhancements
    img = enhancements(img)
    # Image.fromarray(img).show()

    # De-rotate (deskew)
    if deskew:
        img = skew_rotation(img)
    return img


def binarize(img, window_size=35):
    # cv_image = img_as_ubyte(img)
    # img = cv2.adaptiveThreshold(cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, window_size, 0)

    thresh = filters.threshold_sauvola(img, window_size)
    img = img > thresh
    img = np.array(img * 255, dtype=np.uint8)
    return img


def normalize(img):
    img = exposure.equalize_adapthist(img, clip_limit=0.03)
    img = np.array(img * 255, dtype=np.uint8)
    return img


def noise_removal(img, window_size=25):
    # img = filters.gaussian(img)
    # img = np.array(img * 255, dtype=np.uint8)

    # Denoising
    cv_image = img_as_ubyte(img)
    img = cv2.fastNlMeansDenoising(cv_image, None, window_size, 7, 21)

    # # Median filtering
    # img = filters.median(img)
    return img


def enhancements(img):
    # # Thin elements
    # structure = morphology.disk(radius=3)
    # img = morphology.binary_closing(img, selem=structure)

    # Remove small objects
    # img = np.array(img, dtype=np.bool)
    # img = morphology.remove_small_objects(img, min_size=5**2)

    # # Remove small holes
    # img = morphology.remove_small_holes(img, area_threshold=3**2)
    # img = np.array(img * 255, dtype=np.uint8)

    # Median & blur filter
    img = Image.fromarray(img)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img = np.array(img)

    # Apply otsu
    thres = filters.threshold_otsu(img)
    img = img > thres
    img = np.array(img * 255, dtype=np.uint8)
    return img


def get_angle_text(img, method="hough", limit=5.0, step=1.0):
    if method == "hough":
        angle = determine_skew(img)
        if abs(angle) >= 90:  # Vertical lines detected
            angle = angle % 90
            angle -= 90
        if abs(angle) > 5:
            print("\t- [WARNING] Ignoring rotation. Maximum angle exceeded ({:.2f}º > +-{:.2f}º)".format(angle, limit))
            angle = 0.0
        return angle
    elif method == "projection":
        # Find rotation angle
        angles = np.arange(-limit, limit + step, step)
        scores = []
        scores = []
        for angle in angles:
            hist, score = find_score(img, angle)
            scores.append(score)
        best_score = max(scores)
        best_angle = angles[scores.index(best_score)]
    else:
        raise NameError("Unknown method")
    return best_angle


def skew_rotation(img, fillcolor='white', orientation='portrait'):
    # Rotate if needed
    h, w = img.shape[0], img.shape[1]
    if (orientation == "portrait" and h < w) or (orientation == "landscape" and h > w):
        img = img.T

    angle = get_angle_text(img)
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
