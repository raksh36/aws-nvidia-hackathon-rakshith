#!/usr/bin/env python3
"""
Deploy web interface to S3 static website
"""
import boto3
import json

s3 = boto3.client('s3', region_name='us-east-1')

BUCKET_NAME = 'logguardian-ai-demo'

print("Deploying web interface to S3...")

# 1. Create bucket
try:
    s3.create_bucket(Bucket=BUCKET_NAME)
    print(f"[OK] Created bucket: {BUCKET_NAME}")
except s3.exceptions.BucketAlreadyOwnedByYou:
    print(f"[EXISTS] Bucket already exists: {BUCKET_NAME}")
except Exception as e:
    print(f"[ERROR] {e}")

# 2. Enable static website hosting
s3.put_bucket_website(
    Bucket=BUCKET_NAME,
    WebsiteConfiguration={
        'IndexDocument': {'Suffix': 'index.html'},
        'ErrorDocument': {'Key': 'index.html'}
    }
)
print("[OK] Enabled static website hosting")

# 3. Make bucket public
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "PublicReadGetObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:GetObject",
        "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
    }]
}

s3.put_bucket_policy(
    Bucket=BUCKET_NAME,
    Policy=json.dumps(bucket_policy)
)
print("[OK] Set public read policy")

# 4. Upload index.html
s3.upload_file(
    'web/index.html',
    BUCKET_NAME,
    'index.html',
    ExtraArgs={'ContentType': 'text/html'}
)
print("[OK] Uploaded index.html")

# 5. Get website URL
url = f"http://{BUCKET_NAME}.s3-website-us-east-1.amazonaws.com"
print("\n" + "="*60)
print("WEB INTERFACE DEPLOYED!")
print("="*60)
print(f"\nURL: {url}")
print("\nUse this URL in your demo video!")
print("="*60)

