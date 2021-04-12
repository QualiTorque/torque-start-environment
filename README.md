# colony-start-sb-action

This action integrates CloudShell Colony into your CI/CD pipeline.

You can configure your available build workflows to create a sandbox from any blueprint, start your tests and end the sandbox when finished (using [colony-end-sb-action](https://github.com/QualiSystemsLab/colony-end-sb-action)).

To use this GitHub Action you need to have an account in CloudShell Colony and API token.

## Usage

```yaml
- name: QualiSystemsLab/colony-start-sb-action@v0.0.1
  with:
    # The name of the Colony Space your repository is connected to
    space: TestSpace

    # Provide the long term Colony token which could be generated
    # on the 'Integrations' page under the Colony's Settings page
    colony_token: ${{ secrets.COLONY_TOKEN }}

    # Provide the name of the blueprint you would like to use as a source for the sandbox.
    blueprint_name: WebApp

    # [Optional] Provide a name for the Sandbox. If not set, the name will be generated automatically
    # using the following pattern <BlueprintName>-build-<RunNumber>
    sandbox_name: demo-sb

    # [Optional] Your Colony account name. The account name is equal to your subdomain in the Colony URL.
    # If set, an action prints a link to the Sandbox to workflow log 
    colony_account: demo-acct

    # [Optional] Run the Blueprint version from a remote Git branch. If not provided, the branch
    # currently connected to Colony will be used
    branch: development

    # [Optional] The Blueprints inputs can be provided as a comma-separated list of key=value
    # pairs. For example: key1=value1, key2=value2.
    inputs: 'PORT=8080,AWS_INSTANCE_TYPE=m5.large'

    # [Optional] A comma-separated list of artifacts per application. These are relative to the
    # artifact repository root defined in Colony. Example: appName1=path1, appName2=path2.
    artifacts: 'flask-app=artifacts/latest/flask_app.tar.gz,mysql=artifacts/latest/mysql.tar.gz'

    # [Optional] Set the timeout in minutes to wait for the sandbox to become active. If not set, an
    # action just starts a sandbox and return its ID without waiting for 'Active' status
    timeout: 15

    # [Optional] Set the Sandbox duration in minutes. The Sandbox will automatically de-provision at 
    # the end of the provided duration. Default is 120 minutes
    duration: 60
```
### Action outputs

- `sandbox_id` - The ID of launched Colony Sandbox. Will be returned regardless timeout is set or not
- `sandbox_details` - The JSON string representing the full sandbox details
- `sandbox_shortcuts` - The JSON string representing mapping between apps and links to access them. Example:
    ```json
    {
        "app1": ["http://app1-path.com:80", "http://app1-path.com:6060"],
        "app2": ["http://app2-path.com:8080", "http://app2-path.com:3130"]
    }
    ```

## Examples

### CI

The following example demonstrates how this action could be used in combination with [colony-end-sb-action](https://github.com/QualiSystemsLab/colony-end-sb-action) to run tests against some flask web application deployed inside Colony Sandbox

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
    - uses: actions/checkout@v1
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
        
  test-with-colony:
    needs: build-and-publish
    runs-on: ubuntu-latest
    
    steps:
    - name: Start Colony Sandbox
      id: start-sandbox
      uses: QualiSystemsLab/colony-start-sb-action@v0.0.1
      with:
        space: Demo
        blueprint_name: WebApp
        colony_token: ${{ secrets.COLONY_TOKEN }}
        duration: 120
        timeout: 30
        artifacts: 'flask-app=latest/flaskapp.lates.tar.gz'
        inputs: 'PORT=8080,AWS_INSTANCE_TYPE=m5.large'
    
    - name: Testing
      id: test-app
      run: |
        echo "Running tests against sandbox with id: ${{ steps.start-sandbox.outputs.sandbox_id }}
        shortcuts=${{ steps.start-sandbox.sandbox_shortcuts }}
        readarray -t shortcuts <<< "$(jq '. | .flask-app[]' <<< '${{ steps.start-sandbox.sandbox_shortcuts }}')"
        for shortcut in ${shortcuts[@]}; do
            "Do something with this ${shortcut}."
        done

    - name: Stop sandbox
      uses: QualiSystemsLab/colony-end-sb-action@v0.0.1
      with:
        space: Demo
        sandbox_id: ${{ steps.start-sandbox.outputs.sandbox_id }}
        colony_token: ${{ secrets.COLONY_TOKEN }} 
```
### Blueprints validation

If you work on Colony Blueprints repository you can extend the validation capabilities of your workflow by using a combination of [validate](https://github.com/QualiSystemsLab/colony-validate-bp-action) action and start/stop actions. So that, you can ensure that not only is your blueprint valid but also the working sandbox could be launched using it.

Please note that the example also shows how you can force the sandbox to terminate if it was not ready within a timeout or was deployed with errors.

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

    - name: Colony validate blueprints
      uses: QualiSystemsLab/colony-validate-bp-action@v0.0.1
      with:
        space: Demo
        files_list: blueprints/empty-bp-empty-app.yaml
        colony_token: ${{ secrets.COLONY_TOKEN }}

  some-parallel-job:
    needs: validate
    runs-on: ubuntu-latest

    steps:
    - name: Sleep for 100s
      uses: juliangruber/sleep-action@v1
      with:
        time: 100s

  start-sb:
    needs: validate
    runs-on: ubuntu-latest

    steps:
    - name: Start sandbox
      id: start-sandbox
      uses: QualiSystemsLab/colony-start-sb-action@v0.0.1
      with:
        space: Demo
        blueprint_name: empty-bp-empty-app
        colony_token: ${{ secrets.COLONY_TOKEN }}
        branch: master
        duration: 30
        timeout: 10
    - name: End sandbox on failure
      if: failure() && steps.start-sandbox.outputs.sandbox_id != ''
      uses: QualiSystemsLab/colony-end-sb-action@v0.0.1
      with:
        space: Demo
        sandbox_id: ${{steps.start-sandbox.outputs.sandbox_id}}
        colony_token: ${{ secrets.COLONY_TOKEN }}

    outputs:
      sandbox_id: ${{ steps.start-sandbox.outputs.sandbox_id }}

  finish-all:
    needs: [start-sb, some-parallel-job]
    runs-on: ubuntu-latest

    steps:
    - name: Stop sandbox
      uses: QualiSystemsLab/colony-end-sb-action@v0.0.1
      with:
        space: Demo
        sandbox_id: ${{needs.start-sb.outputs.sandbox_id}}
        colony_token: ${{ secrets.COLONY_TOKEN }}
```
