#!/usr/bin/env bash
# Create one Ubuntu 26.04 EC2 tagged server=ivolve, reachable over SSH and HTTP from your IP only.
set -euo pipefail

REGION=us-east-1
INSTANCE_TYPE=t3.micro
KEY_NAME=ivolve-lab28
KEY_FILE="$HOME/.ssh/${KEY_NAME}.pem"
SG_NAME=ivolve-lab28-sg
AMI_PARAM=/aws/service/canonical/ubuntu/server/26.04/stable/current/amd64/hvm/ebs-gp3/ami-id

MY_IP=$(curl -s https://checkip.amazonaws.com)
AMI=$(aws ssm get-parameter --region "$REGION" --name "$AMI_PARAM" --query Parameter.Value --output text)
VPC=$(aws ec2 describe-vpcs --region "$REGION" --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)

if [ ! -f "$KEY_FILE" ]; then
  aws ec2 create-key-pair --region "$REGION" --key-name "$KEY_NAME" --query KeyMaterial --output text > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
fi

SG=$(aws ec2 describe-security-groups --region "$REGION" \
  --filters Name=group-name,Values="$SG_NAME" Name=vpc-id,Values="$VPC" \
  --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = "None" ]; then
  SG=$(aws ec2 create-security-group --region "$REGION" --group-name "$SG_NAME" \
    --description "ivolve lab28 SSH and HTTP" --vpc-id "$VPC" --query GroupId --output text)
  aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG" --protocol tcp --port 22 --cidr "${MY_IP}/32"
  aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG" --protocol tcp --port 80 --cidr "${MY_IP}/32"
fi

INSTANCE=$(aws ec2 run-instances --region "$REGION" --image-id "$AMI" --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" --security-group-ids "$SG" --count 1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ivolve-lab28},{Key=server,Value=ivolve}]' \
  --query 'Instances[0].InstanceId' --output text)

echo "Waiting for $INSTANCE to run..."
aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE"
aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE" \
  --query 'Reservations[0].Instances[0].[InstanceId,PublicIpAddress,State.Name]' --output text
