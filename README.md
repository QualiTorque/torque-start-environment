# torque-start-environment

This action integrates Torque into your CI/CD pipeline.

You can configure your available build workflows to create an environment from any blueprint, start your tests and end the environment when finished (using [torque-end-environment](https://github.com/QualiTorque/torque-end-environment)).

To use this GitHub Action you need to have an account in Torque and an API token.

> **_NOTE:_** Torque spec 1 support is available in releases <0.1.0 

## Usage

```yaml
- name: QualiTorque/torque-start-environment@v1
  with:
    # The name of the Torque Space your repository is connected to
    space: TestSpace

    # Provide the long term Torque token. You can generate it in Torque > Settings > Integrations
    # or via the REST API.
    torque_token: ${{ secrets.TORQUE_TOKEN }}

    # Provide the name of the blueprint to be used as a source for the environment.
    blueprint_name: WebApp

    # [Optional] Provide a name for the environment. If not set, the name will be generated automatically
    # using the following pattern <BlueprintName>-build-<RunNumber>
    environment_name: demo-env

    # [Optional] You can provide the blueprint's inputs as a comma-separated list of key=value
    # pairs. For example: key1=value1, key2=value2.
    inputs: 'PORT=8080,AWS_INSTANCE_TYPE=m5.large'

    # [Optional] Provide the url string. In rare cases you migth want to override the main
    # Torque server address 'https://portal.qtorque.io'. 
    torque_url: "https://portal.qtorque.io"

    # [Optional] Set the timeout to wait (in minutes) for the environment to become active. If not set, an
    # action just starts an environment and returns its ID without waiting for 'Active' status.
    timeout: 15

    # [Optional] Set the environment duration in minutes. The environment will automatically de-provision at 
    # the end of the provided duration. Default is 120 minutes.
    duration: 60
```
### Action outputs

- `environment_id` - ID of the launched Torque environment. environment_id is returned regardless if timeout is set or not
- `environment_details` - JSON string that represents the full environment details

## Examples

### CI

The following example demonstrates how to use this action in combination with [torque-end-environment](https://github.com/QualiTorque/torque-end-environment) to run tests against some flask web application deployed inside a Torque environment:

```yaml
name: CI
on:
  pull_request:
    branches:
      - master

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Make artifact
      id: build
      run: |
        mkdir -p workspace
        tar -zcf workspace/flaskapp.latest.tar.gz -C src/ .
    - name: Upload
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
        run: aws s3 copy ./workspace/flaskapp.latest.tar.gz s3://myartifacts/latest
        
  test-with-torque:
    needs: build-and-publish
    runs-on: ubuntu-latest
    
    steps:
    - name: Start Torque Environment
      id: start-env
      uses: QualiTorque/torque-start-environment@v1
      with:
        space: Demo
        blueprint_name: WebApp
        torque_token: ${{ secrets.TORQUE_TOKEN }}
        duration: 120
        timeout: 30
        inputs: 'PORT=8080,AWS_INSTANCE_TYPE=m5.large'
    
    - name: Testing
      id: test-app
      run: |
        echo "Running tests against environment with id: ${{ steps.start-env.outputs.environment_id }}"
        echo "Do something with environment details json: ${{ steps.start-env.outputs.environment_details }}"

    - name: Stop environment
      uses: QualiTorque/torque-end-environment@v1
      with:
        space: Demo
        environment_id: ${{ steps.start-environment.outputs.environment_id }}
        torque_token: ${{ secrets.TORQUE_TOKEN }} 
```
### Blueprints validation

If you're working on Torque's blueprints repository, you can extend the validation capabilities of your workflow by using a combination of the [validate](https://github.com/QualiTorque/torque-validate-bp-action) action and start/stop actions. This way, you can both ensure your blueprint's syntax is valid and also verify that a working environment can be launched using it.

Please note that this example also shows how to force the environment to terminate if it either was not ready within a defined timeout or deployed with errors.

```yaml
name: CI
on:
  push:
    branches:
      - master
  pull_request:
    branches:
      - master

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v1

    - name: Torque validate blueprints
      uses: QualiTorque/torque-validate-blueprints@v1
      with:
        space: Demo
        files_list: blueprints/empty-bp-empty-app.yaml
        torque_token: ${{ secrets.TORQUE_TOKEN }}

  some-parallel-job:
    needs: validate
    runs-on: ubuntu-latest

    steps:
    - name: Sleep for 100s
      uses: juliangruber/sleep-action@v1
      with:
        time: 100s

  start-env:
    needs: validate
    runs-on: ubuntu-latest

    steps:
    - name: Start environment
      id: start-environment
      uses: QualiTorque/torque-start-environment@v1
      with:
        space: Demo
        blueprint_name: empty-bp-empty-app
        torque_token: ${{ secrets.TORQUE_TOKEN }}
        branch: master
        duration: 30
        timeout: 10
    - name: End environment on failure
      if: failure() && steps.start-environment.outputs.environment_id != ''
      uses: QualiTorque/torque-end-environment@v1
      with:
        space: Demo
        environment_id: ${{steps.start-environment.outputs.environment_id}}
        torque_token: ${{ secrets.TORQUE_TOKEN }}

    outputs:
      environment_id: ${{ steps.start-environment.outputs.environment_id }}

  finish-all:
    needs: [start-env, some-parallel-job]
    runs-on: ubuntu-latest

    steps:
    - name: Stop environment
      uses: QualiTorque/torque-end-environment@v1
      with:
        space: Demo
        environment_id: ${{needs.start-env.outputs.environment_id}}
        torque_token: ${{ secrets.TORQUE_TOKEN }}
```
