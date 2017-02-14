import os
import re
import cv2
import json
import util
import template_match
import numpy as np

WINDOW_TITLE = 'Tagger Helper :)'
VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tiff']
CHANGE_FACTOR = 5
DIALOG = '''
Remember:
Path folder name should be the name of the class.
A file will be saved with then name IMG_NAME.json.
'''
DIALOG_INPUT_PATH = 'Input data path.'
DIALOG_EXIT = 'Really want to exit (y)?'
DIALOG_SAVE = 'File saved on: %s'
INSTRUCTIONS ='''---------------------------
Move box           : arrows
Change box size    : wasd
Change slider size : qe

Previous box       : z
Delete box         : x
Next box           : c

Reset boxes        : r
Save boxes         : f
Draw suggestions   : v

Previous image     : b
Next image         : n

Exit               : escape
---------------------------
'''

class TaggerHelper(object):
    
    def __init__(self):
        self.boxes = []
        self.box_idx = -1
        self.window_title = WINDOW_TITLE
        self.run_window(WINDOW_TITLE)

    def keep_one_box(self):
        x = self.boxes[self.box_idx]['x']
        y = self.boxes[self.box_idx]['y']
        w = self.boxes[self.box_idx]['w']
        h = self.boxes[self.box_idx]['h']
        self.reset_boxes(x, y, w, h)

    def reset_boxes(self, x, y, w, h):
        self.boxes = []
        self.create_box(x, y, w, h)

    def create_box(self, x, y, w, h):
        box = {'x': x, 'y': y, 'w': w, 'h': h}
        self.boxes.append(box)
        self.box_idx = len(self.boxes) - 1

    def set_box(self, x, y, w, h):
        box = {'x': x, 'y': y, 'w': w, 'h': h}
        self.boxes[self.box_idx] = box

    def click_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.boxes[self.box_idx]['x'] = x
            self.boxes[self.box_idx]['y'] = y
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.create_box(x, y, self.boxes[self.box_idx]['w'], self.boxes[self.box_idx]['h'])

    def draw_text(self, img, text, size=0.5, width=2):
        img = cv2.putText(img, text, (200, 200), cv2.FONT_HERSHEY_SIMPLEX,
                          size, (0, 0, 0), width * 2)
        img = cv2.putText(img, text, (200, 200), cv2.FONT_HERSHEY_SIMPLEX,
                          size, (255, 255, 255), width)

    def load_data(self, file):
        if os.path.exists(file):
            with open(file) as f:
                data = json.load(f)
            
            self.boxes = data['boxes']
            self.box_idx = len(self.boxes) - 1

    def save_data(self, image, json_file, label, boxes):
        # save json
        out_data = {}
        out_data['label'] = label
        out_data['boxes'] = boxes
        with open(json_file, 'w') as f:
            json.dump(out_data, f)

        # delete current templates
        template_prename = '%s_template_' % json_file.split('.')[0]
        rm_files = (os.path.join(self.cwd, f) for f in os.listdir(self.cwd)
                    if f.find(os.path.basename(template_prename)) > -1)
        for rm_file in rm_files:
            os.remove(rm_file)

        # save template: file_template_i.npy
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = util.whboxes2xyboxes(box['x'], box['y'], box['w'], box['h'])
            template = gray[y1:y2, x1:x2].copy()
            template = util.template_preprocess(template)
            np.save('%s%d.npy' % (template_prename, i), template)


    def load_suggestions(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template_files = [os.path.join(self.cwd, f) for f in os.listdir(self.cwd)
                          if f.find('_template_') > -1]
        
        if len(template_files) == 0:
            return

        n = min(5, len(template_files))
        template_files = np.random.choice(template_files, n, replace=False)
        
        for template_file in template_files:
            template = np.load(template_file)
            template = np.asarray(template)
            boxes = template_match.get_boxes(gray, template)
            for box in boxes:
                wh_box = util.xyboxes2whboxes(*box)
                self.create_box(*wh_box)


    def correct_box(self):
        if self.boxes[self.box_idx]['x'] < 0:
            self.boxes[self.box_idx]['x'] = 0

        if self.boxes[self.box_idx]['y'] < 0:
            self.boxes[self.box_idx]['y'] = 0

        if self.boxes[self.box_idx]['w'] < 0:
            self.boxes[self.box_idx]['w'] = abs(self.boxes[self.box_idx]['w'])

        if self.boxes[self.box_idx]['h'] < 0:
            self.boxes[self.box_idx]['h'] = abs(self.boxes[self.box_idx]['h'])

    def draw_boxes(self, image):
        for i, box in enumerate(self.boxes):
            x1, y1, x2, y2 = util.whboxes2xyboxes(box['x'], box['y'], box['w'], box['h'])
            color = (0, 255, 0) if i == self.box_idx else (150, 0, 0)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

    def run_window(self, window_title):
        cwd = os.path.realpath('.')
        print(DIALOG)
        util.print_cwd(cwd)
        print(DIALOG_INPUT_PATH)

        while True:
            path = input('>> ')
            if os.path.exists(path):
                cwd = os.path.realpath(path)
                util.print_cwd(cwd)
                break
            else:
                print('--INVALID PATH--')

        self.cwd = cwd

        # Get files and label
        label = os.path.basename(cwd)
        valid_extensions = '|'.join(VALID_EXTENSIONS)
        files = [os.path.join(cwd, file) for file in os.listdir(cwd)
                 if re.search(valid_extensions, file.lower())]
        files.sort()

        # Check saved files
        load_saved_files = False

        load_options = input('Load saved files y/n? [n]\n')
        if load_options.lower() == 'y':
            load_saved_files = True

        if not load_saved_files:
            i = 0
            while i < len(files):
                if os.path.exists(files[i].split('.')[0]):
                    del(files[i])
                else:
                    i += 1

        # Check number of files            
        if len(files) == 0:
            print('No files found.')
            quit()

        print('%d files founded for label %s.' % (len(files), label))

        # Start
        print('')
        input('Press Enter to start.')
        print(INSTRUCTIONS)

        index = 0
        load_flag = False
        file = files[index]
        image = cv2.imread(file)
        orig = image.copy()
        change_factor = CHANGE_FACTOR
        height, width, _ = image.shape
        img_x = round(width / 2)
        img_y = round(height / 2)
        img_w = round(width * 0.1) * 2
        img_h = round(height * 0.1) * 2
        self.create_box(img_x, img_y, img_w, img_h)

        cv2.namedWindow(window_title)
        cv2.setMouseCallback(window_title, self.click_event)

        while True:
            json_file = '%s.json' % file.split('.')[0]
            image =  orig.copy()

            # check json file
            if not load_flag:
                self.load_data(json_file)
                load_flag = True

            # draw rectanle
            self.draw_boxes(image)
            cv2.imshow(window_title, image)
            key = cv2.waitKey(1)
            # print(key)

            # save 
            if key == ord('f'):
                confirm_save = image.copy()
                self.save_data(orig, json_file, label, self.boxes)
                if not load_saved_files:
                    del(files[index])
                if index > 0:
                    index -= 1

                self.draw_text(confirm_save, DIALOG_SAVE % json_file)
                cv2.imshow(window_title, confirm_save)
                cv2.waitKey(500)

            # draw suggestions
            elif key == ord('v'):
                self.load_suggestions(orig)

            # move up on arrow up
            elif key == 82:
                self.boxes[self.box_idx]['y'] -= change_factor

            # move down on arrow down
            elif key == 84:
                self.boxes[self.box_idx]['y'] += change_factor

            # move left on arrow left
            elif key == 81:
                self.boxes[self.box_idx]['x'] -= change_factor

            # move right on arrow right
            elif key == 83:
                self.boxes[self.box_idx]['x'] += change_factor
            
            # increase width
            elif key == ord('d'):
                self.boxes[self.box_idx]['w'] += change_factor * 2

            # decrease width
            elif key == ord('a'):
                self.boxes[self.box_idx]['w'] -= change_factor * 2

            # increase height
            elif key == ord('w'):
                self.boxes[self.box_idx]['h'] += change_factor * 2

            # decrease height
            elif key == ord('s'):
                self.boxes[self.box_idx]['h'] -= change_factor * 2

            # increase change_factor
            elif key == ord('e'):
                change_factor += 1

            # decrease change_factor
            elif key == ord('q') and change_factor > 1:
                change_factor -= 1

            # reset settings
            elif key == ord('r'):
                change_factor = CHANGE_FACTOR
                height, width, _ = image.shape
                t_x = round(width / 2)
                t_y = round(height / 2)
                t_w = round(width * 0.1) * 2
                t_h = round(height * 0.1) * 2
                self.reset_boxes(t_x, t_y, t_w, t_h)

            # load previous file
            elif key == ord('b'):
                if index == 0:
                    index = len(files) - 1
                else:
                    index -= 1
                
                self.keep_one_box()
                file = files[index]
                orig = cv2.imread(file)
                load_flag = False

            # load next file
            elif key == ord('n'):
                if index == len(files) - 1:
                    index = 0
                else:
                    index += 1
                
                self.keep_one_box()
                file = files[index]
                orig = cv2.imread(file)
                load_flag = False

            # activate previous box
            elif key == ord('z'):
                if self.box_idx == 0:
                    self.box_idx = len(self.boxes) - 1
                else:
                    self.box_idx -= 1

            # activate next box
            elif key == ord('c'):
                if self.box_idx == len(self.boxes) - 1:
                    self.box_idx = 0
                else:
                    self.box_idx += 1

            # remove current box
            elif key == ord('x'):
                if len(self.boxes) > 1:
                    self.boxes.pop(self.box_idx)
                    self.box_idx = len(self.boxes) - 1

            # Close
            elif key == 27:
                confirm_exit = image.copy()
                self.draw_text(confirm_exit, DIALOG_EXIT, 2, 5)
                cv2.imshow(window_title, confirm_exit)
                key = cv2.waitKey()

                if key == ord('y'):
                    break

            self.correct_box()

if __name__ == '__main__':
    # main()
    app = TaggerHelper()
