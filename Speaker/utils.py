import base64


def form_messages(prompt: str, system_prompt: str | None = None, base64_image: str | None = None) -> list[dict]:
    messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": system_prompt}]
        },
    ]

    messages.append({
        "role": "user",
        "content": [],
    })

    messages[-1]['content'].append({
        "type": "input_text", 
        "text": prompt
    })

    if base64_image:
        messages[-1]['content'].append(
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_image}"}
        )

    return messages


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
