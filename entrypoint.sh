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
params="\"${BP_NAME}\" -s 03-Live --name \"${ENV_NAME}\" -d \"${DURATION}\""

if [ "$TIMEOUT" -gt 0 ]; then
    params="$params -w -t ${TIMEOUT}"
fi
if [ ! -z "${INPUTS}" ]; then
    IFS=',' # Set comma as the internal field separator
    for input in ${INPUTS}; do
        params="$params -i \"${input}\""
    done
    unset IFS # Reset IFS to default
fi
if [ ! -z "${BRANCH}" ]; then
    params="$params -b \"${BRANCH}\""
fi


 
command="/Quali.Torque.Cli/torque-cli env start ${params} --token $TORQUE_TOKEN --detail"
echo "The following command will be executed: ${command}"

echo "Starting the environment..."
response=$(eval $command 2>&1)
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Error: Failed to start environment"
    echo "$response"
    exit $exit_code
fi
# response=$(torque --disable-version-check env start ${params} --output=json) || exit 1
environment_id=$(echo "$response" | tr -d '"')
echo "Started environment with id '${environment_id}'"

response=$(/Quali.Torque.Cli/torque-cli env get ${environment_id} --token $TORQUE_TOKEN --detail 2>&1)
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Error: Failed to get environment details"
    echo "$response"
    exit $exit_code
fi
environment_details=$(echo "$response" | tr -d "\n")

echo "Writing data to outputs"
echo "environment_id=${environment_id}" >> $GITHUB_OUTPUT
echo "environment_details=${environment_details}" >> $GITHUB_OUTPUT
