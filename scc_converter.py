import os
import argparse
import traceback
from pycaption import SCCReader

def parse_captions(scc_file_path, desired_ext, scc_captions):
    file_name, file_ext = full_scc_file_path.split("/")[-1].split(".")
    full_output_file_path = os.path.join("/".join(full_scc_file_path.split("/")[:-1]), file_name+desired_ext)
    with open(full_output_file_path, "w+") as output_file:
        for lang, caption in scc_captions.items():
            if lang == "en-US":
                for timestep in caption:
                    output_file.write("{} {} {}\n".format(timestep.format_start(), timestep.format_end(), timestep.get_text()))
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str)
    parser.add_argument("--ext", type=str)
    parser.add_argument("--desired_ext", type=str)
    args = parser.parse_args()

    for scc_file_path in os.listdir(args.dir):
        if scc_file_path.endswith(args.ext):
            try:
                full_scc_file_path = os.path.join(args.dir, scc_file_path)
                scc_file = open(full_scc_file_path, "r")
                scc_context = scc_file.read()
                pycaps = SCCReader().read(scc_context)
                parse_captions(full_scc_file_path, args.desired_ext, pycaps._captions)
            except Exception as e:
                print("error with "+scc_file_path, traceback.print_exc())
                continue