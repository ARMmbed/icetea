#!/usr/bin/env bash
echo "This is smoke build!"


cd nanosimulator
cp CliNode ..
cd ..
sudo setcap cap_net_admin,cap_net_raw+ep CliNode
getcap CliNode

git clone --recursive git@github.com:ARMmbed/mbed-clitest-suites.git

cd mbed-clitest-suites/thread-tests
git checkout master

cd ../6lowpan
git checkout master


cd ../../mbed-clitest

#sudo python setup.py install
python clitest.py --suitedir ../mbed-clitest-suites/suites --suite mbed_clitest_smoke --tcdir ../mbed-clitest-suites --type simulate -v --use_sniffer -w --with_logs --bin ../CliNode --failure_return_value
