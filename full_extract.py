import struct
import os
import subprocess
import json
from pathlib import Path
import sys
from ctypes import cdll, c_char_p, create_string_buffer
import glob

fs_magic = "ONEPACK"
file_dir = "files"
schema_dir = "schemas"
info_dir = "info"
tool_dir = "tools"
output_dir = "output"
init_offset = 0
name_dict = {}
hash_dict = {}

def FNV1a64(input_str):
    fnv_prime = 1099511628211
    offset_basis = 14695981039346656837
    for i in input_str:
        offset_basis ^= ord(i)
        offset_basis = (offset_basis * fnv_prime) % (2**64)
    return offset_basis

def ExtractFS():
    print("Extracting data from trpfs file...")
    with open(file_dir + "\data.trpfs", mode="rb") as fs, open(file_dir + "\\fs_data_separated.trpfs", mode="wb") as fs_sep:
        magic = fs.read(8).decode("utf-8") [:-1]
        assert (magic == fs_magic), "Invalid trpfs magic!"
        global init_offset
        init_offset = struct.unpack('Q', fs.read(8))[0]
        fs.seek(0, os.SEEK_END)
        eof_offset = fs.tell()
        fs.seek(init_offset)
        fs_sep.write(fs.read(eof_offset - init_offset))

    command = tool_dir + "\\flatc.exe --raw-binary -o info --strict-json --defaults-json -t schemas\\trpfs.fbs -- files\\fs_data_separated.trpfs"
    subprocess.call(command)

def ExtractFD():
    print("Extracting data from trpfd file...")
    command = tool_dir + "\\flatc.exe --raw-binary -o info --strict-json --defaults-json -t schemas\\trpfd.fbs -- files\\data.trpfd"
    subprocess.call(command)
    
    with open(info_dir + "\\names_original.txt", mode="r") as onames_file, open(info_dir + "\\names_changed.txt", mode="r") as cnames_file:
        onames = onames_file.read().splitlines() 
        cnames = cnames_file.read().splitlines() 
        for i in range(len(onames)):
            name_dict[onames[i]] = cnames[i]
            hash_dict[onames[i]] = FNV1a64(onames[i])

def WriteFiles():
    print("Extracting files...")
    with open(info_dir + "\data.json", mode="r") as fd_info, open(info_dir + "\\fs_data_separated.json", mode="r") as fs_info, open(file_dir + "\data.trpfs", mode="rb") as data:
        fd = json.load(fd_info)
        fs = json.load(fs_info)
        num_files = len(fs["file_offsets"])
        global init_offset
        fs["file_offsets"].append(init_offset)
        
        for i in range(num_files):
            offset = fs["file_offsets"][i]
            end_offset = fs["file_offsets"][i + 1]
            name_hash = fs["hashes"][i]

            path = "ERROR_NO_MATCHING_FILENAME"
            for j in fd["paths"]:
                if name_hash == hash_dict[j]:
                    path = output_dir + "/" + name_dict[j]
            print(path)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            data.seek(offset)
            out_file = open(path, mode="wb+")
            out_file.write(data.read(end_offset - offset))
            out_file.close()
    print("\nExtraction complete!")

def OodleDecompress(raw_bytes, size, output_size):
    handle = cdll.LoadLibrary(tool_dir + "\\oo2core_6_win64.dll")
    output = create_string_buffer(output_size)
    output_bytes = handle.OodleLZ_Decompress(c_char_p(raw_bytes), size, output, output_size, 0, 0, 0, None, None, None, None, None, None, 3)
    return output.raw

def ParseFlatbuffer(foldername):    
    for filename in glob.glob(os.path.join(foldername, "**/*.trpak"), recursive=True):
        print("Parsing " + filename)
        command = tool_dir + "\\flatc.exe --raw-binary -o info --strict-json --defaults-json -t schemas\\trpak.fbs -- " + filename
        subprocess.call(command)

        folderName = os.path.dirname(filename) + "\\" + os.path.basename(filename.replace(".trpak", ""))

        if not os.path.exists(folderName):
            os.mkdir(folderName)

        json_path = info_dir + "\\" + Path(filename).stem + ".json"
        with open(json_path, mode="r") as parsed_file:
            data = json.load(parsed_file)
            for i in range(len(data["files"])):
                hashValue = data["hashes"][i]
                out_file = open(folderName + "\\" + hex(hashValue), mode="wb")
                compressed_data = []
                data_size = 0
                for j in data["files"][i]["data"]:
                    data_size += 1
                    compressed_data.append(j)
                if data["files"][i]["compression_type"] == "OODLE":
                    decompressed_data = OodleDecompress(bytes(compressed_data), data_size, data["files"][i]["decompressed_size"])
                elif data["files"][i]["compression_type"] == "NONE":
                    decompressed_data = bytes(compressed_data)
                out_file.write(decompressed_data)
                out_file.close()
        os.remove(filename)

if __name__ == "__main__":

    if not os.path.exists(output_dir):
        ExtractFS()
        ExtractFD()
        WriteFiles()
    ParseFlatbuffer(output_dir)
