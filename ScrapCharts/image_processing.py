from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


lookup: dict = {
        '401': {
            'angle': 18,
            'crop': (460, 750, 3750, 1500),
            'scale': 0.5
        },
        'L4L1': {
            'angle': 18,
            'crop': (450, 460, 1380, 2000),
            'scale': 0.98
        },
        '501': {
            'angle': 72,
            'crop': (970, 1930, 5133, 2620),
            'scale': 0.5
        },
    }


def straighten(image: Image, angle: int) -> Image:
    if not hasattr(Image, 'Resampling'):  # Pillow<9.0
        Image.Resampling = Image
    return image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=None)


def cropping(image: Image, crop: tuple[int, int, int, int]) -> Image:
    """ crop -> (left, top, right, bottom) """
    return image.crop(crop)


def legend(image: Image, _text: str) -> Image:
    font = ImageFont.truetype("arial.ttf", 48)
    draw = ImageDraw.Draw(image)
    draw.text((25, 25), _text, (245, 235, 8), font=font)
    return image


def pipeline(input_path: str,
             angle: int,
             crop_values: tuple[int, int, int, int],
             scaling: bool,
             scale: float,
             rotate: bool,
             crop: bool,
             draw: bool) -> Image:

    with Image.open(input_path) as img:
        result_image: Image = img.copy()

        if scaling:
            try:
                new_width = int(result_image.width * scale)
                new_height = int(result_image.height * scale)
                result_image = result_image.resize((new_width, new_height), Image.ANTIALIAS)
            except Exception as e:
                print(f'Scaling error: {e}')

        if rotate:
            try:
                result_image: Image = straighten(result_image, angle)
                print(f"Image straightened by {angle:.2f} degrees")
            except Exception as e:
                print(f'Rotate error: {e}')

        if crop:
            try:
                result_image: Image = cropping(result_image, crop_values)
                print(f"Image cropped by: {crop_values}")
            except Exception as e:
                print(f'Crop Error: {e}')

        if draw:
            try:
                result_image: Image = legend(result_image, '')
                print(f'Image drawn')
            except Exception as e:
                print(f'Draw error: {e}')

    return result_image
