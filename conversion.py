import os
import argparse
import traceback
from pycaption import SCCReader
from tika import parser as tika_parser

def get_output_file_path(src_file_path, desired_ext):
    file_name, file_ext = src_file_path.split("/")[-1].split(".")
    return os.path.join("/".join(src_file_path.split("/")[:-1]), file_name + desired_ext)

def parse_captions(scc_file_path, desired_ext):
    assert(desired_ext == ".txt"), "caption file must output to txt file"
    src_file = open(scc_file_path, "r")
    pycaps = SCCReader().read(src_file.read())
    with open(get_output_file_path(scc_file_path, desired_ext), "w+") as output_file:
        for lang, caption in pycaps._captions.items():
            if lang == "en-US":
                for caption_at_timestep in caption:
                    output_file.write(
                        "{} {} {}\n".format(caption_at_timestep.format_start(),
                                            caption_at_timestep.format_end(),
                                            caption_at_timestep.get_text()))

def parse_doc_images(doc_img_file_path, desired_ext):
    assert(desired_ext[0] == ".txt" and desired_ext[1] == ".pkl"), "document image file must output " \
                                                                "content to txt file and metadata info to pkl file"
    doc_img_parsed = tika_parser.from_file(doc_img_file_path)
    with open(get_output_file_path(doc_img_file_path, desired_ext[0]), "w") as content_output_file:
        content_output_file.writelines(doc_img_parsed["content"])
    with open(get_output_file_path(doc_img_file_path, desired_ext[1]), "w") as metadata_output_file:
        metadata_output_file.writelines(doc_img_parsed["metadata"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str)
    args = parser.parse_args()

    for src_file_path in os.listdir(args.dir):
        try:
            full_src_file_path = os.path.join(args.dir, src_file_path)
            if src_file_path.endswith(".scc"):
                parse_captions(full_src_file_path, ".txt")
            if src_file_path.endswith(".pdf") or src_file_path.endswith(".docx") or src_file_path.endswith(".doc"):
                parse_doc_images(full_src_file_path, (".txt", ".pkl"))
        except Exception as e:
            print("error with " + src_file_path, traceback.print_exc())
            continue
