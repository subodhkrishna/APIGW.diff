# AWS Terraform Configuration

Terraform configuration for deploying API gateways to AWS for testing.

## Prerequisites

- AWS account
- Terraform installed
- AWS credentials configured

## Structure

```
aws/
├── main.tf           # Main Terraform configuration
├── variables.tf      # Input variables
├── outputs.tf        # Output values
└── README.md         # This file
```

## Quick Start

```bash
# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy
terraform apply

# Get outputs
terraform output

# Cleanup
terraform destroy
```

## Configuration

Create `terraform.tfvars`:

```hcl
region = "us-east-1"
environment = "testing"
api_gateway_name = "gateway-comparison-test"
```

## Outputs

After deployment, Terraform will output:

- API Gateway URL
- API Gateway ID
- API Key

Use these values in `config/gateways.yaml`:

```yaml
gateways:
  aws_api_gateway:
    enabled: true
    url: "<terraform_output_url>"
    api_id: "<terraform_output_id>"
    credentials:
      api_key: "<terraform_output_key>"
```

## Cost Considerations

- API Gateway: Pay per request + data transfer
- Lambda: Pay per invocation (if using Lambda backend)
- CloudWatch: Logs storage

Estimated cost for testing: $5-20/month depending on usage.

## Cleanup

Always run `terraform destroy` when done testing to avoid charges.
