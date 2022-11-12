import os
from pathlib import Path
import subprocess
import sys
import json
from ctypes import cdll, c_char_p, create_string_buffer

schema_dir = "schemas"
info_dir = "info"
tool_dir = "tools"

def OodleDecompress(raw_bytes, size, output_size):
    handle = cdll.LoadLibrary(tool_dir + "\\oo2core_6_win64.dll")
    output = create_string_buffer(output_size)
    output_bytes = handle.OodleLZ_Decompress(c_char_p(raw_bytes), size, output, output_size, 0, 0, 0, None, None, None, None, None, None, 3)
    return output.raw

def ParseFlatbuffer(filename):
    command = tool_dir + "\\flatc.exe --raw-binary -o info --strict-json --defaults-json -t schemas\\trpak.fbs -- " + filename
    subprocess.call(command)

def WriteFiles():
    global filename
    json_path = info_dir + "\\" + Path(filename).stem + ".json"
    with open(json_path, mode="r") as parsed_file:
        data = json.load(parsed_file)
        for i in range(len(data["files"])):
            out_file = open(os.path.dirname(filename) + "\\" + hex(data["hashes"][i]), mode="wb")
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
