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

from datetime import datetime
import time
import re

class CliResponseParser:
    # constructor
    def __init__(self):
        self.parsers = {
            'ping': self.__pingParser,
        }

    # parse response
    def parse(self, *args, **kwargs):
        cmd = args[0]
        resp = args[1]
        if cmd in self.parsers:
            try:
                return self.parsers[cmd](resp)
            except Exception as err:
                print(err)
        return {}

    # Private functions

    # regexp search with one value to return
    def __find_one(self, line, lookup):
        m = re.search(lookup, line)
        if m:
            if m.group(1):
                return m.group(1)
        return False

    # regex search with multiple values to return
    def __find_multiple(self, line, lookup):
        m = re.search(lookup, line)
        if m:
            ret = []
            for i in range(1,len(m.groups())+1):
                ret.append(m.group(i))
            if ret:
                return ret
        return False

    # commands parsers

    # response parser for ping
    def __pingParser(self, response):
        results = {
            'sent': -1,
            'received': -1,
            'lost': -1,
            'duplicates': 0,
            'min': -1,
            'max': -1,
            'avg': -1,
            'errors': 0,
            'timestamp': None
        }

        results['timestamp'] = time.time()

        respLines = response.lines
        for line in respLines:
            # Match line
            matches = {}
            matches["cli_ipv6_reply"] = re.match(r'Reply\[\d{4}\]\Wfrom\W([\da-f\:]+):\Wbytes=(\d+)\Wtime[=<>](\d+)ms', line)
            matches["cli_stats1"] = re.match(r'^\s*Packets: Sent = (\d+), Received: (\d+), Lost = (\d+)', line)
            matches["cli_stats1_no_lost"] = re.match(r'^\s*Packets: Sent = (\d+), Received: (\d+),', line)
            matches["cli_stats2"] = re.match(r'\s*Minimum = (-{0,1}\d+)ms, Maximum = (-{0,1}\d+)ms, Average = (\d+)ms', line)

            matches["win_ipv4_reply"] = re.match(r'Reply from (.*?): bytes=(\d+) time=(\d+)ms TTL=(\d+)', line)
            matches["win_stats1"] = re.match(r'^\s*Packets: Sent = (\d+), Received = (\d+), Lost = (\d+)', line)
            matches["win_stats2"] = matches["cli_stats2"]

            matches["linux_ipvx_reply"] = re.match(r"^(\d+) bytes from (.*?): icmp_seq=(\d+) ttl=(\d+) time=(\d+(?:\.\d+){0,1}) ms$", line)
            matches["linux_ipv4_reply_domain"] = re.match(r"^(\d+) bytes from .*? \((.*?)\): icmp_seq=(\d+) ttl=(\d+) time=(\d+(?:\.\d+){0,1}) ms$", line)
            matches["linux_ipvx_stats1"] = re.match(r"^(\d+) packets transmitted, (\d+) received, (\d+(?:\.\d+){0,1})% packet loss, time (\d+)ms$", line)
            matches["linux_ipvx_stats1_dup"] = re.match(r"^(\d+) packets transmitted, (\d+) received, \+(\d+) duplicates, (\d+(?:\.\d+){0,1})% packet loss, time (\d+)ms$", line)
            matches["linux_ipvx_stats1_ureach"] = re.match(r"^(\d+) packets transmitted, (\d+) received, \+(\d+) errors, (\d+(?:\.\d+){0,1})% packet loss, time (\d+)ms$", line)
            matches["linux_ipvx_stats2"] = re.match(r"^rtt min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) ms", line)


            if not any([matches[match] for match in matches]):
                continue

            # Go with the first successful match
            (match_name, match) = next((match, matches[match]) for match in matches if matches[match] is not None)

            if match_name == "cli_ipv6_reply" or match_name == "win_ipv4_reply":
                _from = match.group(1)
                bytes = int(match.group(2))
                rtt_time = int(match.group(3))

                response = {'bytes': bytes, 'time': rtt_time}
                if _from not in results:
                    results[_from] = []
                results[_from].append(response)

            elif match_name in ["linux_ipvx_reply", "linux_ipv4_reply_domain"]:
                _from = match.group(2)
                bytes = int(match.group(1))
                rtt_time = float(match.group(5))

                response = {'bytes': bytes, 'time': rtt_time}
                if _from not in results:
                    results[_from] = []
                results[_from].append(response)

            elif match_name in ["cli_stats1", "win_stats1"]:
                results['sent'] = int(match.group(1))
                results['received'] = int(match.group(2))
                results['lost'] = int(match.group(3))

            elif match_name in ["cli_stats1_no_lost"]:
                results['sent'] = int(match.group(1))
                results['received'] = int(match.group(2))
                results['lost'] = 0

            elif match_name in ["cli_stats2", "win_stats2"]:
                results['min'] = int(match.group(1))
                results['max'] = int(match.group(2))
                results['avg'] = int(match.group(3))

            elif match_name in ["linux_ipvx_stats1"]:
                results['sent'] = int(match.group(1))
                results['received'] = int(match.group(2))
                results['lost'] = results['sent'] - results['received']

            elif match_name in ["linux_ipvx_stats1_dup"]:
                results['sent'] = int(match.group(1))
                results['received'] = int(match.group(2))
                results['duplicates'] = int(match.group(3))
                results['lost'] = results['sent'] - results['received']

            elif match_name in ["linux_ipvx_stats1_ureach"]:
                results['sent'] = int(match.group(1))
                results['received'] = int(match.group(2))
                results['errors'] = int(match.group(3))
                results['lost'] = results['sent'] - results['received']

            elif match_name in ["linux_ipvx_stats2"]:
                results['min'] = float(match.group(1))
                results['avg'] = float(match.group(2))
                results['max'] = float(match.group(3))

        return results
