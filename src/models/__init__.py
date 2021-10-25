import os
import glob
import importlib

#Dynamically add *_model.py files to flask application
for f in glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"**","*_model.py"),recursive=True):
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3],f)
    mod = f.replace(os.sep,".").split("online-claims-submission-api",1)[1][:-3]
    mod = mod.replace(".","",1)
    importlib.import_module(mod)
    