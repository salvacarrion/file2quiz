import os

import file2quiz
from file2quiz import preprocess


if __name__ == "__main__":
    input_dir = "/Users/salvacarrion/Desktop/raw_images"
    output_dir = "/Users/salvacarrion/Desktop/processed"
    dpi = 300
    crop = (250, 200)
    EXTENSIONS = {".jpg", ".tiff", ".png"}

    # Get files
    files = file2quiz.get_files(input_dir, extensions=EXTENSIONS)
    for i, filename in enumerate(files, 1):
        fname, ext = file2quiz.get_fname(filename)

        # Build paths
        filename = os.path.abspath(os.path.join(input_dir, filename))
        savepath = os.path.abspath(os.path.join(output_dir, f"{fname}_new.tiff"))

        # Check format
        if ext in EXTENSIONS:
            print(f"- [{i}/{len(files)}] Pre-processing image... ({filename})")

            # Read image
            img = preprocess.imread(filename)

            # Pre-process image
            img = preprocess.image_cleaner(img, crop=crop)

            # Save image
            img = preprocess.imsave(img, savepath, dpi=dpi)
            print(f"\t- Image saved! ({savepath})")

    print("Done!")
