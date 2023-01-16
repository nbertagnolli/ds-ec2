
# Setup
The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

Add the following proxy configuration to .ssh/config

```
# SSH over Session Manager
host i-* mi-*
    ProxyCommand sh -c "aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"
```

# Usage

1. Activate your virtual environment.

`source .venv/bin/activate`

2. Deploy your stack

`cdk deploy`

3. Once your stack is deployed conect to the remote host:

`aws ssm start-session --target $INSTANCE_ID --region=$AWS_REGION`

4. On the remote host start a screen for your notebook 

`screen -S jupyter`

5. Move to a directory with read and write access

`cd /home/ssm-user`

6. Run jupyter lab, We set port to 8123. This can be whatever you want but make sure that it is correctly forwarded in the other steps.

`jupyter-lab --no-browser --allow-root --ip=0.0.0.0 --port=8123`

7. Copy down the login and token from the jupyter instance. It should look something like:

`http://127.0.0.1:8123/lab?token=tokenstuff!!!!`

8. Log out of the remote session

9. Open an SSM session with the remote instance forwarding the correct port.

`aws ssm start-session --target <instance_id> --region <out_region> --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8123"],"localPortNumber":["8123"]}'`

10. Paste the URL from (6) into the browser and enjoy developing on your remote instance.
 * `cdk docs`        open CDK documentation

Enjoy!


## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state# Usage


