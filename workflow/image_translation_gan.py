#!/usr/bin/env python
# Filename: image_translation_gan.py 
"""
introduction: using GAN (Generative Adversarial Networks) to convert images from one domain to another domain

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 07 October, 2021
"""


import os,sys
import time
from datetime import datetime
from optparse import OptionParser

import GPUtil
from multiprocessing import Process

code_dir = os.path.join(os.path.dirname(sys.argv[0]), '..')
sys.path.insert(0, code_dir)
import parameters
import basic_src.basic as basic
import basic_src.io_function as io_function
import datasets.raster_io as raster_io


def CUT_gan_is_ready_to_train(working_folder):
    if os.path.isfile(os.path.join(working_folder,'ready_to_train.txt')):
        return True
    return False

def generate_image_exists(working_folder):
    if os.path.isfile(os.path.join(working_folder,'generate.txt_done')):
        return True
    return False

def get_gan_project_save_dir(gan_working_dir,gan_dir_pre_name,area_name,area_remark,area_time,area_src_ini):
    'get the folder name for data gan_project'

    area_src_name = os.path.splitext(os.path.basename(area_src_ini))[0]
    gan_project_save_dir = os.path.join(gan_working_dir,
        gan_dir_pre_name + '_' + area_name + '_' + area_remark + '_' + area_time + '_SRC%s' % area_src_name)
    return gan_project_save_dir

def train_CUT_gan(python_path, train_script,gan_para_file,gpu_ids):

    if os.path.isfile('train.txt_done'):
        basic.outputlogMessage('training of GAN in %s has completed previoulsy, please remove it if necessary'%os.getcwd())
        return True

    time0 = time.time()
    train_tile_width = parameters.get_digit_parameters(gan_para_file,'train_tile_width','int')
    train_tile_height = parameters.get_digit_parameters(gan_para_file,'train_tile_height','int')
    train_overlay_x = parameters.get_digit_parameters(gan_para_file,'train_overlay_x','int')
    train_overlay_y = parameters.get_digit_parameters(gan_para_file,'train_overlay_y','int')

    gan_model = parameters.get_string_parameters(gan_para_file, 'gan_model')

    folder=os.path.basename(os.getcwd())
    train_models = io_function.get_file_list_by_pattern(os.path.join('checkpoints',folder),'latest*.pth')

    command_string = python_path + ' '  +  train_script \
                + ' --model ' + str(gan_model) \
                + ' --dataset_mode '+'satelliteimage' \
                + ' --image_A_dir_txt ' + 'image_A_list.txt' \
                + ' --image_B_dir_txt ' + 'image_B_list.txt' \
                + ' --tile_width ' + str(train_tile_width) \
                + ' --tile_height ' + str(train_tile_height) \
                + ' --overlay_x ' + str(train_overlay_x) \
                + ' --overlay_y ' + str(train_overlay_y)  \
                + ' --display_env ' + folder  \
                + ' --name ' + folder  \
                + ' --gpu_ids ' + ','.join([str(item) for item in gpu_ids])

    # if trained model exist, continue train
    if len(train_models) > 0:
        command_string += ' --continue_train '

    n_epochs = parameters.get_digit_parameters(gan_para_file,'n_epochs','int')
    n_epochs_decay = parameters.get_digit_parameters(gan_para_file,'n_epochs_decay','int')
    command_string += ' --n_epochs ' + str(n_epochs) + ' --n_epochs_decay ' + str(n_epochs_decay)

    train_max_dataset_size = parameters.get_digit_parameters_None_if_absence(gan_para_file,'train_max_dataset_size','int')
    if train_max_dataset_size is not None:
        command_string += ' --max_dataset_size ' + str(train_max_dataset_size)

    # status, result = basic.exec_command_string(command_string)  # this will wait command finished
    # os.system(command_string + "&")  # don't know when it finished
    res = os.system(command_string)  # this work
    # print('command_string deeplab_inf_script: res',res)
    if res != 0:
        sys.exit(1)

    duration = time.time() - time0
    os.system('echo "$(date): time cost of training a GAN : %.2f seconds">>"time_cost.txt"' % (duration))
    # write a file to indicate that the training has completed.
    os.system('echo done > train.txt_done')

    return True

def generate_image_CUT(python_path, generate_script, gan_para_file, gpu_ids, image_list, save_folder):

    if os.path.isfile('generate.txt_done'):
        basic.outputlogMessage('generate of new images using GAN in %s has completed previoulsy, please remove them if necessary'%os.getcwd())
        return True

    time0 = time.time()
    generate_tile_width = parameters.get_digit_parameters(gan_para_file,'generate_tile_width','int')
    generate_tile_height = parameters.get_digit_parameters(gan_para_file,'generate_tile_height','int')
    generate_overlay_x = parameters.get_digit_parameters(gan_para_file,'generate_overlay_x','int')
    generate_overlay_y = parameters.get_digit_parameters(gan_para_file,'generate_overlay_y','int')

    folder=os.path.basename(os.getcwd())
    img_list_txt = 'image_to_generate_list.txt'
    io_function.save_list_to_txt(img_list_txt,image_list)

    command_string = python_path + ' '  +  generate_script \
                + ' --dataset_mode '+'satelliteimage' \
                + ' --model '+ 'generate' \
                + ' --image_A_dir_txt ' + img_list_txt \
                + ' --tile_width ' + str(generate_tile_width) \
                + ' --tile_height ' + str(generate_tile_height) \
                + ' --overlay_x ' + str(generate_overlay_x) \
                + ' --overlay_y ' + str(generate_overlay_y)  \
                + ' --name ' + folder  \
                + ' --results_dir ' + save_folder  \
                + ' --gpu_ids ' + ','.join([str(item) for item in gpu_ids])

    train_max_dataset_size = parameters.get_digit_parameters_None_if_absence(gan_para_file,'gen_max_dataset_size','int')
    if train_max_dataset_size is not None:
        command_string += ' --max_dataset_size ' + str(train_max_dataset_size)

    # if it's cycleGAN, need to assign A generator
    gan_model = parameters.get_string_parameters(gan_para_file, 'gan_model')
    if gan_model == 'cycle_gan':
        command_string += ' --model_suffix _A '       # from A to B

    # status, result = basic.exec_command_string(command_string)  # this will wait command finished
    # os.system(command_string + "&")  # don't know when it finished
    res = os.system(command_string)  # this work
    # print('command_string deeplab_inf_script: res',res)
    if res != 0:
        sys.exit(1)

    duration = time.time() - time0
    os.system('echo "$(date): time cost of generate images using a GAN : %.2f seconds">>"time_cost.txt"' % (duration))
    # write a file to indicate that the process has completed.
    os.system('echo done > generate.txt_done')

    return True


def image_translate_train_generate_one_domain(gan_working_dir, gan_para_file, area_src_ini, area_gan_ini, gpu_ids, domainB_imgList):

    current_dir = os.getcwd()

    # get orignal sub-images
    _, _,area_ini_sub_images_labels_dict = original_sub_images_labels_list_before_gan()
    sub_img_label_txt = os.path.join(current_dir,area_ini_sub_images_labels_dict)
    if os.path.isfile(area_ini_sub_images_labels_dict) is False:
        raise IOError('%s not in the current folder, please get subImages first' % sub_img_label_txt)

    # prepare image list of domain A
    # what if the size of some images are not fit with CUT input?
    domain_A_images = []
    # domain_A_labels = []
    # with open(sub_img_label_txt) as txt_obj:
    #     line_list = [name.strip() for name in txt_obj.readlines()]
    #     for line in line_list:
    #         sub_image, sub_label = line.split(':')
    #         domain_A_images.append(os.path.join(current_dir,sub_image))
    #         # domain_A_labels.append(os.path.join(current_dir,sub_label))

    area_ini_sub_images_labels = io_function.read_dict_from_txt_json('area_ini_sub_images_labels.txt')
    for line in area_ini_sub_images_labels[os.path.basename(area_src_ini)]:
            sub_image, sub_label = line.split(':')
            domain_A_images.append(os.path.join(current_dir,sub_image))
            # domain_A_labels.append(os.path.join(current_dir,sub_label))

    
    os.chdir(gan_working_dir)

    io_function.save_list_to_txt('image_A_list.txt',domain_A_images)

    # read target images, that will consider as target domains
    # what if there are too many images in domain B?
    io_function.save_list_to_txt('image_B_list.txt',domainB_imgList)

    
    gan_python = parameters.get_file_path_parameters(gan_para_file,'python')
    cut_dir = parameters.get_directory(gan_para_file,'gan_script_dir')
    train_script = os.path.join(cut_dir, 'train.py')
    generate_script = os.path.join(cut_dir,'generate_image.py')
    # training of CUT 
    if train_CUT_gan(gan_python,train_script,gan_para_file,gpu_ids) is False:
        os.chdir(current_dir)
        return False

    # genenerate image using CUT, convert images in domain A to domain B
    save_tran_img_folder = 'subImages_translate'
    if generate_image_CUT(gan_python, generate_script,gan_para_file,gpu_ids, domain_A_images, save_tran_img_folder) is False:
        os.chdir(current_dir)
        return False


    # change working directory back
    os.chdir(current_dir)
    pass

def original_sub_images_labels_list_before_gan():

    # backup original sub_images list
    sub_img_label_txt = 'sub_images_labels_list.txt'
    sub_img_label_txt_noGAN = 'sub_images_labels_list_noGAN.txt'
    area_ini_sub_images_labels_dict = 'area_ini_sub_images_labels.txt'
    if os.path.isfile(sub_img_label_txt_noGAN) is False:
        io_function.copy_file_to_dst(sub_img_label_txt,sub_img_label_txt_noGAN,overwrite=False)

    return sub_img_label_txt_noGAN, sub_img_label_txt,area_ini_sub_images_labels_dict


def merge_subImages_from_gan(multi_gan_source_regions,multi_gan_regions,gan_working_dir,gan_dir_pre_name,save_image_dir, save_label_dir):
    '''
    merge translate subimages from GAN to orginal sub_images
    :param multi_gan_regions:
    :param gan_working_dir:
    :param gan_dir_pre_name:
    :return:
    '''

    current_dir = os.getcwd()
    sub_img_label_txt_noGAN, sub_img_label_txt,area_ini_sub_images_labels_dict = original_sub_images_labels_list_before_gan()

    # # get original sub-images and labels
    # org_sub_images = []
    # org_sub_labels = []
    # with open(sub_img_label_txt_noGAN) as txt_obj:
    #     line_list = [name.strip() for name in txt_obj.readlines()]
    #     for line in line_list:
    #         sub_image, sub_label = line.split(':')
    #         org_sub_images.append(os.path.join(current_dir,sub_image))
    #         org_sub_labels.append(os.path.join(current_dir,sub_label))
    #
    # # merge new sub images, and copy sub labels if necessary.
    new_sub_images = []
    new_sub_labels = []

    area_ini_sub_images_labels = io_function.read_dict_from_txt_json(area_ini_sub_images_labels_dict)
    # copy the original sub images and labels before GAN
    for key in area_ini_sub_images_labels.keys():
        for line in area_ini_sub_images_labels[key]:
            sub_image, sub_label = line.split(':')
            new_sub_images.append(sub_image)
            new_sub_labels.append(sub_label)

    for area_idx, (area_ini, area_src_ini) in enumerate(zip(multi_gan_regions,multi_gan_source_regions)):
        area_name = parameters.get_string_parameters(area_ini, 'area_name')
        area_remark = parameters.get_string_parameters(area_ini, 'area_remark')
        area_time = parameters.get_string_parameters(area_ini, 'area_time')

        gan_project_save_dir = get_gan_project_save_dir(gan_working_dir, gan_dir_pre_name, area_name, area_remark,
                                                        area_time, area_src_ini)

        org_sub_images = []
        org_sub_labels = []
        for line in area_ini_sub_images_labels[os.path.basename(area_src_ini)]:
            sub_image, sub_label = line.split(':')
            org_sub_images.append(os.path.join(current_dir, sub_image))
            org_sub_labels.append(os.path.join(current_dir, sub_label))

        # the new images, keep the same order of original images
        for idx, (org_img, org_label) in enumerate(zip(org_sub_images,org_sub_labels)):
            new_img = os.path.join(gan_project_save_dir,'subImages_translate', 'I%d.tif' % idx)

            if os.path.isfile(new_img) is False:
                basic.outputlogMessage('warning, %d th image does not exist, '
                                       'may exceed gen_max_dataset_size, skip the following images '%idx)
                break

            # check height, width, band count, datatype
            height, width, count, dtype = raster_io.get_height_width_bandnum_dtype(new_img)
            o_height, o_width, o_count, o_dtype = raster_io.get_height_width_bandnum_dtype(org_img)
            if height!=o_height or width!=o_width or count != o_count or dtype!=o_dtype:
                raise ValueError('inconsistence between new GAN image and original images: %s vs %s'%
                                 (str([height, width, count, dtype]), str([o_height, o_width, o_count, o_dtype])))

            # copy subimage and sublabel
            new_file_name_no_ext = io_function.get_name_no_ext(org_img)+ '_'  + os.path.basename(gan_project_save_dir)
            save_img_path = os.path.join(save_image_dir, new_file_name_no_ext  +'_gan.tif' )
            save_label_path = os.path.join(save_label_dir, new_file_name_no_ext + '_label.tif')
            io_function.copy_file_to_dst(new_img,save_img_path,overwrite=False)
            io_function.copy_file_to_dst(org_label,save_label_path,overwrite=False)

            new_sub_images.append(save_img_path)
            new_sub_labels.append(save_label_path)

    # save new images_labels_list.txt, overwrite the original one
    with open(sub_img_label_txt,'w') as f_obj:
        lines = [ img + ':' + label + '\n' for img, label in zip(new_sub_images,new_sub_labels)]
        f_obj.writelines(lines)

    return True


def image_translate_train_generate_main(para_file, gpu_num):
    '''
     apply GAN to translate image from source domain to target domain

    existing sub-images (with sub-labels), these are image in source domain
    depend images for inference but no training data, each image for inference can be considered as on target domain

    '''
    print(datetime.now(), "image translation (train and generate) using GAN")

    if os.path.isfile(para_file) is False:
        raise IOError('File %s not exists in current folder: %s'%(para_file, os.getcwd()))

    gan_para_file = parameters.get_string_parameters_None_if_absence(para_file, 'regions_n_setting_image_translation_ini')
    if gan_para_file is None:
        print('regions_n_setting_image_translation_ini is not set, skip image translation using GAN')
        return None
    gan_para_file = os.path.abspath(gan_para_file)  # change to absolute path, because later, we change folder
    training_regions = parameters.get_string_list_parameters(para_file, 'training_regions')

    machine_name = os.uname()[1]
    SECONDS = time.time()

    # get regions (equal to or subset of inference regions) need apply image translation
    multi_gan_regions = parameters.get_string_list_parameters(gan_para_file, 'regions_need_image_translation')
    multi_gan_source_regions = parameters.get_string_list_parameters(gan_para_file, 'source_domain_regions')
    # check target domain
    if len(multi_gan_source_regions) != len(multi_gan_regions):
        raise ValueError('the number of source domain and target domain is different')
    if set(multi_gan_source_regions).issubset(training_regions) is False:
        raise ValueError('the source domain regions are not the subset of training regions')
    for area_idx, (area_gan_ini, area_src_ini) in enumerate(zip(multi_gan_regions,multi_gan_source_regions)):
        basic.outputlogMessage('%d: source and target area: %s vs %s'%(area_idx,area_src_ini,area_gan_ini))

    gan_working_dir = parameters.get_string_parameters(gan_para_file, 'working_root')
    # gan_dir_pre_name = parameters.get_string_parameters(gan_para_file, 'gan_dir_pre_name')
    # use GAN model name as the gan_dir_pre_name
    gan_model = parameters.get_string_parameters(gan_para_file, 'gan_model')
    gan_dir_pre_name =  gan_model # '_' +

    # loop each regions need image translation
    sub_tasks = []
    for area_idx, (area_gan_ini, area_src_ini) in enumerate(zip(multi_gan_regions,multi_gan_source_regions)):

        area_ini = os.path.abspath(area_gan_ini)
        area_src_ini = os.path.abspath(area_src_ini)
        area_name = parameters.get_string_parameters(area_ini, 'area_name')
        area_remark = parameters.get_string_parameters(area_ini, 'area_remark')
        area_time = parameters.get_string_parameters(area_ini, 'area_time')

        inf_image_dir = parameters.get_directory(area_ini, 'inf_image_dir')

        # it is ok consider a file name as pattern and pass it the following functions to get file list
        inf_image_or_pattern = parameters.get_string_parameters(area_ini, 'inf_image_or_pattern')

        inf_img_list = io_function.get_file_list_by_pattern(inf_image_dir, inf_image_or_pattern)
        img_count = len(inf_img_list)
        if img_count < 1:
            raise ValueError('No image for image translation, please check inf_image_dir and inf_image_or_pattern in %s' % area_ini)

        gan_project_save_dir = get_gan_project_save_dir(gan_working_dir,gan_dir_pre_name,area_name,area_remark,area_time,area_src_ini)

        if os.path.isdir(gan_project_save_dir):
            if generate_image_exists(gan_project_save_dir) is True:
                basic.outputlogMessage('generated new images (generate.txt_done) exist for %s exist, skip'%gan_project_save_dir)
                continue
        else:
            io_function.mkdir(gan_project_save_dir)

        # parallel run image translation for this area
        CUDA_VISIBLE_DEVICES = []
        if 'CUDA_VISIBLE_DEVICES' in os.environ.keys():
            CUDA_VISIBLE_DEVICES = [int(item.strip()) for item in os.environ['CUDA_VISIBLE_DEVICES'].split(',')]

        # get an valid GPU
        gpuids = []
        while len(gpuids) < 1:
            # get available GPUs  # https://github.com/anderskm/gputil
            deviceIDs = GPUtil.getAvailable(order='first', limit=100, maxLoad=0.5,
                                            maxMemory=0.5, includeNan=False, excludeID=[], excludeUUID=[])
            # only use the one in CUDA_VISIBLE_DEVICES
            if len(CUDA_VISIBLE_DEVICES) > 0:
                deviceIDs = [item for item in deviceIDs if item in CUDA_VISIBLE_DEVICES]
                basic.outputlogMessage('on ' + machine_name + ', available GPUs:' + str(deviceIDs) +
                                       ', among visible ones:' + str(CUDA_VISIBLE_DEVICES))
            else:
                basic.outputlogMessage('on ' + machine_name + ', available GPUs:' + str(deviceIDs))

            if len(deviceIDs) < 1:
                print(datetime.now(),'No available GPUs, will check again in 60 seconds')
                time.sleep(60)  # wait one minute, then check the available GPUs again
                continue
            # set only the first available visible
            gpuids.append(deviceIDs[0])
            basic.outputlogMessage('%d:image translation for  %s on GPU %s of %s' % (area_idx, area_ini, str(gpuids), machine_name))

        # run image translation
        # pytorch consider first GPUs in CUDA_VISIBLE_DEVICES as zero, so need to re-index gpu ids
        if len(CUDA_VISIBLE_DEVICES) > 0:
            gpuids = [CUDA_VISIBLE_DEVICES.index(id) for id in gpuids]

        sub_process = Process(target=image_translate_train_generate_one_domain,
                              args=(gan_project_save_dir,gan_para_file, area_src_ini, area_ini, gpuids,inf_img_list))

        sub_process.start()
        sub_tasks.append(sub_process)

        # wait until image translation has started or exceed 20 minutes
        time0 = time.time()
        elapsed_time = time.time() - time0
        while elapsed_time < 20 * 60:
            elapsed_time = time.time() - time0
            if CUT_gan_is_ready_to_train(gan_project_save_dir) is True or sub_process.is_alive() is False:
                break
            else:
                time.sleep(5)

        time.sleep(10)   # wait, allowing time for the GAN process to start, and run into problem

        if sub_process.exitcode is not None and sub_process.exitcode != 0:
            sys.exit(1)

        basic.close_remove_completed_process(sub_tasks)

    # check all the tasks already finished
    while basic.b_all_process_finish(sub_tasks) is False:
        basic.outputlogMessage('wait all tasks to finish')
        time.sleep(60)
    basic.check_exitcode_of_process(sub_tasks)
    basic.close_remove_completed_process(sub_tasks)

    save_image_dir = parameters.get_string_parameters(para_file,'input_train_dir')
    save_label_dir = parameters.get_string_parameters(para_file,'input_label_dir')
    merge_subImages_from_gan(multi_gan_source_regions,multi_gan_regions, gan_working_dir, gan_dir_pre_name, save_image_dir, save_label_dir)


    duration= time.time() - SECONDS
    os.system('echo "$(date): time cost of translating sub images to target domains: %.2f seconds">>time_cost.txt'%duration)


def main(options, args):
    para_file = sys.argv[1]
    gpu_num = int(sys.argv[2])

    image_translate_train_generate_main(para_file, gpu_num)



if __name__ == '__main__':
    usage = "usage: %prog [options] para_file gpu_num"
    parser = OptionParser(usage=usage, version="1.0 2021-10-07")
    parser.description = 'Introduction: translate images from source domain to target domain '

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    main(options, args)


