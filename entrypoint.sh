#!/bin/sh -l

BP_NAME=$1
SB_NAME=$2
BRANCH=$3
DURATION=$4
TIMEOUT=$5
INPUTS=$6

echo "Running torque start sandbox command"
params="\"${BP_NAME}\" -n \"${SB_NAME}\" -b \"${BRANCH}\" -d ${DURATION}"

env

if [ "$TIMEOUT" -gt 0 ]; then
    params="$params -w -t ${TIMEOUT}"
fi
if [ ! -z ${INPUTS} ]; then
    params="$params -i \"${INPUTS}\""
fi

echo "The following parameters will be used: ${params}"

sandbox_id=`torque sb start ${params} --output=json`

echo "Started sandbox with id '${sandbox_id}'"
echo "sandbox_id=$sandbox_id" >> $GITHUB_OUTPUT