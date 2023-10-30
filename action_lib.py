from typing import Callable


def show_artsy_image():
    # TODO: implement a simple function to pick a random image out of a
    # a pre-defined list of images in the assets folder.
    # Make sure to return something you can embed to the chat window, e.g. HTML.
    raise NotImplementedError(f'')


def show_dalle_image():
    # TODO: make a call to Dalle to generate an image
    raise NotImplementedError(f'')


def show_image(impl: str) -> str:
    if impl == 'show artsy image':
        return show_artsy_image()
    elif impl == 'dalle':
        return show_dalle_image()
    else:
        # default to something
        return show_artsy_image()