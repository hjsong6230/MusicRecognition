import sys
import cv2
import numpy as np
import pickle

from collections import defaultdict

from Momr.OMR import TemplateProcessor
from Momr.OMR import TailDetector
from Momr.Tool import Image
from Momr.Objects.Stave import Stave
from Momr.Objects.Note import Note

COLOR = [(255,0,0), (0, 255, 0), (0, 0, 255),  (0, 255,255), (255, 0, 255), (120, 120, 120), (90, 180, 120), (10, 10, 10) ]
THRESHOLD = 0.7

def __check_coliision(x0, y0, x1, y1, w, h):
    target_corners = [x0, x0+w, y0, y0+h]
    new_points = [(x1,y1), (x1+w, y1), (x1, y1+h), (x1+w, y1+h)]
    for point in new_points:
        if target_corners[0] <= point[0] and point[0] <= target_corners[1]:
            if target_corners[2] <= point[1] and point[1] <= target_corners[3]:
                return True
    #print target_corners, x1, y1, w, h
    return False


def __match_template(image, templates, test, test_color):
    detected_symbols = []
    for index, note in enumerate(templates):
        if note is None: continue
        #Image.saveImage(session_id, "test"+ str(index) +".png", note)
        symbols = TemplateProcessor.detect_symbols(image, test, note, test_color[index])
        w, h = note.shape[::-1]
        prev = (0, 0)
        for x in sorted(symbols.keys(), key=lambda x: int(x)):
            for y in sorted(symbols[x].keys(), key=lambda y: int(y)):
                x = int(x)
                y = int(y)
                if not __check_coliision(prev[0], prev[1], x, y, w, h):
                    prev = (x, y)
                    detected_symbols.append(Note(x, y, index, w, h))
    return detected_symbols

def __process_tail_direction(detected_symbols, image, test):
    for symbol in detected_symbols:
        x = symbol.x
        y = symbol.y
        w = symbol.w
        h = symbol.h
        note_type = symbol.note_type

        #TemplateProcessor.remove_detected(img, int(y), int(x), w, h)
        if note_type == 0:
            cv2.rectangle(test, (x, y), (x + 10, y + 10),  (0, 0, 255), 1)
        elif note_type == 1:
            cv2.rectangle(test, (x, y), (x + 10, y + 10),  (255, 255, 0), 1)
        elif note_type == 2:
            cv2.rectangle(test, (x, y), (x + 10, y + 10),  (0, 255, 255), 1)
        elif note_type == 3:
            cv2.rectangle(test, (x, y), (x + 10, y + 10),  (255, 0, 255), 1)
        else:
            cv2.rectangle(test, (x, y), (x + 10, y + 10),  (255, 0, 0), 1)
        tail_type, tail_x, tail_y = TailDetector.find_tail_direction(image, x, y, w, h, test)

        symbol.tail_direction = tail_type
        symbol.tail_x = tail_x
        symbol.tail_y = tail_y
        #TailDetector.find_tail_type(img_copy, tail_type, tail_x, tail_y, int(x), int(y), w, h, img_rgb)
    return detected_symbols

def __allocate_note_to_stave(staves, detected_symbols):
    for symbol in detected_symbols:
        symbol_x = symbol.x
        symbol_y = symbol.y
        tail_direction = symbol.tail_direction
        current = staves[0]
        for stave in staves[1:]:
            stave_0_y_0 = current.y0
            stave_0_y_1 = current.y1
            stave_1_y_0 = stave.y0
            stave_1_y_1 = stave.y1
            #print symbol_x, symbol_y, stave_0_y_0, stave_0_y_1, stave_1_y_0, stave_1_y_1
            if symbol_y <= stave_0_y_1:
                break
            elif symbol_y > stave_0_y_1 and symbol_y < stave_1_y_0:
                if tail_direction == 0:
                    break
                else:
                    current = stave
                    break
            current = stave

        for index, stave_x_0 in enumerate(current.sections[:-1]):
            stave_x_1 = current.sections[index+1]
            if stave_x_0 <= symbol_x and symbol_x <= stave_x_1:
                break

        current.addNote(str(stave_x_0), symbol)

def __process_tail_type(staves, image, test):
    for stave in staves:
        for separator in stave.notes:
            for index, note in enumerate(stave.notes[separator]):
                if note.note_type> 1:
                    if index == (len(stave.notes[separator])-1):
                        keys = sorted(stave.notes.keys(), key= lambda x: int(x))
                        note.tail_type = TailDetector.find_tail_type(image, note, int(keys[-1]), stave.y1, test)
                    else:
                        next_note =  stave.notes[separator][index + 1]
                        note.tail_type = TailDetector.find_tail_type(image, note, next_note.tail_x, next_note.tail_y, test)

def __find_note_pitch(staves):
    for stave in staves:
        y0 = stave.y0
        y1 = stave.y1
        #print stave
        for section in stave.notes:
            #print '\t', section
            for note in stave.notes[section]:
                #print '\t\t', note.center(), stave.lines
                note_y = note.center()[1]
                for index, line in enumerate(stave.lines):
                    if index == (len(stave.lines) - 1):
                        pitchVar = index + (index + 1)
                        #print '\t\t\t', line[-1], note_y, "BLANK", pitchVar
                        note.setPitch(pitchVar)
                        break
                    elif index == 0 and note_y < line[-1]:
                        pitchVar = -1
                        #print '\t\t\t', line[-1], note_y, "BLANK", pitchVar
                        note.setPitch(pitchVar)
                        break
                    else:
                        if line[-1] <= note_y and note_y < stave.lines[index+1][-1]:
                            if note_y == line[-1]:
                                pitchVar = index * 2
                                #print '\t\t\t', line[-1], note_y, stave.lines[index+1][-1], pitchVar
                                note.setPitch(pitchVar)
                                break
                            else:
                                pitchVar = index + (index + 1)
                                #print '\t\t\t', line[-1], note_y, stave.lines[index+1][-1], pitchVar
                                note.setPitch(pitchVar)
                                break
                #print '\t\t\t', note

def locate_symbols():
    detected_symbols = {}
    note_type = []

    normal = sys.argv[1].split(',')
    half = sys.argv[2].split(',')
    whole = sys.argv[3].split(',')
    flat = sys.argv[4].split(',')
    sharp = sys.argv[5].split(',')

    session_id = sys.argv[6]
    file_name = sys.argv[7]

    img = Image.openImage(session_id, file_name)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    img = np.asarray(img)
    img_copy = img.copy()
    img_rgb = np.asarray(img_rgb)
    if int(flat[0]) != -1: note_type.append(img[int(flat[1]):int(flat[3]), int(flat[0]):int(flat[2])].copy())
    else: note_type.append(None)

    if int(sharp[0]) != -1: note_type.append(img[int(sharp[1]):int(sharp[3]), int(sharp[0]):int(sharp[2])].copy())
    else: note_type.append(None)

    if int(normal[0]) != -1: note_type.append(img[int(normal[1]):int(normal[3]), int(normal[0]):int(normal[2])].copy())
    else: note_type.append(None)

    if int(half[0]) != -1: note_type.append(img[int(half[1]):int(half[3]), int(half[0]):int(half[2])].copy())
    else: note_type.append(None)

    if int(whole[0]) != -1: note_type.append(img[int(whole[1]):int(whole[3]), int(whole[0]):int(whole[2])].copy())
    else: note_type.append(None)

    pkl_file = open('./public/' + session_id + '/' + 'stave.pkl')
    staves = pickle.load(pkl_file)

    detected_symbols = __match_template(img, note_type, img_rgb, COLOR)
    detected_symbols = __process_tail_direction(detected_symbols, img_copy, img_rgb)
    __allocate_note_to_stave(staves, detected_symbols)
    __process_tail_type(staves, img_copy, img_rgb)
    __find_note_pitch(staves)

    for stave in staves:
        print stave.json()
    Image.saveImage(session_id, "image_marked.png", img_rgb)
    Image.saveImage(session_id, "image_after_process.png", img)
        #print symbol_x, symbol_y
    #return detected_symbols

locate_symbols()
