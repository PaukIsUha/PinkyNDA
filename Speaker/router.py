import json
import os
from dotenv import load_dotenv
from fastapi import APIRouter
from openai import AsyncOpenAI
from typing import Optional, Dict, Any

from prompts import topic_system_prompts, CLASSIFIER_PROMPT_TEMPLATE, CLASSIFIER_SYSTEM_PROMPT
from utils import form_messages, encode_image
from pydantic import BaseModel

load_dotenv()
API_KEY = os.getenv("API_KEY")

MODEL_NAME = 'gpt-4.1'  # "gpt-4.1-mini"
client = AsyncOpenAI(api_key=API_KEY)
router = APIRouter(
    prefix='/chat_ai'
)


class InferenceRequest(BaseModel):
    query: str
    topic: str
    base64_image: Optional[str] = None


class ValidationRequest(BaseModel):
    query: str
    chosen_topic: str
    base64_image: Optional[str] = None


@router.post("/pipeline")
async def pipeline_example(chosen_topic: str,
                           query: str,
                           image_path: str | None = None) -> Dict[str, str | None]:
    """
    Пример пайплайна. Выполняет:
    1. Кодирование изображения (если есть)
    2. Проверка валидности вопроса + определение его стоимости
    3. Принятие решения о дальнейших действиях (кнопка подтверждения в тг)
    4. Выполнение основного запроса к ИИ (при необходимости)
    
    Args:
        chosen_topic (str): Выбранная пользователем тема.
        query (str): Текстовый запрос пользователя.
        image_path (str | None): Путь к изображению (опционально).
    
    Returns:
        response_text: Ответ ИИ или None если запрос невалиден
    """
    # Кодирование изображения
    base64_image = encode_image(image_path) if image_path else None

    # Проверка валидности + стоимость
    validation_result = await check_validity_and_cost(query=query, base64_image=base64_image, chosen_topic=chosen_topic)
    is_valid = validation_result['is_valid']
    true_topic = validation_result['true_topic']
    cost = validation_result['cost']

    # Кнопка бота
    button_is_pressed = False
    if is_valid:
        print(f'Стоимость ответа: {cost}💖')
        # Кнопка для пользователя
        button_is_pressed = True
    else:
        if true_topic != 'Другое':
            print(f'Перенаправляю в блок: {true_topic}. Стоимость ответа: {cost}💖')
            # Кнопка для пользователя
            button_is_pressed = True
        else:
            print("К сожалению, я не знаю ответ на ваш вопрос😔")

    # Основной запрос к ИИ
    if button_is_pressed:
        inference_result = await general_inference(query=query, topic=true_topic, base64_image=base64_image)
        response_text = inference_result['response_text']
    else:
        response_text = None
    
    return {
        'response_text': response_text
    }


@router.post("/general_inference")
async def general_inference(payload: InferenceRequest) -> Dict[str, Any]:
    """
    Выполняет основной запрос к GPT.

    Тело запроса:
    {
        "query": "...",
        "topic": "...",
        "base64_image": "<опционально>"
    }
    """
    topic_system_prompt = topic_system_prompts[payload.topic]

    messages = form_messages(
        base64_image=payload.base64_image,
        system_prompt=topic_system_prompt,
        prompt=payload.query,
    )

    response = await client.responses.create(
        model=MODEL_NAME,
        tools=[{"type": "web_search_preview"}],
        input=messages,
    )

    return {"response_text": response.output_text}


# =========================== VALIDATION =====================================

@router.post("/validation")
async def check_validity_and_cost(payload: ValidationRequest) -> Dict[str, Any]:
    """
    Проверяет валидность запроса и рассчитывает «стоимость».

    Тело запроса:
    {
        "chosen_topic": "...",
        "query": "...",
        "base64_image": "<опционально>"
    }
    """
    messages = form_messages(
        base64_image=payload.base64_image,
        system_prompt=CLASSIFIER_SYSTEM_PROMPT,
        prompt=CLASSIFIER_PROMPT_TEMPLATE.format(
            query=payload.query,
            topic=payload.chosen_topic,
        ),
    )

    response = await client.responses.create(
        model=MODEL_NAME,
        input=messages,
    )

    topic_names = [
        "Разбор переписки",
        "Астрология",
        "Косметика и уход",
        "Здоровье и спорт",
        "Стиль",
        "Учёба",
    ]

    try:
        res_dict = json.loads(response.output_text)
        if res_dict["true_topic_idx"] != -1:
            res_dict["true_topic"] = topic_names[res_dict["true_topic_idx"] - 1]
        else:
            res_dict["true_topic"] = "Другое"
    except (json.JSONDecodeError, KeyError):
        res_dict = {
            "valid": False,
            "true_topic": "Другое",
            "cost": 2,
        }

    return {
        "is_valid": res_dict["valid"],
        "true_topic": res_dict["true_topic"],
        "cost": res_dict["cost"],
    }
