#!/bin/bash

nosetests qubell/tests
if [[ ${TRAVIS_PULL_REQUEST} == "false" ]]; then
  nosetests test_qubell_client
fi