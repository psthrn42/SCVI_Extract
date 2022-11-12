# SCVI Extract
Python scripts to extract data formats from the pokemon games 'Scarlet' and 'Violet'

## How to use
1. Create the folders 'files' and 'tools' in the root directory of the repo.
2. Place the files 'flatc.exe' and 'oo2core_6_win64.dll' in the 'tools' folder.
3. Place the files 'data.trpfs' and 'data.trpfd' (from the romfs) into the 'files' folder.

### TRPFS Extraction
1. Run the script 'trpfs_extract.py' with no arguments.
2. The extracted files will be located in a folder called 'output' in the root directory.

### TRPAK Extraction
1. Run the script 'trpak_extract.py' with the full path of the trpak you want to extract as an argument.
2. The extracted files will be located alongside the input file.

### Full Extraction (Note: this might take a while)
1. Run the script 'full_extract.py' with no arguments
2. The extracted files will be located in a folder called 'output' in the root directory.
