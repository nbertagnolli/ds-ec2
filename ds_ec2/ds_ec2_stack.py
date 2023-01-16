"""Stack to create a secure EC2 instance accessible through ssm."""

from aws_cdk import Stack, aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct
import os


def is_gpu(instance_type: str) -> bool:
    """Check to see if an instance type is gpu enabled."""
    return "p" in instance_type or "g5" in instance_type or "g4" in instance_type


class DsEc2Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Create a single EC2 instance with the libraries need to do data science work.

        This ec2 instance understands whether it has a gpu or not and installs the
        correct libraries.  If not instance_type is provided defaults to c4.2xlarge.
        """
        super().__init__(scope, construct_id, **kwargs)

        # Get the current region to deploy to
        region = os.getenv("CDK_DEFAULT_REGION")

        # Get the instance type from the environment. If none then defaults c4.2xlarge.
        if "INSTANCE_TYPE" in os.environ:
            instance_type = os.getenv("INSTANCE_TYPE")
        else:
            instance_type = "c4.2xlarge"

        # Create a VPC to control the network our instance lives on.
        vpc = ec2.Vpc(self, "ds-vpc", cidr="10.0.0.0/16")

        # Create a session manager role so we can connect without SSH.
        role = iam.Role(
            self,
            "ds-ec2-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            role_name="ds-ec2-role",
        )

        # Provide access to SSM for secure communication with the instance.
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore",
            )
        )

        # Create a security group that only allows inbound traffic.
        security_group = ec2.SecurityGroup(
            self,
            "ds-security-group",
            vpc=vpc,
            allow_all_outbound=True,
            security_group_name="ds-security-group",
        )

        # Create initializatoin commands for non GPU instances
        multipart_user_data = ec2.MultipartUserData()

        # Create a list of all requirements we want installed on our instance.
        with open("ds_ec2/requirements.txt", "r") as f:
            python_pkgs = [x.strip() for x in f.readlines()]

        # Check if the instance is a GPU if it isn't we want to install python
        # and install the cpu version of pytorch.  Otherwise we want to activate
        # the GPU enabled version of pytorch in the AMI.
        if not is_gpu(instance_type):
            python_other_pkgs = []
            env_activate_cmd = "python3.8 -m "
            install_python = ec2.UserData.for_linux()

            # Install python3.8 on the instance
            install_python.add_commands(
                "sudo yum update & sudo amazon-linux-extras install -y python3.8 "
            )

            # Activate python3.8 and install the CPU version of torch.
            install_python.add_commands(
                f"{env_activate_cmd} pip install torch --extra-index-url https://download.pytorch.org/whl/cpu"  # noqa: E501
            )

            # Add commands to the multipart user data and execute them to install python
            multipart_user_data.add_part(ec2.MultipartBody.from_user_data(install_python))

            # Increase the disk space on the device.
            root_volume = ec2.BlockDevice(
                device_name="/dev/xvda", volume=ec2.BlockDeviceVolume.ebs(25)
            )

            # Create a generic machine image for use with CPU.
            image = ec2.MachineImage.latest_amazon_linux(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            )

        else:
            python_other_pkgs = []

            # The deep learning AMI's have python installed we need to activate it.
            env_activate_cmd = "source activate pytorch; "

            # Increase the disk space on the device
            root_volume = ec2.BlockDevice(
                device_name="/dev/xvda", volume=ec2.BlockDeviceVolume.ebs(60)
            )

            # Create a Machine Image with the specified AMI.
            image = ec2.MachineImage.generic_linux({region: os.getenv("AWS_AMI")})

        # Install python dependencies.
        pkgs_to_install = " ".join(python_pkgs + python_other_pkgs)
        install_dependencies = ec2.UserData.for_linux()
        print(f"{env_activate_cmd} pip install {pkgs_to_install}")
        install_dependencies.add_commands(
            f"{env_activate_cmd} pip install {pkgs_to_install}"
        )
        multipart_user_data.add_part(
            ec2.MultipartBody.from_user_data(install_dependencies)
        )

        ec2.Instance(
            self,
            "ds-instance",
            role=role,
            instance_type=ec2.InstanceType(instance_type),
            machine_image=image,
            vpc=vpc,
            security_group=security_group,
            user_data=multipart_user_data,
            block_devices=[root_volume],
        )
