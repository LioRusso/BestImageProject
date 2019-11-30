# BestImageProject

Description:

"Best Image" = The image where the bounding box of the face is largest in relation to the size of the image.

Input - JSON over http
* List of images - "Image" means a local filename (no need for a URL).

Output - JSON over http
* Face metadata from azure, based on the "best image" decision above.
* Filename of the "best image".

Assumptions:

Images size is between 1KB and 6MB.
