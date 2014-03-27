#!/bin/bash

nosetests --version

nosetests -v qubell/tests
if [[ ${TRAVIS_PULL_REQUEST} == "false" ]]; then
  nosetests -v integration_tests
fi