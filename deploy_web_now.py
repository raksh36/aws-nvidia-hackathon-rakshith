#!/usr/bin/env python3
"""
Deploy web interface to S3 - Ready for organizers
"""
import boto3
import json
import os

# Note: Set AWS credentials from Vocareum before running
# AWS credentials should be in environment variables

s3 = boto3.client('s3', region_name='us-east-1')

BUCKET_NAME = 'logguardian-demo-rakshith'

print("\n" + "="*60)
print("DEPLOYING WEB INTERFACE TO S3")
print("="*60)

# 1. Create bucket
try:
    s3.create_bucket(Bucket=BUCKET_NAME)
    print(f"\n[OK] Created bucket: {BUCKET_NAME}")
except Exception as e:
    if 'BucketAlreadyOwnedByYou' in str(e):
        print(f"\n[EXISTS] Bucket already exists: {BUCKET_NAME}")
    else:
        print(f"\n[INFO] Bucket creation: {e}")

# 2. Enable static website hosting
try:
    s3.put_bucket_website(
        Bucket=BUCKET_NAME,
        WebsiteConfiguration={
            'IndexDocument': {'Suffix': 'index.html'},
            'ErrorDocument': {'Key': 'index.html'}
        }
    )
    print("[OK] Enabled static website hosting")
except Exception as e:
    print(f"[INFO] Website config: {e}")

# 3. Make bucket public
try:
    # Disable block public access first
    s3.delete_public_access_block(Bucket=BUCKET_NAME)
    
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
except Exception as e:
    print(f"[INFO] Public access: {e}")

# 4. Upload index.html
try:
    s3.upload_file(
        'web/index.html',
        BUCKET_NAME,
        'index.html',
        ExtraArgs={
            'ContentType': 'text/html',
            'CacheControl': 'no-cache'
        }
    )
    print("[OK] Uploaded index.html")
except Exception as e:
    print(f"[ERROR] Upload failed: {e}")
    print("\nMake sure web/index.html exists!")

# 5. Get website URL
url = f"http://{BUCKET_NAME}.s3-website-us-east-1.amazonaws.com"

print("\n" + "="*60)
print("✅ WEB INTERFACE DEPLOYED!")
print("="*60)
print(f"\n🌐 PUBLIC URL:")
print(f"   {url}")
print("\n📋 Use this URL in your:")
print("   - Demo video")
print("   - DevPost submission")
print("   - Share with organizers")
print("\n⚠️  Note: This URL works publicly - anyone can access it!")
print("="*60 + "\n")

