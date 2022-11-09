#!/bin/sh -l

BP_NAME=$1
ENV_NAME=$2
BRANCH=$3
DURATION=$4
TIMEOUT=$5
INPUTS=$6

echo "Running torque start environment command"
params="${BP_NAME} -n ${ENV_NAME} -d ${DURATION}"

if [ "$TIMEOUT" -gt 0 ]; then
    params="$params -w -t ${TIMEOUT}"
fi
if [ ! -z ${INPUTS} ]; then
    params="$params -i ${INPUTS}"
fi
if [ ! -z ${BRANCH} ]; then
    params="$params -b ${BRANCH}"
fi

echo "The following parameters will be used: ${params}"

echo "Starting the environment..."
environment_id=$(torque --disable-version-check env start ${params} --output=json | tr -d '"') || exit 1
echo "Started environment with id '${environment_id}'"

environment_details=$(torque --disable-version-check env get ${environment_id} --output=json --detail | tr -d "\n") || exit 1

echo "Writing data to outputs"
echo "environment_id=${environment_id}" >> $GITHUB_OUTPUT
echo "environment_details=${environment_details}" >> $GITHUB_OUTPUT
