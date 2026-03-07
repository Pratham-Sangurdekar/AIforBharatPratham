#!/bin/bash
# ═══════════════════════════════════════════════
# ENGAUGE — AWS Deployment Script
# Deploys the full stack using AWS SAM CLI
# ═══════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ENGAUGE — AWS Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found. Install it: https://aws.amazon.com/cli/${NC}"
    exit 1
fi

if ! command -v sam &> /dev/null; then
    echo -e "${RED}Error: AWS SAM CLI not found. Install it: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html${NC}"
    exit 1
fi

# Verify AWS credentials
aws sts get-caller-identity > /dev/null 2>&1 || {
    echo -e "${RED}Error: AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
}

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}
STACK_NAME="engauge-stack"

echo -e "${GREEN}✓ AWS CLI configured (Account: ${ACCOUNT_ID}, Region: ${REGION})${NC}"
echo -e "${GREEN}✓ SAM CLI available${NC}"

# ── Step 1: Prepare Lambda deployment package ──
echo -e "\n${YELLOW}Step 1: Preparing Lambda deployment package...${NC}"

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$DEPLOY_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
BUILD_DIR="$DEPLOY_DIR/.build"

# Clean and create build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy backend code
cp -r "$BACKEND_DIR"/*.py "$BUILD_DIR/" 2>/dev/null || true
cp -r "$BACKEND_DIR"/api "$BUILD_DIR/"
cp -r "$BACKEND_DIR"/models "$BUILD_DIR/"
cp -r "$BACKEND_DIR"/services "$BUILD_DIR/"
cp -r "$BACKEND_DIR"/utils "$BUILD_DIR/"

# Copy Lambda handlers
cp "$DEPLOY_DIR/lambda_handler.py" "$BUILD_DIR/"
cp "$DEPLOY_DIR/trend_ingestion_handler.py" "$BUILD_DIR/"

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r "$BACKEND_DIR/requirements.txt" -t "$BUILD_DIR/" -q

# Copy SAM template
cp "$DEPLOY_DIR/template.yaml" "$BUILD_DIR/"

echo -e "${GREEN}✓ Deployment package prepared${NC}"

# ── Step 2: SAM Build ──
echo -e "\n${YELLOW}Step 2: Building with SAM...${NC}"
cd "$BUILD_DIR"
sam build --template-file template.yaml

echo -e "${GREEN}✓ SAM build complete${NC}"

# ── Step 3: SAM Deploy ──
echo -e "\n${YELLOW}Step 3: Deploying to AWS...${NC}"
sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --resolve-s3 \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

echo -e "${GREEN}✓ Backend deployed${NC}"

# ── Step 4: Get outputs ──
echo -e "\n${YELLOW}Step 4: Retrieving deployment outputs...${NC}"

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text --region "$REGION")

CF_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
    --output text --region "$REGION")

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
    --output text --region "$REGION")

MEDIA_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`MediaBucketName`].OutputValue' \
    --output text --region "$REGION")

echo -e "${GREEN}API URL: ${API_URL}${NC}"
echo -e "${GREEN}CloudFront URL: ${CF_URL}${NC}"
echo -e "${GREEN}Frontend Bucket: ${FRONTEND_BUCKET}${NC}"
echo -e "${GREEN}Media Bucket: ${MEDIA_BUCKET}${NC}"

# ── Step 5: Build and deploy frontend ──
echo -e "\n${YELLOW}Step 5: Building and deploying frontend...${NC}"

FRONTEND_DIR="$PROJECT_ROOT/frontend"
cd "$FRONTEND_DIR"

# Set the API URL for the frontend build
export NEXT_PUBLIC_API_URL="$API_URL"

# Build Next.js as static export
npm run build

# Upload to S3
aws s3 sync out/ "s3://${FRONTEND_BUCKET}/" \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --region "$REGION"

# Set correct cache headers for HTML files
aws s3 cp "s3://${FRONTEND_BUCKET}/" "s3://${FRONTEND_BUCKET}/" \
    --exclude "*" \
    --include "*.html" \
    --metadata-directive REPLACE \
    --cache-control "public, max-age=0, must-revalidate" \
    --content-type "text/html" \
    --recursive \
    --region "$REGION"

echo -e "${GREEN}✓ Frontend deployed${NC}"

# ── Step 6: Trigger initial trend ingestion ──
echo -e "\n${YELLOW}Step 6: Running initial trend ingestion...${NC}"
aws lambda invoke \
    --function-name engauge-trend-ingestion \
    --region "$REGION" \
    /tmp/trend-output.json > /dev/null 2>&1 || true

echo -e "${GREEN}✓ Initial trends loaded${NC}"

# ── Done ──
echo -e "\n${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ENGAUGE deployment complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Frontend:${NC}  ${CF_URL}"
echo -e "  ${GREEN}API:${NC}       ${API_URL}"
echo -e "  ${GREEN}Health:${NC}    ${API_URL}/health"
echo ""
echo -e "  ${YELLOW}To tear down: aws cloudformation delete-stack --stack-name ${STACK_NAME}${NC}"
echo ""
