import cv2

def template_preprocess(image):
    template = cv2.GaussianBlur(image, (11, 11), 0)
    
    return template

def print_cwd(wd):
    out = 'Current directory: [%s]' % wd
    print('-' * len(out))
    print(out)
    print('-' * len(out))

def whboxes2xyboxes(x, y, w, h):
    x1 = x - int(w / 2)
    y1 = y - int(h / 2)
    x2 = x + int(w / 2)
    y2 = y + int(h / 2)

    return x1, y1, x2, y2

def xyboxes2whboxes(x1, y1, x2, y2):
    w = x2 - x1
    h = y2 - y1
    x = x1 + int(w / 2)
    y = y1 + int(h / 2)
    
    return x, y, w, h