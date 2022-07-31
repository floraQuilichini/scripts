# whole registration workflow

import matlab.engine
import numpy as np
import subprocess
import os
import sys
import statistics
from shutil import copyfile
from pathlib import Path

eng = matlab.engine.start_matlab()

source_file = "C:\\Registration\\test_gls_algo\\meshes\\small_meshes_for_test\\larger_rescaling\\bunny_simp.ply"
target_file = "C:\\Registration\\test_gls_algo\\meshes\\small_meshes_for_test\\larger_rescaling\\bunny_simp_rX45_t0-4-3_s0.5.ply"
executable_FGR = "C:\\Registration\\FGR\\FastGlobalRegistration-build\\FastGlobalRegistration\\Release\\FastGlobalRegistration.exe"
transform_prefix = "transform_r45_t0_4_3_s05_K12_lambda"
transform_path = "C:\\Registration\\FGR\\gls_example"
pairs_path = "C:\\Registration\\test_gls_algo\\matching_pairs"
pairs_prefix = "12pairs_lambda"
pairs_suffix = "_file";
target_transformed_path = "C:\\Registration\\FGR\\gls_example\\transformed_target"
ext = ".txt"
mean_and_std_path = "C:\\Registration\\FGR\\gls_example\\mean&std"
executable_cloudCompare = "C:\\Program Files\\CloudCompare\\CloudCompare.exe"
all_means_file = "mean_file.txt";
open(os.path.join(mean_and_std_path, all_means_file), 'w').close()

for i in range(0, 101, 1):
    transform_file = transform_prefix + str(i) + ext;
    pairs_file = pairs_prefix + str(i) + pairs_suffix + ext
    # compute registration
    args = executable_FGR + " " + source_file + " " + target_file + " " + os.path.join(pairs_path, pairs_file) + " " + os.path.join(transform_path, transform_file)
    subprocess.call(args, stdin=None, stdout=None, stderr=None)
    # process registration
    estimated_transform_struct = eng.importdata(os.path.join(transform_path, transform_file),' ', 1)
    estimated_transform = eng.getfield(estimated_transform_struct, 'data')
    output_ply_file = os.path.join(target_transformed_path, transform_prefix + str(i) + ".ply")
    eng.register_pcs(source_file, target_file, estimated_transform, output_ply_file, nargout = 0)
    # compute target registered to source distance
    fgr_c2m_result_file = os.path.join(mean_and_std_path, transform_prefix + str(i) +'_c2m_results.txt')
    open(fgr_c2m_result_file, 'w').close()
    args_c2m = executable_cloudCompare + " -SILENT" + " -o " + output_ply_file + " -o " + source_file + " -NO_TIMESTAMP -C_EXPORT_FMT ASC -c2m_dist"  # compute C2M distance
    subprocess.call(args_c2m, stdin=None, stdout=None, stderr=None)
    # process cloudCompare output
        # get file with c2m distances 
    for file in os.listdir(target_transformed_path):
        if "lambda" + str(i) + "_C2M_DIST.asc" in file:
            c2m_file = file

    # get everything in column 4 for c2m
    col_num = 3
    col_data = []
    delimiter = " "
    with open(Path(target_transformed_path) / c2m_file) as f:
        data = f.readlines()
        for line in data:
            col_data.append(line.strip().split(delimiter)[col_num])

    distances_list = list(map(float, col_data))
    signed_mean_c2m_dist = statistics.mean(distances_list)
    unsigned_mean_C2M_dist = statistics.mean(list(map(abs, distances_list)))
    signed_std_c2m = statistics.stdev(distances_list)
    unsigned_std_C2M = statistics.stdev(list(map(abs, distances_list)))
    out_file =open(fgr_c2m_result_file, "a+")
    out_file.write("Mean distance = %5.6f / std deviation = %5.6f\n" % (unsigned_mean_C2M_dist, unsigned_std_C2M))
    out_file.close()
    general_mean_file =open(os.path.join(mean_and_std_path, all_means_file), "a+")
    general_mean_file.write("%5.6f \n" % (unsigned_mean_C2M_dist))
    general_mean_file.close()
