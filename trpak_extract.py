import os
from pathlib import Path
import subprocess
import json
import glob
from ctypes import cdll, c_char_p, create_string_buffer
import platform
import sys

schema_dir = "schemas"
info_dir = "info"
tool_dir = "tools"

def GetPathSeparator():
    if platform.system() == "Linux":
        return "/"
    return "\\"

def GetFlatcName():
    if platform.system() == "Linux":
        return "flatc"
    return "flatc.exe"

def GetOodleLibName(version):
    if platform.system() == "Linux":
        return "liblinoodle.so"
    names = ["oo2core_6_win64.dll", "oo2core_7_win64.dll", "oo2core_8_win64.dll"]
    return names[version]

def OodleDecompress(raw_bytes, size, output_size):
    filename = Path("")
    for i in range(3):
        filename = Path(tool_dir + GetPathSeparator() + GetOodleLibName(i))
        if filename.exists():
            break
    if not filename.exists():
        sys.exit("\noodle decompress library not found!")
    os.chdir(tool_dir)
    handle = cdll.LoadLibrary("." + GetPathSeparator() + str(filename.name))
    output = create_string_buffer(output_size)
    output_bytes = handle.OodleLZ_Decompress(c_char_p(raw_bytes), size, output, output_size, 0, 0, 0, None, None, None, None, None, None, 3)
    os.chdir("..")
    return output.raw

def ParseFlatbuffer(filename):
    command = [tool_dir + GetPathSeparator() + GetFlatcName(), "--raw-binary", "-o", "info", "--strict-json", "--defaults-json", "-t", "schemas" + GetPathSeparator() + "trpak.fbs", "--", filename]
    subprocess.call(command)

def WriteFiles():
    global filename
    json_path = info_dir + GetPathSeparator() + Path(filename).stem + ".json"
    with open(json_path, mode="r") as parsed_file:
        data = json.load(parsed_file)
        for i in range(len(data["files"])):
            out_file = open(os.path.dirname(filename) + GetPathSeparator() + hex(data["hashes"][i]), mode="wb")
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

filename = sys.argv[1]
ParseFlatbuffer(filename)
WriteFiles()
