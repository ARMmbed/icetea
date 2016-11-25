# Rest API for clitest
The purpose of the extension is to provide a generic API for HTTP methods for clitest framework so that testers can develop and run test for applications that host a HTTP web service. 

The extension is built on top of the python requests library and it contains implementations of HTTP GET, POST, PUT and DELETE methods that wrap the corresponding requests methods to a simple interface that can be extended to use all requests library parameters for those methods if needed. 

#Structure
The API is built into two parts:

* a simple wrapper that is used to extend the Bench class with a link to the HttpApi class [here](../mbed_clitest/Extensions/HttpApi.py).
* the interface logic in [Api.py](../mbed_clitest/Extensions/HTTP/Api.py)

All logic is contained in Api.py. 

#HttpApi
The HttpApi object is the class that wraps the HTTP methods into a simple interface for developers.

When constructing the object you can supply a certificate file path or tuple, a dictionary of default headers and a custom logger.
The default headers will be overwritten by headers supplied in method calls if you supply overlapping headers. Otherwise they are merged.

* Bench.HttpApi(host, headers=None, cert=None, logger=None)

##Method prototypes
The methods of the API are very similar to those of the requests library. They take most of the same arguments and raise the same exceptions should the request fail.

* setHost(host)
* setLogger(logger)
* setHeader(key, value)
* setCert(cert)
* get(self, path, headers=None, params=None, expected=200, raiseException=True, **kwargs)
* post(self, path, data=None, json=None, headers=None, expected=200, raiseException=True, **kwargs)
* put(self, path, data=None, headers=None, expected=200, raiseException=True, **kwargs)
* delete(self, path, headers=None, expected=200, raiseException=True, **kwargs)

These methods can be accessed from testcase by creating the interface object with self.HttpApi(), which creates a wrapper around the bottom layer of the interface to 
enable raising TestStepFail exceptions without hardwiring them into the bottom layer.

The HTTP methods all have parameters expected and raiseException. For defining an expected return code from the server you can use the expected parameter.
If the response return code is not the expected value, the interface either raises a TestStepFail exception (which will fail a test case unless it is caught) or logs the expected and received return codes and returns the response.
This behaviour is controlled by the raiseException parameter. If expected is set to None this check is skipped and the response is returned.

The kwargs field takes all arguments you can supply to the requests library methods. Take a look at the documentation of requests [here](http://docs.python-requests.org/en/master/api/) for more information.

##Logger
The API uses a default, barebones console logger unless you provide it with a custom logger. The logger name you can look out for is HttpApi.
The bench logger is used when creating the interface from testcase with self.HttpApi

##Example use in a test case
The interface can be accessed from a testcase by calling http = self.HttpApi with parameters as described above. After that you can use get, post, put and delete methods
with http.get() etc.

Short example of get() in test case:

api = self.HttpApi("http://google.com")
response = api.get("/")

A very simple example use case can be found in [examples](../examples/sample_http.py)


