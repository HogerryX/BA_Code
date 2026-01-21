## Setup the conda environment
1. Install conda
2. Open termianl in root folder
3. Execute conda env create -f environment.yml

## Setup of the RAG-System
1. Create a folder "data" in the root folder
2. Create a folder "files" in the data folder
3. Move all files you want to be part of the knowledge base in the files folder
4. Open a terminal in the root folder
5. Execute conda activate \<environment name\>
6. Execute streamlit run src/ui/streamlit_app.py
8. The System starts and the index will be created automaticly
9. The index files are safed in data/index
