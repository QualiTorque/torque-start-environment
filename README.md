# torque-start-sb-action

This action integrates Torque into your CI/CD pipeline.

You can configure your available build workflows to create a sandbox from any blueprint, start your tests and end the sandbox when finished (using [torque-end-sb-action](https://github.com/QualiTorque/torque-end-sb-action)).

To use this GitHub Action you need to have an account in Torque and an API token.

## Usage

```yaml
- name: QualiTorque/torque-start-sb-action@v0.0.1
  with:
    # The name of the Torque Space your repository is connected to
    space: TestSpace

    # Provide the long term Torque token. You can generate it in Torque > Settings > Integrations
    # or via the REST API.
    torque_token: ${{ secrets.TORQUE_TOKEN }}

    # Provide the name of the blueprint to be used as a source for the sandbox.
    blueprint_name: WebApp

    # [Optional] Provide a name for the sandbox. If not set, the name will be generated automatically
    # using the following pattern <BlueprintName>-build-<RunNumber>
    sandbox_name: demo-sb

    # [Optional] Your Torque account name. The account name is your subdomain in the Torque URL.
    # If set, an action prints (to the workflow log) a link to the sandbox.  
    torque_account: demo-acct

    # [Optional] Run the blueprint version from a remote Git branch. If not provided, the branch
    # currently connected to Torque will be used.
    branch: development

    # [Optional] You can provide the blueprint's inputs as a comma-separated list of key=value
    # pairs. For example: key1=value1, key2=value2.
    inputs: 'PORT=8080,AWS_INSTANCE_TYPE=m5.large'

    # [Optional] A comma-separated list of artifacts per application. These are relative to the
    # artifact repository's root defined in Torque. Example: appName1=path1, appName2=path2.
    artifacts: 'flask-app=artifacts/latest/flask_app.tar.gz,mysql=artifacts/latest/mysql.tar.gz'

    # [Optional] Set the timeout to wait (in minutes) for the sandbox to become active. If not set, an
    # action just starts a sandbox and returns its ID without waiting for 'Active' status.
    timeout: 15

    # [Optional] Set the sandbox duration in minutes. The sandbox will automatically de-provision at 
    # the end of the provided duration. Default is 120 minutes.
    duration: 60
```
### Action outputs

- `sandbox_id` - ID of the launched Torque sandbox. sandbox_id is returned regardless if timeout is set or not
- `sandbox_details` - JSON string that represents the full sandbox details
- `sandbox_shortcuts` - JSON string that represents mapping between applications and the links to access them. Example:
    ```json
    {
        "app1": ["http://app1-path.com:80", "http://app1-path.com:6060"],
        "app2": ["http://app2-path.com:8080", "http://app2-path.com:3130"]
    }
    ```

## Examples

### CI

The following example demonstrates how to use this action in combination with [torque-end-sb-action](https://github.com/QualiTorque/torque-end-sb-action) to run tests against some flask web application deployed inside a Torque sandbox:

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
        
  test-with-torque:
    needs: build-and-publish
    runs-on: ubuntu-latest
    
    steps:
    - name: Start Torque Sandbox
      id: start-sandbox
      uses: QualiTorque/torque-start-sb-action@v0.0.1
      with:
        space: Demo
        blueprint_name: WebApp
        torque_token: ${{ secrets.TORQUE_TOKEN }}
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
            echo "Do something with this ${shortcut}."
        done

    - name: Stop sandbox
      uses: QualiTorque/torque-end-sb-action@v0.0.1
      with:
        space: Demo
        sandbox_id: ${{ steps.start-sandbox.outputs.sandbox_id }}
        torque_token: ${{ secrets.TORQUE_TOKEN }} 
```
### Blueprints validation

If you're working on Torque's blueprints repository, you can extend the validation capabilities of your workflow by using a combination of the [validate](https://github.com/QualiTorque/torque-validate-bp-action) action and start/stop actions. This way, you can both ensure your blueprint's syntax is valid and also verify that a working sandbox can be launched using it.

Please note that this example also shows how to force the sandbox to terminate if it either was not ready within a defined timeout or deployed with errors.

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
      uses: QualiTorque/torque-validate-bp-action@v0.0.1
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

  start-sb:
    needs: validate
    runs-on: ubuntu-latest

    steps:
    - name: Start sandbox
      id: start-sandbox
      uses: QualiTorque/torque-start-sb-action@v0.0.1
      with:
        space: Demo
        blueprint_name: empty-bp-empty-app
        torque_token: ${{ secrets.TORQUE_TOKEN }}
        branch: master
        duration: 30
        timeout: 10
    - name: End sandbox on failure
      if: failure() && steps.start-sandbox.outputs.sandbox_id != ''
      uses: QualiTorque/torque-end-sb-action@v0.0.1
      with:
        space: Demo
        sandbox_id: ${{steps.start-sandbox.outputs.sandbox_id}}
        torque_token: ${{ secrets.TORQUE_TOKEN }}

    outputs:
      sandbox_id: ${{ steps.start-sandbox.outputs.sandbox_id }}

  finish-all:
    needs: [start-sb, some-parallel-job]
    runs-on: ubuntu-latest

    steps:
    - name: Stop sandbox
      uses: QualiTorque/torque-end-sb-action@v0.0.1
      with:
        space: Demo
        sandbox_id: ${{needs.start-sb.outputs.sandbox_id}}
        torque_token: ${{ secrets.TORQUE_TOKEN }}
```
