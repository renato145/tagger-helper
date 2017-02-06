import os
import re
import cv2
import json

WINDOW_TITLE = 'Tagger Helper :)'
VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tiff']
SLIDE = 10
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
Save box           : f
Reset box          : r
Next image         : n
Previous image     : b

Exit               : x
---------------------------
'''

def print_cwd(wd):
    out = 'Current directory: [%s]' % wd
    print('-' * len(out))
    print(out)
    print('-' * len(out))

def draw_text(img, text, size=0.5, width=2):
    img = cv2.putText(img, text, (200, 200), cv2.FONT_HERSHEY_SIMPLEX,
                      size, (0, 0, 0), width * 2)
    img = cv2.putText(img, text, (200, 200), cv2.FONT_HERSHEY_SIMPLEX,
                      size, (255, 255, 255), width)

    return img

def load_data(file):
    if os.path.exists(file):
        with open(file) as f:
            data = json.load(f)
        return data['box']
    else:
        return

def save_data(file, label, box):
    out_data = {}
    out_data['label'] = label
    out_data['box'] = box
    with open(file, 'w') as f:
        json.dump(out_data, f)

def main():
    # Get folder
    cwd = os.path.realpath('.')
    print(DIALOG)
    print_cwd(cwd)
    print(DIALOG_INPUT_PATH)

    while True:
        path = input('>> ')
        if os.path.exists(path):
            cwd = os.path.realpath(path)
            print_cwd(cwd)
            break
        else:
            print('--INVALID PATH--')

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
            if os.path.exists('%s.json' % files[i].split('.')[0]):
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
    slide = SLIDE
    change_factor = CHANGE_FACTOR
    height, width, _ = image.shape
    start_x = round(2 * width / 5 / slide) * slide
    start_y = round(2 * height / 5 / slide) * slide
    end_x = round(3 * width / 5 / slide) * slide
    end_y = round(3 * height / 5 / slide) * slide

    while True:
        json_file = '%s.json' % file.split('.')[0]
        image =  orig.copy()

        # check json file
        if not load_flag:
            temp_box = load_data(json_file)
            if temp_box is not None:
                start_x, start_y, end_x, end_y = temp_box
                load_flag = True

        cv2.rectangle(image, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        cv2.imshow(WINDOW_TITLE, image)
        key = cv2.waitKey()
        # print(key)

        # save 
        if key == ord('f'):
            confirm_save = image.copy()
            save_data(json_file, label, (start_x, start_y, end_x, end_y))
            if not load_saved_files:
                del(files[index])
                if index > 0:
                    index -= 1

            draw_text(confirm_save, DIALOG_SAVE % json_file)
            cv2.imshow(WINDOW_TITLE, confirm_save)
            cv2.waitKey()

            if index == len(files) - 1:
                index = 0
            else:
                index += 1
            
            file = files[index]
            orig = cv2.imread(file)

        # move up on arrow up
        elif key == 82:
            start_y -= change_factor
            end_y -= change_factor

        # move down on arrow down
        elif key == 84:
            start_y += change_factor
            end_y += change_factor

        # move left on arrow left
        elif key == 81:
            start_x -= change_factor
            end_x -= change_factor

        # move right on arrow right
        elif key == 83:
            start_x += change_factor
            end_x += change_factor
        
        # increase width
        elif key == ord('d'):
            start_x -= change_factor
            end_x += change_factor

        # decrease width
        elif key == ord('a'):
            start_x += change_factor
            end_x -= change_factor

        # increase height
        elif key == ord('w'):
            start_y -= change_factor
            end_y += change_factor

        # decrease height
        elif key == ord('s'):
            start_y += change_factor
            end_y -= change_factor

        # increase change_factor
        elif key == ord('e'):
            change_factor += 1

        # decrease change_factor
        elif key == ord('q') and change_factor > 1:
            change_factor -= 1

        # reset settings
        elif key == ord('r'):
            slide = SLIDE
            change_factor = CHANGE_FACTOR
            height, width, _ = image.shape
            start_x = round(2 * width / 5 / slide) * slide
            start_y = round(2 * height / 5 / slide) * slide
            end_x = round(3 * width / 5 / slide) * slide
            end_y = round(3 * height / 5 / slide) * slide

        # load next file
        elif key == ord('n'):
            if index == len(files) - 1:
                index = 0
            else:
                index += 1
            
            file = files[index]
            orig = cv2.imread(file)
            load_flag = False

        # load previous file
        elif key == ord('b'):
            if index == 0:
                index = len(files) - 1
            else:
                index -= 1
            
            file = files[index]
            orig = cv2.imread(file)
            load_flag = False

        # Close
        elif key == ord('x'):
            confirm_exit = image.copy()
            draw_text(confirm_exit, DIALOG_EXIT, 2, 5)
            cv2.imshow(WINDOW_TITLE, confirm_exit)
            key = cv2.waitKey()

            if key == ord('y'):
                break

if __name__ == '__main__':
    main()
