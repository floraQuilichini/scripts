from shutil import copyfile
import numpy as np
import subprocess
import matlab.engine
import statistics

import os
from pathlib import Path

# variables
source_filename = 'C:\\Registration\\test_modified_pipeline\\input_meshes\\source\\ObjetSynthetique_simp32.ply'
target_filenames = ['C:\\Registration\\test_modified_pipeline\\input_meshes\\target\\ObjetSynthetique_simp64_edgeCollapse.ply']
output_directory = 'C:\\Registration\\test_modified_pipeline'
initial_matching = 'False'
cross_check = 'False'

bool_range = ['True', 'False']
correspondence_metrics = ['KL', 'L2']




for target_filename in target_filenames : 
    if 'brain' in target_filename :
        subdir_pc = 'brain'        
    elif 'liver' in target_filename :
        subdir_pc = 'liver'
    else :
        subdir_pc = 'several_organs'
    
    if not os.path.isdir(os.path.join(output_directory, subdir_pc)) : 
        os.mkdir(os.path.join(output_directory, subdir_pc))

    for correspondence_metric in correspondence_metrics : 

        subdir_corres_metric = correspondence_metric

            
        if not os.path.isdir(os.path.join(output_directory, subdir_pc, subdir_corres_metric)) : 
            os.mkdir(os.path.join(output_directory, subdir_pc, subdir_corres_metric))

        for computing_features_with_downsampled_mesh in bool_range :

            if computing_features_with_downsampled_mesh == 'True' : 
                subdir_downsampling = "feature_down"
            else :
                subdir_downsampling = "no_feature_down"
            
            if not os.path.isdir(os.path.join(output_directory, subdir_pc, subdir_corres_metric, subdir_downsampling)) : 
                os.mkdir(os.path.join(output_directory, subdir_pc, subdir_corres_metric, subdir_downsampling))
            
            for bilateral_filtering in bool_range : 
        
                if bilateral_filtering == 'True' : 
                    subdir_filtering = "filtering"
                else :
                    subdir_filtering = "no_filtering"
        
            
                if not os.path.isdir(os.path.join(output_directory, subdir_pc, subdir_corres_metric, subdir_downsampling, subdir_filtering)) : 
                    os.mkdir(os.path.join(output_directory, subdir_pc, subdir_corres_metric, subdir_downsampling, subdir_filtering))
               
            
            
                noise_level_source_list = [0.0, 0.0, 0.0, 0.3, 0.5, 0.5]
                noise_level_target_list = [0.0, 0.3, 0.8, 0.5, 0.8, 1.0]
                nb_noise_matrix_source_list = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
                nb_noise_matrix_target_list = [0.0, 1.0, 1.0, 1.0, 1.0, 1.0]

                for index in range(len(noise_level_source_list)):

                    noise_level_source = noise_level_source_list[index]
                    noise_level_target = noise_level_target_list[index]
                    nb_noise_matrix_source = nb_noise_matrix_source_list[index]
                    nb_noise_matrix_target = nb_noise_matrix_target_list[index]
                    subdir_noise = "m0_s" + str(noise_level_source)+ "_m0_s" + str(noise_level_target)

                    if not os.path.isdir(os.path.join(output_directory, subdir_pc, subdir_corres_metric, subdir_downsampling, subdir_filtering, subdir_noise)) : 
                        os.mkdir(os.path.join(output_directory, subdir_pc, subdir_corres_metric, subdir_downsampling, subdir_filtering, subdir_noise))

                    eng = matlab.engine.start_matlab()
                    eng.workspace['output_directory'] = os.path.join(output_directory, subdir_pc, subdir_corres_metric, subdir_downsampling, subdir_filtering, subdir_noise)
                    eng.workspace['source_filename'] = source_filename
                    eng.workspace['target_filename'] = target_filename
                    eng.workspace['noise_level_source'] = noise_level_source;
                    eng.workspace['noise_level_target'] = noise_level_target;
                    eng.workspace['nb_noise_matrix_source'] = nb_noise_matrix_source;
                    eng.workspace['nb_noise_matrix_target'] = nb_noise_matrix_target;
                    eng.eval("nb_pc_target = 1;", nargout = 0)
                    eng.eval("type_of_noise = 'gaussian';", nargout = 0)
                    eng.eval("noise_generation = 'auto';", nargout = 0)
                    eng.eval("cutting_plane = 'YZ';", nargout = 0)
                    eng.eval("ratio = 0.4;", nargout = 0)
                    eng.eval("theta = 3.14/2;", nargout = 0)
                    eng.eval("rot_axis = 'X';", nargout = 0)
                    eng.eval("trans = [0, 10, 6];", nargout = 0)
                    eng.eval("scale_coeff = [1, 1, 1];", nargout = 0)


                    # for loop to compute mean curves
                    for i in range(1):

                        # generate input data (source and target files)
                        [full_output_dir, source_name, target_name] = eng.eval("generate_inputs_for_FPFH_algorithm(output_directory, source_filename, target_filename, theta, rot_axis, trans, scale_coeff, cutting_plane, ratio, nb_pc_target, type_of_noise, noise_generation, nb_noise_matrix_source, noise_level_source, nb_noise_matrix_target, noise_level_target);", nargout = 3)

                        # FGR registration
                        downsampling_coeff_list = ['0.9', '0.8', '0.7', '0.6', '0.5', '0.4', '0.3', '0.2']
                        for down_coeff  in downsampling_coeff_list:
                            print(down_coeff)
                            myProcess = subprocess.Popen(["python", "registration_workflow.py", source_filename, full_output_dir, source_name, target_name, down_coeff, computing_features_with_downsampled_mesh, bilateral_filtering, correspondence_metric, initial_matching, cross_check])
                            myProcess.wait()



                        # file header
                            # c2c
                        fgr_c2c_result_file = os.path.join(full_output_dir, 'c2c', 'c2c_results.txt')
                        out_file =open(fgr_c2c_result_file, "a+")
                        out_file.write("test %s ending\n" % str(i+1))
                        out_file.close()
                            # c2m
                        fgr_c2m_result_file = os.path.join(full_output_dir, 'c2m', 'c2m_results.txt')
                        out_file =open(fgr_c2m_result_file, "a+")
                        out_file.write("test %s ending\n" % str(i+1))
                        out_file.close()


                        # ICP registration
                        pcd_source_file = source_name + ".pcd"
                        pcd_target_file = target_name + ".pcd"
                        output_subdir = "ICP"

                        #create ICP directory
                        if not os.path.exists(os.path.join(full_output_dir, 'c2c', output_subdir)):
                            os.mkdir(os.path.join(full_output_dir, 'c2c', output_subdir))
                        copyfile(os.path.join(full_output_dir, pcd_target_file), os.path.join(full_output_dir, 'c2c', output_subdir, pcd_target_file))
                        copyfile(os.path.join(full_output_dir, pcd_source_file), os.path.join(full_output_dir, 'c2c', output_subdir, pcd_source_file))
                        
                        if not os.path.exists(os.path.join(full_output_dir, 'c2m', output_subdir)):
                            os.mkdir(os.path.join(full_output_dir, 'c2m', output_subdir))
                        copyfile(os.path.join(full_output_dir, pcd_target_file), os.path.join(full_output_dir, 'c2m', output_subdir, pcd_target_file))
                        copyfile(os.path.join(full_output_dir, pcd_source_file), os.path.join(full_output_dir, 'c2m', output_subdir, pcd_source_file))
                        copyfile(source_filename, os.path.join(full_output_dir, 'c2m', output_subdir, source_name + '.ply'))


                        # compute ICP registration
                        cloudCompare_exe = "C:\\Program Files\\CloudCompare\\CloudCompare.exe"
                        registered_pc_name = "registered_pc.pcd"
                        args = cloudCompare_exe + " -SILENT" + " -o " + os.path.join(full_output_dir, 'c2c', output_subdir, pcd_target_file) + " -o " + os.path.join(full_output_dir, 'c2c', output_subdir, pcd_source_file) + " -NO_TIMESTAMP -AUTO_SAVE OFF -ICP -RANDOM_SAMPLING_LIMIT 3500 -C_EXPORT_FMT PCD -SAVE_CLOUDS FILE " + os.path.join(full_output_dir, 'c2c', output_subdir, registered_pc_name) + " FILE " + os.path.join(full_output_dir, 'c2c', output_subdir, pcd_source_file) # data file first and reference file second 
                        subprocess.call(args, stdin=None, stdout=None, stderr=None)
                        args = cloudCompare_exe + " -SILENT" + " -o " + os.path.join(full_output_dir, 'c2m', output_subdir, pcd_target_file) + " -o " + os.path.join(full_output_dir, 'c2m', output_subdir, pcd_source_file) + " -NO_TIMESTAMP -AUTO_SAVE OFF -ICP -RANDOM_SAMPLING_LIMIT 3500 -C_EXPORT_FMT PCD -SAVE_CLOUDS FILE " + os.path.join(full_output_dir, 'c2m', output_subdir, registered_pc_name) + " FILE " + os.path.join(full_output_dir, 'c2m', output_subdir, pcd_source_file) # data file first and reference file second 
                        subprocess.call(args, stdin=None, stdout=None, stderr=None)


                        # compute point cloud to point cloud distance 
                        icp_c2c_result_file = os.path.join(full_output_dir, 'c2c', output_subdir, 'icp_c2c_results.txt')
                        icp_c2m_result_file = os.path.join(full_output_dir, 'c2m', output_subdir, 'icp_c2m_results.txt')
                        open(icp_c2c_result_file, 'a').close()
                        open(icp_c2m_result_file, 'a').close()
                  
                        args_c2c = cloudCompare_exe + " -SILENT" + " -o " + os.path.join(full_output_dir, 'c2c', output_subdir, registered_pc_name) + " -o " + os.path.join(full_output_dir, 'c2c', output_subdir, pcd_source_file) + " -NO_TIMESTAMP -C_EXPORT_FMT ASC -c2c_dist"  # compared file first and reference file second
                        subprocess.call(args_c2c, stdin=None, stdout=None, stderr=None)
                        args_c2m = cloudCompare_exe + " -SILENT" + " -o " + os.path.join(full_output_dir, 'c2m', output_subdir, registered_pc_name) + " -o " + os.path.join(full_output_dir, 'c2m', output_subdir, source_name + '.ply') + " -NO_TIMESTAMP -C_EXPORT_FMT ASC -c2m_dist" # compute C2M distance
                        subprocess.call(args_c2m, stdin=None, stdout=None, stderr=None)


                        # process cloudCompare output
                            # get file with c2c distance 
                        path_c2c = Path(full_output_dir) / 'c2c' / output_subdir
                        for file in os.listdir(path_c2c):
                            if "C2C_DIST" in file and ".asc" in file:
                                c2c_file = file   
                            # get everything in column 4
                        col_num = 3
                        col_data = []
                        delimiter = " "
                        with open(path_c2c / c2c_file) as f:
                            data = f.readlines()
                            for line in data:
                                col_data.append(line.strip().split(delimiter)[col_num])

                        mean_c2c_dist = statistics.mean(list(map(float, col_data)))
                        print(mean_c2c_dist)
                        std_c2c = statistics.stdev(list(map(float, col_data)))
                        print(std_c2c)
                        header = "objet source : " + source_name  + " ; objet target : " + target_name + "\n"
                        out_file =open(icp_c2c_result_file, "a+")
                        out_file.write("%s" % header)
                        out_file.write("Mean distance = %5.6f / std deviation = %5.6f\n" % (mean_c2c_dist,std_c2c))
                        out_file.close()
                        
                        
                            # get file with c2m distance 
                        path_c2m = Path(full_output_dir) / 'c2m' / output_subdir
                        for file in os.listdir(path_c2m):
                            if "C2M_DIST" in file and ".asc" in file:
                                c2m_file = file                            
                            # get everything in column 4
                        col_num = 3
                        col_data = []
                        delimiter = " "
                        with open(path_c2m / c2m_file) as f:
                            data = f.readlines()
                            for line in data:
                                col_data.append(line.strip().split(delimiter)[col_num])

                        mean_c2m_dist = statistics.mean(list(map(float, col_data)))
                        print(mean_c2m_dist)
                        std_c2m = statistics.stdev(list(map(float, col_data)))
                        print(std_c2m)
                        header = "objet source : " + source_name  + " ; objet target : " + target_name + "\n"
                        out_file =open(icp_c2m_result_file, "a+")
                        out_file.write("%s" % header)
                        out_file.write("Mean distance = %5.6f / std deviation = %5.6f\n" % (mean_c2m_dist,std_c2m))
                        out_file.close()





                    # matlab plot
                    fgr_c2c_result_file = os.path.join(full_output_dir, 'c2c', 'c2c_results.txt')
                    figure = eng.draw_pointCloud_to_pointCloud_meanDistance(fgr_c2c_result_file, icp_c2c_result_file)
                    
                    fgr_c2m_result_file = os.path.join(full_output_dir, 'c2m', 'c2m_results.txt')
                    figure = eng.draw_pointCloud_to_pointCloud_meanDistance(fgr_c2m_result_file, icp_c2m_result_file)
