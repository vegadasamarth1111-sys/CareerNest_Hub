from django.shortcuts import render
from django.http import JsonResponse
from .models import ChatMessage
from .ai import get_ai_response


def chat_page(request):
    return render(request, "chat/chat.html")


def chat_api(request):
    if request.method == "POST":
        user_message = request.POST.get("message")

        ai_reply = get_ai_response(user_message)

        # Save chat if user is logged in
        if request.user.is_authenticated:
            ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response=ai_reply
            )

        return JsonResponse({
            "message": user_message,
            "response": ai_reply
        })