#!/bin/sh -l

BP_NAME=$1
SB_NAME=$2
BRANCH=$3
DURATION=$4
TIMEOUT=$5
INPUTS=$6

echo "Running torque start sandbox command"
params="${BP_NAME} -n ${SB_NAME} -d ${DURATION}"

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

sandbox_id=$(torque --disable-version-check sb start ${params} --output=json | tr -d '"') || exit 1
echo "Started sandbox with id '${sandbox_id}'"

sandbox_details=$(torque --disable-version-check sb get ${sandbox_id} --output=json --detail | tr -d "\n") || exit 1

echo "sandbox_id=${sandbox_id}" >> $GITHUB_OUTPUT
echo "sandbox_details=${sandbox_details}" >> $GITHUB_OUTPUT
