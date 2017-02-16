import cv2
import util
import imutils
import numpy as np
from imutils.object_detection import non_max_suppression

def get_boxes(gray, template, scales=5, template_threshold=0.5, nms_threshold=0.2):
    w, h = gray.shape[::-1]
    t_w, t_h = template.shape[::-1]
    boxes = np.zeros([0,4])

    for scale in np.linspace(0.2, 1.0, scales)[::-1]:
        resized = imutils.resize(gray, width=int(w * scale))
        ratio = w / float(resized.shape[1])
        
        if resized.shape[0] < t_h or resized.shape[1] < t_w:
            break
        
        edged = util.template_preprocess(resized)
        res = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF_NORMED)
        div = res.shape[1]
        res = res.reshape(-1)
        inds = res.argsort()[::-1]
        n = np.sum(res[inds] > template_threshold)
        inds = inds[:n]
        scale_boxes = np.zeros([n, 4])
        scale_boxes[:, 0] = np.floor(inds / div)
        scale_boxes[:, 1] = inds % div
        scale_boxes[:, 2] = scale_boxes[:, 0] + t_w
        scale_boxes[:, 3] = scale_boxes[:, 1] + t_h
        scale_boxes = np.asarray(scale_boxes * ratio, dtype=np.int)
        boxes = np.vstack((boxes, scale_boxes))
        
    boxes = np.asarray(boxes, dtype=np.int)
    boxes[:, 2][boxes[:, 2] > w] = w
    boxes[:, 3][boxes[:, 3] > h] = h
    boxes = non_max_suppression(boxes, overlapThresh=nms_threshold)

    return boxes

def get_n_boxes(gray, templates, scales=3, template_threshold=0.8, nms_threshold=0.1,
                min_area_r=0.1):
    w, h = gray.shape[::-1]
    min_area = int(w * h * min_area_r**2)
    boxes = np.zeros([0,5])

    for file in templates:
        template = np.load(file)
        t_w, t_h = template.shape[::-1]

        for scale in np.linspace(0.5, 1.0, scales)[::-1]:
            resized = imutils.resize(gray, width=int(w * scale))
            ratio = w / float(resized.shape[1])
            
            if resized.shape[0] < t_h or resized.shape[1] < t_w:
                break
            
            edged = util.template_preprocess(resized)
            res = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF_NORMED)
            div = res.shape[1]
            res = res.reshape(-1)
            inds = res.argsort()[::-1]
            n = np.sum(res[inds] > template_threshold)
            inds = inds[:n]
            scale_boxes = np.zeros([n, 5])
            scale_boxes[:, 0] = np.floor(inds / div)
            scale_boxes[:, 1] = inds % div
            scale_boxes[:, 2] = scale_boxes[:, 0] + t_w
            scale_boxes[:, 3] = scale_boxes[:, 1] + t_h
            scale_boxes = np.asarray(scale_boxes * ratio)
            scale_boxes[:, 4] = res[inds]
            boxes = np.vstack((boxes, scale_boxes))
    
    probs = boxes[:, 4]
    boxes = np.asarray(boxes[:, :4], dtype=np.int)
    boxes[:, 0][boxes[:, 0] < 0] = 0
    boxes[:, 0][boxes[:, 0] > w] = w
    boxes[:, 1][boxes[:, 1] < 0] = 0
    boxes[:, 1][boxes[:, 1] > h] = h
    boxes[:, 2][boxes[:, 2] < 0] = 0
    boxes[:, 2][boxes[:, 2] > w] = w
    boxes[:, 3][boxes[:, 3] < 0] = 0
    boxes[:, 3][boxes[:, 3] > h] = h

    area = abs((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1]))
    boxes = boxes[area >= min_area]
    probs = probs[area >= min_area]

    boxes = non_max_suppression(boxes, probs=probs, overlapThresh=nms_threshold)

    if len(boxes) > 5:
        boxes = boxes[:5, :]

    return boxes
