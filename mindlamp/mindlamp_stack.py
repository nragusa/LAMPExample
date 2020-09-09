from aws_cdk import core
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_route53 as route53


class MindlampStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        """
        Creates a VPC with 2 public and 2 private subnets,
        each subnet with a /18 CIDR range,
        a 2 NAT gateways
        """
        vpc = ec2.Vpc(
            self, "MindLAMPVPC",
            cidr="10.10.0.0/16"
        )

        # Security group for instances
        security_group = ec2.SecurityGroup(
            self, "MindLAMPSecurityGroup",
            vpc=vpc,
            description="Security group for LAMP Platform instances"
        )

        # Allow TCP to port 80 from 0.0.0.0/0
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP connections to port 80"
        )
        # Allow TCP to port 443 from 0.0.0.0/0
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTP connections to port 443"
        )

        # Allow TCP to port 443 from 0.0.0.0/0
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv6(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTP connections to port 443 with ipv6"
        )

        # Install docker on boot
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "yum -y install docker && usermod -a -G docker ec2-user")

        # The EC2 instance
        instance1 = ec2.Instance(
            self, "MindLAMPInstance1",
            instance_type=ec2.InstanceType("t3a.large"),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            user_data=user_data,
            instance_name="LAMP platform",
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sdf",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=30,
                        encrypted=True,
                        delete_on_termination=True
                    )
                ),
                ec2.BlockDevice(
                    device_name="/dev/sdg",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=100,
                        encrypted=True,
                        delete_on_termination=False
                    )
                )
            ],
            security_group=security_group,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

        # Associate the SSM managed policy for SSM control + access
        instance1.role.add_managed_policy(
            policy=iam.ManagedPolicy.from_aws_managed_policy_name(
                managed_policy_name="AmazonSSMManagedInstanceCore")
        )

        # Get an existing Route53 hosted zone
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "MindLAMPHostedZone",
            hosted_zone_id=self.node.try_get_context("hosted_zone_id"),
            zone_name=self.node.try_get_context("zone_name")
        )

        # Create an A record to point to the public IP of instance1
        record_set1 = route53.RecordSet(
            self, "Node1RecordSet",
            record_type=route53.RecordType.A,
            target=route53.RecordTarget(values=[instance1.instance_public_ip]),
            zone=hosted_zone,
            record_name="node1"
        )
