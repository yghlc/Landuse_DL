#!/usr/bin/env bash

# rasterize mapping polygons

#authors: Huang Lingcao
#email:huanglingcao@gmail.com
#add time: 3 July, 2021

# Exit immediately if a command exits with a non-zero status. E: error trace
#set -eE -o functrace

shp_dir=~/Data/flooding_area/automapping/houston_deeplabV3+_1/result_backup
out_dir=~/Data/flooding_area/mapping_polygons_rasters

py=~/codes/PycharmProjects/Landuse_DL/datasets/rasterize_polygons.py

#for shp in $(ls ${shp_dir}/*/*/*.shp); do
#  echo $shp
#done
function rasterize_map() {
  folder=$1
  ref_tif_dir=$2
  date_pos=$3
  for shp in $(ls ${shp_dir}/${folder}/*/*.shp); do
    echo $shp
    save_dir=${out_dir}/$folder
    name=$(basename $shp)
    name_noext="${name%.*}"
    date_str=$(echo $name | cut -d "_"  -f ${date_pos})

    ref_raster=$(ls ${ref_tif_dir}/*${date_str}*.tif)
    echo $ref_raster
    if [ -z "$ref_raster"  ]; then # ! -f ${ref_raster
      echo "error, ${ref_raster} not exist, skip"
      continue
    fi
    mkdir -p  ${save_dir}
    ${py} -r ${ref_raster} -o ${save_dir} -b 1 ${shp}

    # compress the raster
    gdal_translate -co "compress=lzw" ${save_dir}/${name_noext}_label.tif ${save_dir}/tmp.tif
    rm ${save_dir}/${name_noext}_label.tif
    mv ${save_dir}/tmp.tif ${save_dir}/${name_noext}_label.tif

  done
}
#area_exp=exp1_grd_Goalpara
#ref_tif_dir=~/Data/flooding_area/Goalpara/Goalpara_power_transform_prj_8bit
#rasterize_map ${area_exp} ${ref_tif_dir} 3


#area_exp=exp2_binary_Goalpara
#ref_tif_dir=~/Data/flooding_area/Goalpara/Goalpara_power_transform_prj_8bit
#rasterize_map ${area_exp} ${ref_tif_dir} 4

#area_exp=exp2_binary_Houston
#ref_tif_dir=~/Data/flooding_area/Houston/Houston_mosaic
#rasterize_map ${area_exp} ${ref_tif_dir} 3

#area_exp=exp1_grd_Houston
#ref_tif_dir=~/Data/flooding_area/Houston/Houston_mosaic
#rasterize_map ${area_exp} ${ref_tif_dir} 3


#area_exp=exp4_3band_Houston
#ref_tif_dir=~/Data/flooding_area/Houston/Houston_mosaic
#rasterize_map ${area_exp} ${ref_tif_dir} 4

area_exp=exp5_3band_Houston_fixColor
ref_tif_dir=~/Data/flooding_area/Houston/Houston_mosaic
rasterize_map ${area_exp} ${ref_tif_dir} 4








