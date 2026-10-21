
import json
import logging
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

SUNNY_INSTRUCTIONS = """
You are Sunny, the friendly solar assistant for SPAGTECH Solar
Installation in Chennai, India.

Be cheerful, helpful, concise, and explain technical terms simply.

Help visitors understand:
- On-grid, off-grid, and hybrid solar systems
- Solar panels, inverters, batteries, and maintenance
- Installation basics and electricity savings
- SPAGTECH website information and service areas

SPAGTECH contact details:
WhatsApp/Phone: +91 84336 46019
Email: spagtechs@gmail.com

Never invent company prices, offers, warranties, certifications,
stock, installation dates, or confirmed appointments.

Solar costs and savings depend on system size, usage, equipment,
the property, and applicable schemes. Direct quote requests to
SPAGTECH through WhatsApp or email.

Never claim you checked live company records or booked an
installation. If unsure, say so honestly.
"""


@csrf_exempt
def sunny_chat(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Please send a POST request."},
            status=405,
        )

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return JsonResponse(
            {"error": "Sunny's Gemini API key is not configured."},
            status=503,
        )

    try:
        body = json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Invalid JSON request."},
            status=400,
        )

    messages = body.get("messages")

    if not isinstance(messages, list) or not messages:
        return JsonResponse(
            {"error": "Please enter a message."},
            status=400,
        )

    if len(messages) > 12:
        return JsonResponse(
            {"error": "Please start a new conversation."},
            status=400,
        )

    history = []

    for message in messages:
        if not isinstance(message, dict):
            return JsonResponse(
                {"error": "Invalid message format."},
                status=400,
            )

        role = message.get("role")
        content = message.get("content")

        if role not in ("user", "assistant"):
            return JsonResponse(
                {"error": "Invalid message role."},
                status=400,
            )

        if not isinstance(content, str) or not content.strip():
            return JsonResponse(
                {"error": "Message cannot be empty."},
                status=400,
            )

        if len(content) > 2000:
            return JsonResponse(
                {"error": "Message is too long."},
                status=400,
            )

        history.append({
            "role": "user" if role == "user" else "model",
            "parts": [{"text": content.strip()}],
        })

    if history[-1]["role"] != "user":
        return JsonResponse(
            {"error": "The last message must be from the user."},
            status=400,
        )

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=os.environ.get(
                "GEMINI_MODEL",
                "gemini-2.5-flash-lite",
            ),
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SUNNY_INSTRUCTIONS,
                temperature=0.5,
                max_output_tokens=500,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            return JsonResponse(
                {"error": "Sunny couldn't generate an answer. Try again."},
                status=502,
            )

        return JsonResponse({"reply": answer})

    except Exception as exc:
     logger.exception("Gemini request failed: %s", exc)

    return JsonResponse(
        {
            "error": (
                "Gemini request failed. Check the Django "
                "terminal for the actual error."
            )
        },
        status=502,
    )
