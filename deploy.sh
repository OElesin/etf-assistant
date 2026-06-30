#!/bin/bash

# AmpliFolio Deployment Script
set -e

echo "🚀 Deploying AmpliFolio API..."

# Check if required environment variables are set
if [ -z "$SSL_CERTIFICATE_ARN" ]; then
    echo "❌ SSL_CERTIFICATE_ARN environment variable is required"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install -g serverless
npm install serverless-python-requirements serverless-offline

# Deploy API
echo "🔧 Deploying API to AWS..."
serverless deploy --stage prod

# Get API Gateway URL
API_URL=$(serverless info --stage prod | grep "ServiceEndpoint" | awk '{print $2}')
echo "✅ API deployed to: $API_URL"

# Deploy landing page to S3
echo "🌐 Deploying landing page to S3..."

# Create S3 bucket for website
aws s3 mb s3://amplifolio-website-prod --region eu-west-1

# Configure bucket for static website hosting
aws s3 website s3://amplifolio-website-prod \
    --index-document index.html \
    --error-document error.html

# Upload landing page
aws s3 sync landing-page/ s3://amplifolio-website-prod/ \
    --delete \
    --cache-control "max-age=86400"

# Set public read permissions
aws s3api put-bucket-policy \
    --bucket amplifolio-website-prod \
    --policy '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::amplifolio-website-prod/*"
            }
        ]
    }'

# Create CloudFront distribution for website
echo "☁️ Setting up CloudFront distribution..."

DISTRIBUTION_CONFIG='{
    "CallerReference": "'$(date +%s)'",
    "Comment": "AmpliFolio Website Distribution",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-amplifolio-website",
                "DomainName": "amplifolio-website-prod.s3-website-eu-west-1.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-amplifolio-website",
        "ViewerProtocolPolicy": "redirect-to-https",
        "MinTTL": 0,
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        }
    },
    "Enabled": true,
    "Aliases": {
        "Quantity": 1,
        "Items": ["amplifolio.eu"]
    },
    "ViewerCertificate": {
        "AcmCertificateArn": "'$SSL_CERTIFICATE_ARN'",
        "SslSupportMethod": "sni-only"
    }
}'

# Create distribution
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config "$DISTRIBUTION_CONFIG" \
    --query 'Distribution.Id' \
    --output text)

echo "✅ CloudFront distribution created: $DISTRIBUTION_ID"

# Output deployment information
echo ""
echo "🎉 Deployment Complete!"
echo "================================"
echo "API Endpoint: $API_URL"
echo "Website: https://amplifolio.eu"
echo "API Docs: https://api.amplifolio.eu/docs"
echo ""
echo "Next steps:"
echo "1. Update DNS records to point to CloudFront"
echo "2. Test API endpoints"
echo "3. Configure monitoring and alerts"
echo ""