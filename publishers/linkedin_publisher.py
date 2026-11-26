import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()   # antes funcionaba solo porque gemini_adp lo llamaba primero
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PERSON_URN   = os.getenv("URN_PERSON")
def register_upload():
    url = "https://api.linkedin.com/v2/assets?action=registerUpload"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202501"
    }

    body = {
        "registerUploadRequest": {
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "owner": PERSON_URN,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }

    r = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=TIMEOUT
    )

    return r.json()

def publish_linkedin(text: str, media_paths=None):
    media_assets = []
    for path in media_paths:
        asset = upload_image(path)
        media_assets.append({
            "status": "READY",
            "media": asset
        })
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    body = {
        "author": PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": (
                    "IMAGE"
                    if media_assets
                    else "NONE"
                ),
                "media": media_assets
            }
            
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    try:
        r = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=TIMEOUT
        )

        print(f"STATUS: {r.status_code}")
        print("RAW RESPONSE:")
        print(r.text)

        return r.status_code, r.json()

    except Exception as e:
        print("❌ Publish error:", e)
        return None, str(e)

def upload_image(image_path):

    upload_data = register_upload()

    upload_url = (
        upload_data["value"]
        ["uploadMechanism"]
        ["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]
        ["uploadUrl"]
    )

    asset = upload_data["value"]["asset"]

    with open(image_path, "rb") as f:
        image_binary = f.read()

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    r = requests.put(
        upload_url,
        data=image_binary,
        headers=headers,
        timeout=TIMEOUT
    )

    print("UPLOAD:", r.status_code)

    return asset

def get_first_png(folder_path):
    png_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".png")
    ])

    if not png_files:
        return None

    return os.path.join(folder_path, png_files[0])
