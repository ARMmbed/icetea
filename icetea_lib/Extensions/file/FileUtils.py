from icetea_lib.tools.file.FileUtils import LockFile, removeFile, renameFile

"""
This file exists for backwards compatibility. the file module has been relocated
to icetea_lib.tools but some other applications import if from this location.

Backwards compatibility achieved by importing the contents of the module contents from the new
location to this module.
"""