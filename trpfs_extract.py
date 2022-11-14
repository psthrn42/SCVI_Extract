import struct
import os
import subprocess
import json

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
    if input_str in hash_dict:
        return hash_dict[input_str]
    fnv_prime = 1099511628211
    offset_basis = 14695981039346656837
    for i in input_str:
        offset_basis ^= ord(i)
        offset_basis = (offset_basis * fnv_prime) % (2**64)
    hash_dict[input_str] = offset_basis
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
                if name_hash == FNV1a64(j):
                    if j in name_dict:
                        path = output_dir + "/" + name_dict[j]
                    else:
                        path = output_dir + "/" + j
                    break
            print(path)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            data.seek(offset)
            out_file = open(path, mode="wb+")
            out_file.write(data.read(end_offset - offset))
            out_file.close()
    print("\nExtraction complete!")

ExtractFS()
ExtractFD()
WriteFiles()
#print(hex(FNV1a64("pm0081_00_00_20146_stepout01.traef")))
