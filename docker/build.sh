#!/usr/bin/env bash

app="spider-platform"
version="latest"
image="${app}:${version}"

base_dir=$(cd `dirname "$0"`/.. && pwd)
config_dir=${base_dir}/docker
cd ${base_dir}

# build docker image
docker build -t ${image} -f ${config_dir}/${app} ${base_dir}
docker stop ${app}
docker rm ${app}
docker run --name ${app} -d ${image}
docker images|grep none|awk '{print $3}'|xargs docker rmi
