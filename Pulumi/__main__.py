import pulumi
import pulumi_aws as aws
import pulumi_docker as docker

# 1. Obtener la VPC y subredes por defecto
vpc = aws.ec2.get_vpc(default=True)
subnets = aws.ec2.get_subnets(filters=[{
    "name": "vpc-id",
    "values": [vpc.id],
}])

# 2. Crear repositorio ECR para la imagen
repo = aws.ecr.Repository("fastapi-app-repo")

# 3. Login ECR
ecr_creds = aws.ecr.get_authorization_token()
registry_info = docker.ImageRegistry(
    server=repo.repository_url,
    username=ecr_creds.user_name,
    password=ecr_creds.password
)

# 4. Construir y subir imagen desde carpeta app/
image = docker.Image(
    "fastapi-app-image",
    build=docker.DockerBuild(context="../app"),
    image_name=f"{repo.repository_url}:v1.0.0",
    registry=registry_info
)

# 5. Crear cluster ECS
cluster = aws.ecs.Cluster("fastapi-cluster")

# 6. Rol para ECS task execution
role = aws.iam.Role("fastapi-task-exec-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }"""
)

aws.iam.RolePolicyAttachment("fastapi-task-exec-policy",
    role=role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)

# 7. Crear Security Group
sg = aws.ec2.SecurityGroup("fastapi-sg",
    vpc_id=vpc.id,
    description="Allow HTTP",
    ingress=[{
        "protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }]
)

# 8. Task definition
task_def = aws.ecs.TaskDefinition("fastapi-task-def",
    family="fastapi-task",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=role.arn,
    container_definitions=pulumi.Output.all(image.image_name).apply(
        lambda image_name: f"""
        [
            {{
                "name": "fastapi",
                "image": "{image_name}",
                "portMappings": [
                    {{
                        "containerPort": 80,
                        "hostPort": 80,
                        "protocol": "tcp"
                    }}
                ]
            }}
        ]
        """
    )
)

# 9. Crear servicio ECS con IP pública
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

# 10. Exportar la URL (necesitarás encontrarla manualmente en consola, o usar un ALB)
pulumi.export("image_url", image.image_name)
pulumi.export("repository_url", repo.repository_url)
