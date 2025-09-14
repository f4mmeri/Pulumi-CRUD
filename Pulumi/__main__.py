import pulumi
import pulumi_aws as aws

# 1) VPC y subnets por defecto
vpc = aws.ec2.get_vpc(default=True)
subnets = aws.ec2.get_subnets(filters=[{"name": "vpc-id", "values": [vpc.id]}])

# 2) Cluster ECS
cluster = aws.ecs.Cluster("fastapi-cluster")

# 3) Security Group (HTTP 80 abierto)
sg = aws.ec2.SecurityGroup("fastapi-sg",
    vpc_id=vpc.id,
    description="Allow HTTP",
    ingress=[{"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]}],
    egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}]
)

# 4) Imagen pública en Docker Hub
image_name = "f4mmeri/pulumi-crud:latest"  # ajusta si cambias el tag

# 5) Task Definition (Fargate) SIN executionRoleArn
task_def = aws.ecs.TaskDefinition("fastapi-task-def",
    family="fastapi-task",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    # execution_role_arn OMITIDO a propósito
    container_definitions=pulumi.Output.from_input(f"""
    [
      {{
        "name": "pulumi-crud",
        "image": "{image_name}",
        "portMappings": [
          {{ "containerPort": 80, "hostPort": 80, "protocol": "tcp" }}
        ]
      }}
    ]
    """)
)

# 6) Service con IP pública
service = aws.ecs.Service("fastapi-service",
    cluster=cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=task_def.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=True,
        subnets=subnets.ids,
        security_groups=[sg.id],
    ),
    opts=pulumi.ResourceOptions(depends_on=[task_def])
)

# 7) Exports útiles
pulumi.export("docker_image", image_name)
pulumi.export("ecs_cluster_name", cluster.name)
pulumi.export("ecs_service_name", service.name)
