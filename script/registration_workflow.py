# whole registration workflow

import matlab.engine
import numpy as np
import subprocess
import os
import sys
import statistics
from shutil import copyfile
from pathlib import Path


#input parameters
source_filename = sys.argv[1]
full_output_dir = sys.argv[2]
source_name = sys.argv[3]
target_name = sys.argv[4]
fraction_kept_points = float(sys.argv[5])
computing_features_with_downsampled_mesh = sys.argv[6]
bilateral_filtering = sys.argv[7]
correspondence_metric = sys.argv[8]
initial_matching = sys.argv[9]
cross_check = sys.argv[10]



eng = matlab.engine.start_matlab()

## rescale data
#pcd_source_file = source_name + ".pcd"
#pcd_target_file = target_name + ".pcd"
#[max_scale, trans_source, trans_target] = eng.rescale_data(os.path.join(full_output_dir, pcd_source_file), os.path.join(full_output_dir, pcd_target_file), nargout = 3)


original_ply_source_file = source_name + ".ply"
original_pcd_source_file = source_name + ".pcd"
original_pcd_target_file = target_name + ".pcd"


# downsample source point cloud 
    # downsampling
        ## random
# pointCloud_random_down = eng.pcdownsample(eng.pcread(os.path.join(full_output_dir, original_pcd_source_file)),'random',fraction_kept_points); # random downsampling 50% of the point cloud
            ## save downsampled point cloud
# pc_down_filename = source_name + "_downsampled" + str(fraction_kept_points) + ".pcd"
# eng.pcwrite(pointCloud_random_down,os.path.join(full_output_dir, pc_down_filename),'Encoding','ascii', nargout = 0)
        # vsa
pc_vsa_filename = source_name + str(fraction_kept_points) + "_vsa" + ".pcd"
vsa_exe = "C:/Registration/VSA/vsa/x64/Release/vsa.exe"
args = vsa_exe + " " + os.path.join(full_output_dir, original_ply_source_file) + " " + os.path.join(full_output_dir, pc_vsa_filename) + " " +  str(eng.convert_kept_point_fraction_to_subdivision_ratio(fraction_kept_points))
subprocess.call(args, stdin=None, stdout=None, stderr=None)    

##point cloud denoising
if bilateral_filtering  == 'True' or bilateral_filtering == 'true' :
    pcd_source_file_filtered = source_name + "_filtered" + ".pcd"
    pcd_target_file_filtered = target_name + "_filtered" + ".pcd";
    executable_BilateralFilter = "C:/Registration/BilateralFilter/BilateralFilter/BilateralFilter-build/Release/bilateralfilter.exe"
        #for source
    #[source_radius, source_normal_radius] = eng.getBilateralFilterInputParameters(os.path.join(full_output_dir, original_pcd_source_file), nargout = 2)
    source_radius = eng.compute_voxel_size(eng.pcread(os.path.join(full_output_dir, original_pcd_source_file)), 1.0) * 2.0
    source_normal_radius = source_radius
    args = executable_BilateralFilter + " " + os.path.join(full_output_dir, original_pcd_source_file) + " " + os.path.join(full_output_dir, pcd_source_file_filtered) + " -r " + str(source_radius) +  " -n " + str(source_normal_radius) + " -N 1"
    subprocess.call(args, stdin=None, stdout=None, stderr=None)
    source_name = source_name + "_filtered"
        #for target
    #[target_radius, target_normal_radius] = eng.getBilateralFilterInputParameters(os.path.join(full_output_dir, original_pcd_target_file), nargout = 2)
    target_radius = eng.compute_voxel_size(eng.pcread(os.path.join(full_output_dir, original_pcd_target_file)), 1.0) * 2.0
    target_normal_radius = target_radius
    args = executable_BilateralFilter + " " + os.path.join(full_output_dir, original_pcd_target_file) + " " + os.path.join(full_output_dir, pcd_target_file_filtered) + " -r " + str(target_radius) +  " -n " + str(target_normal_radius) + " -N 1"
    subprocess.call(args, stdin=None, stdout=None, stderr=None)
    target_name = target_name + "_filtered"


# get pc_source_downsampled closest point to pc_source_filtered
pc_down_filename = source_name + "_downsampled" + str(fraction_kept_points) + ".pcd"
output_filename = os.path.join(full_output_dir, pc_down_filename)
print(os.path.join(full_output_dir, pcd_source_file_filtered))
eng.get_pc2_closest_points_in_pc1(eng.pcread(os.path.join(full_output_dir, pc_vsa_filename)), eng.pcread(os.path.join(full_output_dir, pcd_source_file_filtered)), output_filename, nargout = 0)




# compute FPFH
executable_FPFH = "C:/Registration/FPFH/generateFPFH_files/x64/Release/generateFPFH_files.exe"
    # get target pcd file
pcd_target_file = target_name + ".pcd"
voxel_side_size_source = eng.compute_voxel_size(eng.pcread(os.path.join(full_output_dir, pc_down_filename)), 1.0)
    # compute voxel size
voxel_side_size_target = eng.compute_voxel_size(eng.pcread(os.path.join(full_output_dir, pcd_target_file)), 1.0)
voxel_size = eng.max(voxel_side_size_target, voxel_side_size_source)
    # compute FPFH for source
if computing_features_with_downsampled_mesh == 'False' or initial_matching == 'false' :
    args = executable_FPFH + " " + os.path.join(full_output_dir, pc_down_filename) + " " + os.path.join(full_output_dir, pcd_source_file) + " " + str(0) + " " + str(voxel_size*2.0) + " " + str(voxel_size*5.0)
else : 
    args = executable_FPFH + " " + os.path.join(full_output_dir, pc_down_filename) + " " + "-" + " " + str(0) + " " + str(voxel_size*2.0) + " " + str(voxel_size*5.0)
subprocess.call(args, stdin=None, stdout=None, stderr=None)
    # compute FPFH for target
args = executable_FPFH + " " + os.path.join(full_output_dir, pcd_target_file) + " " + "-" + " " + str(0) + " " + str(voxel_size*2.0) + " " + str(voxel_size*5.0)
subprocess.call(args, stdin=None, stdout=None, stderr=None)
    


# compute correspondence pairs (if needed)
if initial_matching == 'False' or initial_matching == 'false' :
    fpfh_source_textfilename = source_name + "_downsampled" + str(fraction_kept_points)+ "_fpfh.txt"
    fpfh_target_textfilename = target_name + "_fpfh.txt"
    Tfilename = os.path.join(full_output_dir, 'transform_matrix_model.txt')
    [mean_dist, pairs_target_source] = eng.getFPFHHistogramsDistance(os.path.join(full_output_dir, fpfh_source_textfilename), os.path.join(full_output_dir, fpfh_target_textfilename), True, correspondence_metric, nargout = 2)
    #eng.visualizeFPFHPoints(os.path.join(full_output_dir, pcd_target_file), os.path.join(full_output_dir, pcd_source_file), os.path.join(full_output_dir, pcd_target_file), os.path.join(full_output_dir, pc_down_filename), pairs_target_source, Tfilename, 1.0, 0.0, 0.0, nargout = 0)


# FGR
executable_FGR = "C:\\Registration\\FGR\\FastGlobalRegistration-build\\FastGlobalRegistration\\Release\\FastGlobalRegistration.exe"
output_prefix = "output_"
output_ext = ".txt"
    # get source and target binary file
source_bin_file = source_name + "_downsampled" + str(fraction_kept_points) + ".bin"
target_bin_file = target_name + ".bin"    
    # compute registration
output_file = output_prefix + source_name +"_downsampled" + str(fraction_kept_points) + "_" + target_name + output_ext
args = executable_FGR + " " + os.path.join(full_output_dir, source_bin_file) + " " + os.path.join(full_output_dir, target_bin_file) + " " + os.path.join(full_output_dir, output_file) + " " + initial_matching + " " + cross_check
subprocess.call(args, stdin=None, stdout=None, stderr=None)


# process registration
eng.eval("scale_coeff = [1, 1, 1];", nargout = 0)
#registered_target_file = eng.pcSimpleRegistration(full_output_dir, output_file, full_output_dir, eng.eval('scale_coeff'))
registered_target_file = eng.pcSimpleRegistration_v2(full_output_dir, output_file, os.path.join(full_output_dir, original_pcd_source_file), original_pcd_target_file, eng.eval('scale_coeff'))


# compute target registered to source distance
subdir_c2c = "c2c"    
subdir_c2m = "c2m"
  
if not os.path.isdir(os.path.join(full_output_dir, subdir_c2c)) : 
    os.mkdir(os.path.join(full_output_dir, subdir_c2c))

if not os.path.isdir(os.path.join(full_output_dir, subdir_c2m)) : 
    os.mkdir(os.path.join(full_output_dir, subdir_c2m))


cloudCompare_exe = "C:\\Program Files\\CloudCompare\\CloudCompare.exe"

fgr_c2c_result_file = os.path.join(full_output_dir, subdir_c2c, 'c2c_results.txt')
open(fgr_c2c_result_file, 'a').close()

fgr_c2m_result_file = os.path.join(full_output_dir, subdir_c2m, 'c2m_results.txt')
open(fgr_c2m_result_file, 'a').close()

args_c2c = cloudCompare_exe + " -SILENT"+ " -o " + registered_target_file + " -o " + os.path.join(full_output_dir, original_pcd_source_file) + " -NO_TIMESTAMP -C_EXPORT_FMT ASC -c2c_dist"  # compared file first and reference file second
args_c2m = cloudCompare_exe + " -SILENT" + " -o " + registered_target_file + " -o " + source_filename + " -NO_TIMESTAMP -C_EXPORT_FMT ASC -c2m_dist"  # compute C2M distance

subprocess.call(args_c2c, stdin=None, stdout=None, stderr=None)
subprocess.call(args_c2m, stdin=None, stdout=None, stderr=None)


# process cloudCompare output
    # get file with c2c and c2m distances 
path = Path(full_output_dir) / 'targetTransformed'
for file in os.listdir(path):
    if "C2C_DIST" in file and ".asc" in file:
        c2c_file = file
    if "C2M_DIST" in file and ".asc" in file:
        c2m_file = file

    # get everything in column 4 for c2c
col_num = 3
col_data = []
delimiter = " "
with open(path / c2c_file) as f:
    data = f.readlines()
    for line in data:
        col_data.append(line.strip().split(delimiter)[col_num])

mean_c2c_dist = statistics.mean(list(map(float, col_data)))
print(mean_c2c_dist)
std_c2c = statistics.stdev(list(map(float, col_data)))
print(std_c2c)
header = "objet source : " + source_name + " , downsampling : " + str(fraction_kept_points) + " ; objet target : " + target_name + "\n"
out_file =open(fgr_c2c_result_file, "a+")
out_file.write("%s" % header)
out_file.write("Mean distance = %5.6f / std deviation = %5.6f\n" % (mean_c2c_dist,std_c2c))
out_file.close()

    # get everything in column 4 for c2m
col_num = 3
col_data = []
delimiter = " "
with open(path / c2m_file) as f:
    data = f.readlines()
    for line in data:
        col_data.append(line.strip().split(delimiter)[col_num])

mean_c2m_dist = statistics.mean(list(map(float, col_data)))
print(mean_c2m_dist)
std_c2m = statistics.stdev(list(map(float, col_data)))
print(std_c2m)
header = "objet source : " + source_name + " , downsampling : " + str(fraction_kept_points) + " ; objet target : " + target_name + "\n"
out_file =open(fgr_c2m_result_file, "a+")
out_file.write("%s" % header)
out_file.write("Mean distance = %5.6f / std deviation = %5.6f\n" % (mean_c2m_dist,std_c2m))
out_file.close()

