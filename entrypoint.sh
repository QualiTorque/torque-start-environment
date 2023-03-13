#!/bin/sh -l

BP_NAME="$1"
REPO_NAME="$2"
ENV_NAME="$3"
BRANCH="$4"
DURATION="$5"
TIMEOUT="$6"
INPUTS="$7"

ENV_NAME="${ENV_NAME:-$BP_NAME-build-$GITHUB_RUN_NUMBER}"

echo "Running torque start environment command"
params="\"${BP_NAME}\" --repo \"${REPO_NAME}\" -n \"${ENV_NAME}\" -d \"${DURATION}\""

if [ "$TIMEOUT" -gt 0 ]; then
    params="$params -w -t ${TIMEOUT}"
fi
if [ ! -z "${INPUTS}" ]; then
    params="$params -i \"${INPUTS}\""
fi
if [ ! -z "${BRANCH}" ]; then
    params="$params -b \"${BRANCH}\""
fi

command="torque --disable-version-check env start ${params} --output=json"
echo "The following command will be executed: ${command}"

echo "Starting the environment..."
response=$(eval $command) || exit 1
# response=$(torque --disable-version-check env start ${params} --output=json) || exit 1
environment_id=$(echo "$response" | tr -d '"')
echo "Started environment with id '${environment_id}'"

response=$(torque --disable-version-check env get ${environment_id} --output=json --detail) || exit 1
environment_details=$(echo "$response" | tr -d "\n")

echo "Writing data to outputs"
echo "environment_id=${environment_id}" >> $GITHUB_OUTPUT
echo "environment_details=${environment_details}" >> $GITHUB_OUTPUT
