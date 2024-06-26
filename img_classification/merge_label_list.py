#!/usr/bin/env python
# Filename: merge_label_list.py 
"""
introduction:

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 01 February, 2024
"""

import os,sys
from optparse import OptionParser
code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, code_dir)
import basic_src.io_function as io_function

def read_BigEarthNet_labels(path):
    label_dict = io_function.read_dict_from_txt_json(path)
    # label_19 = label_dict['BigEarthNet-19_labels']
    # labels = [item.replace(',',' ') for item in label_19.keys()]
    # print(labels)
    labels = [item.replace(',',' ') for item in label_dict['original_labels'].keys()]

    return labels


def merge_label_list(label_list_txts, save_path):
    if len(label_list_txts) < 2:
        raise ValueError('need at least two label list text files')

    labels = []
    for txt in label_list_txts:
        print('reading %s'%txt)
        if 'BigEarthNet' in txt:
            tmp_labels = read_BigEarthNet_labels(txt)
            labels.extend(tmp_labels)
            continue

        tmp_labels = [ item.split(',')[0] for item in  io_function.read_list_from_txt(txt)]
        tmp_labels = [ item.lower().strip() for item in tmp_labels]
        # check duplication
        tmp_labels = [ item for item in tmp_labels if item not in labels]

        labels.extend(tmp_labels)

    # save
    labels_strs = [ '%s, %d'%(item, idx) for idx, item in enumerate(labels)]
    io_function.save_list_to_txt(save_path,labels_strs)
    print('saved to %s'%os.path.abspath(save_path))


def main(options, args):

    if len(args) < 3:
        raise ValueError('need at least three inputs: two label list, last one is the saved_path')

    label_list_txt = args[:-1]
    save_path = args[-1]
    merge_label_list(label_list_txt, save_path)



if __name__ == '__main__':
    usage = "usage: %prog [options] label_list1.txt label_list2.txt ...  save_path"
    parser = OptionParser(usage=usage, version="1.0 2024-02-01")
    parser.description = 'Introduction: merge several label list into one '

    (options, args) = parser.parse_args()
    main(options, args)
