#JsonFile
JsonFile is an extension that provides users with an interface for writing and reading json data to and from files.

##Structure
This module is built as an extension to mbed test. It is split into two files:

* a wrapper for the extension in [FileApi.py](../mbed_test/Extensions/FileApi.py)
* The logic in [SessionFiles.py](../mbed_test/Extensions/file/SessionFiles.py)

##JsonFile class
JsonFile class is the main functional part of this extension. It contains the following public methods:

* write_file(content, filepath, filename, indent, keys_to_write)
* read_file(filepath, filename)
* write_values(data,filepath, filename, indent, keys_to_write)
* read_value(key, filepath, filename)

The class also contains one private method, _write_json(filepath, filename, writemode, content, indent)

Write_file function creates a new json file and tries to write the content to the file. If a file already exists the content is overwritten.
The content must be in a format that can be serialized by json.dump() (dictionary, list of dictionaries, string)

Write_value is used to append new entries from a dictionary into the root instance of the json data found in a file.
It reads the json data from the file into a dict, appends and merges the new keys and data and writes the new data to a temporary file.
Once the temporary file has been created, the old file is removed and the temp file is renamed to match the old file.

Data that is to be written to files with write_file or write_values can be filtered with keys_to_write parameter.
It takes a list of keys that is used to pick the data which is to be written to file from the data provided.

Read_file and read_value can be used to read an entire json document (must be valid json) or a single key from a json document.

None of the functions implement file locking and if the files are not accessible or do not exists, the are either created (write_file) or an EnvironmentError is raised.
Read_value also raises a KeyError if the key could not be found from the document.
Write_file, read_file and write_value can also raise a ValueError if the file contents could not be decoded or the data could not be encoded to json.

###Internal functionality
Internally the extension uses the python json module as well as the os module.

##Logger
You can set a custom logger for the JsonFile class when calling it's init. If a logger is not provided, it will use a bare-bones default streamlogger.

##Example use
In a mbed-test testcase you have access to this extension through bench.JsonFile:

self.jf = self.JsonFile()
self.fileName = "test_file.json"
self.filePath = "path/to/file/"
self.testJson = {"test1": "value1", "test2": "value2", "test3": "value3", "test4": "test5"}
self.jf.write_file(self.testJson, self.filePath, self.fileName, 2)
data = self.jf.read_file(self.filePath, self.fileName)

