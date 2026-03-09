import base64
import os
import time

import requests


def generate_video(
    prompt_file: str,
    reference_images: list[str],
    output_file: str,
    aspect_ratio: str = "16:9",
) -> str:
    with open(prompt_file, "r") as f:
        prompt = f.read()
    # Build request payload
    instance = {"prompt": prompt}
    if reference_images:
        ref_images_data = []
        for img_path in reference_images:
            with open(img_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")
            ref_images_data.append({
                "image": {"mimeType": "image/jpeg", "bytesBase64Encoded": image_b64},
                "referenceType": "asset",
            })
        instance["referenceImages"] = ref_images_data # type: ignore (handled by explicit dict structure)

    payload = {
        "instances": [instance],
        "parameters": {
             "aspectRatio": aspect_ratio,
        }
    }
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "GEMINI_API_KEY is not set"
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview:predictLongRunning",
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
    )
    res_json = response.json()
    if "error" in res_json:
        return f"Error from API: {res_json['error'].get('message', 'Unknown error')}"
        
    operation_name = res_json["name"]
    while True:
        response = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/{operation_name}",
            headers={
                "x-goog-api-key": api_key,
            },
        )
        op_json = response.json()
        if op_json.get("done", False):
            if "error" in op_json:
                return f"Operation failed: {op_json['error'].get('message', 'Unknown error')}"
                
            sample = op_json["response"]["generateVideoResponse"]["generatedSamples"][0]
            url = sample["video"]["uri"]
            download(url, output_file)
            break
        time.sleep(3)
    return f"The video has been generated successfully to {output_file}"


def download(url: str, output_file: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "GEMINI_API_KEY is not set"
    response = requests.get(
        url,
        headers={
            "x-goog-api-key": api_key,
        },
    )
    with open(output_file, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate videos using Gemini API")
    parser.add_argument(
        "--prompt-file",
        required=True,
        help="Absolute path to JSON prompt file",
    )
    parser.add_argument(
        "--reference-images",
        nargs="*",
        default=[],
        help="Absolute paths to reference images (space-separated)",
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Output path for generated image",
    )
    parser.add_argument(
        "--aspect-ratio",
        required=False,
        default="16:9",
        help="Aspect ratio of the generated image",
    )

    args = parser.parse_args()

    try:
        print(
            generate_video(
                args.prompt_file,
                args.reference_images,
                args.output_file,
                args.aspect_ratio,
            )
        )
    except Exception as e:
        print(f"Error while generating video: {e}")
