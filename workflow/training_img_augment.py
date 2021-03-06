#!/usr/bin/env python
# Filename: training_img_augment 
"""
introduction: permaform data augmentation for both training images and label images

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 19 January, 2021
"""

import os,sys
import time

if __name__ == '__main__':

    print("%s : split sub-images and sub-labels" % os.path.basename(sys.argv[0]))

    para_file=sys.argv[1]
    if os.path.isfile(para_file) is False:
        raise IOError('File %s not exists in current folder: %s'%(para_file, os.getcwd()))

    code_dir = os.path.join(os.path.dirname(sys.argv[0]), '..')
    sys.path.insert(0, code_dir)
    import parameters

    augscript = os.path.join(code_dir,'datasets','image_augment.py')

    img_ext = parameters.get_string_parameters_None_if_absence(para_file,'split_image_format')
    print("image format: %s"% img_ext)


    SECONDS=time.time()


    #augment training images
    print("image augmentation on image patches")
    img_list_aug_txt = 'list/images_including_aug.txt'
    command_string = augscript + ' -p ' + para_file + ' -d ' + 'split_images' + ' -e ' + img_ext + \
                     ' -o ' + 'split_images' + ' -l ' + img_list_aug_txt + ' ' + 'list/trainval.txt'
    os.system(command_string)


    #augment training lables
    command_string = augscript + ' -p ' + para_file + ' -d ' + 'split_labels' + ' -e ' + img_ext + \
                     ' -o ' + 'split_labels' + ' -l ' + img_list_aug_txt + ' ' + 'list/trainval.txt' + ' --is_ground_truth '

    os.system(command_string)

    if os.path.isfile(img_list_aug_txt):
        os.system(' cp %s list/trainval.txt'%img_list_aug_txt)
        os.system(' cp %s list/val.txt'%img_list_aug_txt)
    else:
        print('list/images_including_aug.txt does not exist because no data augmentation strings')


    # output the number of image patches
    os.system('echo "count of class 0 ":$(ls split_images/*class_0*${img_ext} |wc -l) >> time_cost.txt')
    os.system('echo "count of class 1 ":$(ls split_images/*class_1*${img_ext} |wc -l) >> time_cost.txt')

    duration= time.time() - SECONDS
    os.system('echo "$(date): time cost of training images augmentation: %.2f seconds">>time_cost.txt'%duration)
