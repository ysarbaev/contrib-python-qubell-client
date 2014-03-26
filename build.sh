#!/bin/bash

nosetests --version

nosetests qubell/tests
if [[ ${TRAVIS_PULL_REQUEST} == "false" ]]; then
  nosetests integration_tests
fi