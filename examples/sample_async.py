"""
Copyright 2016 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Import Bench Class
from mbed_test.bench import Bench


class Testcase(Bench):
    def __init__(self):
        Bench.__init__(
            self,
            name="sample_process_async_testcase",
            title="unittest exception in testcase",
            status="development",
            type="acceptance",
            purpose="dummy",
            requirements={
                "duts": {
                    '*': {
                        "count": 200,
                        "type": "process",
                        "application": {
                            "name": "sample", "version": "1.0",
                            "bin": "test/dut/dummyDut"
                        }
                    }
                }
            }
        )

    def case(self):
        # launch a reverse DNS lookup on each node, in parrallel.
        # The response will be waited once the program will try to access it
        responses = self.command("*", "nslookup 8.8.8.8", async=True)

        # verify that the responses match expectations
        for response in responses:
            # At this point, if the response is not yet available, the system will
            # block and wait for it. In the meantime, other responses will continue
            # their progress.
            response.verifyMessage("google-public-dns-a.google.com")
