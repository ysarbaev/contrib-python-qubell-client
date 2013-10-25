
## Python-qubell-client

### qubellclient/private
Library to access qubell via dev api.


### qubellclient/tests
Tests in python unittests format.
Primary goal is to test qubell platform functionality using different api's (now only private)


### Pre-requisites

Packages required:
python2.7 or greater
python-requests
python-yaml
python-nose
python-testtools


### Configuration
To configure tests look at qubellclient/tests/base.py


### Adding tests
See examples at qubellclient/tests/*


### Running

#### Run single test
    nosetests -s -v qubellclient.tests.instance.test_actions:InstanceTest.test_actions

#### Run all tests
    nosetests -s -v qubellclient/tests/
or just
    nosetests

