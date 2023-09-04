#!/bin/bash
app="docker.waramity"
docker build -t ${app} .
docker run -d -p 56733:80 \
  --link waramity-mongo:mongo \
  --name=${app} \
  -v $PWD:/app ${app}
