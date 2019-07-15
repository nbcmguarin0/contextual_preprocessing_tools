import subprocess
import argparse
import os
import re
import shutil
from pathlib import Path
from multiprocessing import Pool
import ocr_report_generator as report_generator

def get_args():
   parser = argparse.ArgumentParser()
   parser.add_argument("tool", type=str)
   parser.add_argument("full_path_test_dir", type=str)
   parser.add_argument("full_path_truth_dir", type=str)
   parser.add_argument("full_path_output_dir", type=str)
   parser.add_argument("plotly_uname", type=str, help="create a plotly accout here https://plot.ly/feed/#/")
   parser.add_argument("plotly_api_key", type=str, help="create a plotly accout here https://plot.ly/feed/#/ and generate an api key")
   args = parser.parse_args()
   return args
# end

def get_dir_contents(full_path_test_dir, full_path_truth_dir):
   test_dir_contents_txt = [file for file in os.listdir(full_path_test_dir) if file.endswith(".txt")]
   truth_dir_contents_txt = [file for file in os.listdir(full_path_truth_dir) if file.endswith(".txt")]
   return test_dir_contents_txt, truth_dir_contents_txt
# end 

def get_output_dir_contents(full_path_output_dir):
   return [os.path.join(full_path_output_dir, file) for file in os.listdir(full_path_output_dir)]
# end 

def match_test_truth(test_dir_contents_txt, truth_dir_contents_txt):
    get_basename = lambda file: [file, '_'.join(Path(file).stem.split('_')[2:])] # first elm will be GrouthTruth
    truth_contents_basename = list(map(get_basename, truth_dir_contents_txt))

    all_matches = [(truth_filename, test_file, Path(test_file).stem) for truth_filename, truth_pattern in truth_contents_basename 
                             for test_file in test_dir_contents_txt if re.search(truth_pattern.lower()[:30], test_file.lower())]
    
    print("all_matches: {}".format(all_matches))
    return all_matches
# end 

def make_cmd(all_truth_test_output_w_paths):
   assert(os.path.isfile(all_truth_test_output_w_paths[0])), "ground truth file does not exits"
   assert(os.path.isfile(all_truth_test_output_w_paths[1])), "test file does not exits"
   cmd = "java -cp ocrevaluation.jar eu.digitisation.Main -gt {} -ocr {} -o {}".format(all_truth_test_output_w_paths[0], all_truth_test_output_w_paths[1], all_truth_test_output_w_paths[2])
   return cmd
# end 

def run_ocr_jar(cmd):
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).wait()
# end

def main():

   args = get_args()

   if os.path.exists(args.full_path_output_dir):
       shutil.rmtree(args.full_path_output_dir)
   os.mkdir(args.full_path_output_dir)

   test_dir_contents_txt, truth_dir_contents_txt = get_dir_contents(full_path_test_dir=args.full_path_test_dir, full_path_truth_dir=args.full_path_truth_dir)
   all_matches = match_test_truth(test_dir_contents_txt, truth_dir_contents_txt)
   all_truth_w_paths = [os.path.join(args.full_path_truth_dir, truth[0]) for truth in all_matches]
   all_test_w_paths = [os.path.join(args.full_path_test_dir, test[1]) for test in all_matches]
   all_output_w_paths = [os.path.join(args.full_path_output_dir, output[2]+"_report.html") for output in all_matches]
   all_truth_test_output_w_paths = list(zip(all_truth_w_paths, all_test_w_paths, all_output_w_paths))
   all_cmd = list(map(make_cmd, all_truth_test_output_w_paths))

   pool = Pool()
   pool.map(run_ocr_jar, all_cmd)
   pool.close()
   pool.join()

   output_dir_content = get_output_dir_contents(args.full_path_output_dir)
   report_generator.create_reports(output_dir_content, args.full_path_output_dir, args.tool, args.plotly_uname, args.plotly_api_key)
   print("report generation complete")
# end

if __name__ == "__main__":
    main()
