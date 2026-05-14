from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DirectMessageForm
from .models import DirectChat, DirectMessage, DirectMessageAttachment


@login_required
def inbox_view(request):
    User = get_user_model()
    q = (request.GET.get('q') or '').strip()

    people = User.objects.filter(is_active=True, registration_status='APPROVED').exclude(pk=request.user.pk)
    if q:
        people = people.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(department__icontains=q)
        )
    people = people.order_by('last_name', 'first_name', 'email')[:50]

    last_message_qs = DirectMessage.objects.filter(chat=OuterRef('pk')).order_by('-created_at')

    chats = (
        DirectChat.objects.filter(Q(user1=request.user) | Q(user2=request.user))
        .select_related('user1', 'user2')
        .annotate(
            last_message_text=Subquery(last_message_qs.values('text')[:1]),
            last_message_at=Subquery(last_message_qs.values('created_at')[:1]),
        )
        .order_by('-updated_at')
    )

    chat_rows = [
        {
            'chat': chat,
            'other': chat.other_user(request.user),
            'last_message_text': getattr(chat, 'last_message_text', None),
            'last_message_at': getattr(chat, 'last_message_at', None),
        }
        for chat in chats
    ]

    return render(
        request,
        'chat/inbox.html',
        {
            'chat_rows': chat_rows,
            'people': people,
            'q': q,
        },
    )


@login_required
def start_direct_chat_view(request, user_id: int):
    User = get_user_model()
    other = get_object_or_404(User, pk=user_id, is_active=True, registration_status='APPROVED')
    if other.pk == request.user.pk:
        return redirect('chat_inbox')
    chat = DirectChat.get_or_create_for_users(request.user, other)
    return redirect('chat_thread', chat_id=chat.pk)


@login_required
def direct_chat_thread_view(request, chat_id: int):
    chat = get_object_or_404(DirectChat.objects.select_related('user1', 'user2'), pk=chat_id)
    if not chat.is_participant(request.user):
        raise PermissionDenied

    other = chat.other_user(request.user)
    other_last_read = chat.last_read_message_id_for_user(other)

    if request.method == 'POST':
        form = DirectMessageForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                message = DirectMessage.objects.create(chat=chat, sender=request.user, text=form.cleaned_data['text'])
                for f in request.FILES.getlist('files'):
                    DirectMessageAttachment.objects.create(
                        message=message,
                        file=f,
                        original_name=getattr(f, 'name', '') or '',
                        content_type=getattr(f, 'content_type', '') or '',
                        size=int(getattr(f, 'size', 0) or 0),
                    )
                # Sender obviously has "read" up to their own newest message.
                chat.set_last_read_message_id_for_user(request.user, message.id)
                chat.save(update_fields=['user1_last_read_message_id', 'user2_last_read_message_id', 'updated_at'])
            return redirect('chat_thread', chat_id=chat.pk)
    else:
        form = DirectMessageForm()

    messages = chat.messages.select_related('sender').prefetch_related('attachments')
    latest_id = messages.order_by('-id').values_list('id', flat=True).first()

    # Mark as read when user opens the thread.
    current_last_read = chat.last_read_message_id_for_user(request.user)
    if latest_id and (current_last_read is None or latest_id > current_last_read):
        chat.set_last_read_message_id_for_user(request.user, latest_id)
        chat.save(update_fields=['user1_last_read_message_id', 'user2_last_read_message_id'])

    return render(
        request,
        'chat/thread.html',
        {
            'chat': chat,
            'other': other,
            'messages': messages,
            'form': form,
            'other_last_read_message_id': other_last_read,
        },
    )


@login_required
def delete_direct_message_view(request, chat_id: int, message_id: int):
    if request.method != 'POST':
        raise PermissionDenied

    chat = get_object_or_404(DirectChat.objects.select_related('user1', 'user2'), pk=chat_id)
    if not chat.is_participant(request.user):
        raise PermissionDenied

    message = get_object_or_404(DirectMessage, pk=message_id, chat=chat)
    if message.sender_id != request.user.id:
        raise PermissionDenied

    other = chat.other_user(request.user)
    other_last_read = chat.last_read_message_id_for_user(other)
    if other_last_read is not None and message.id <= other_last_read:
        raise PermissionDenied

    message.delete()
    return redirect('chat_thread', chat_id=chat.pk)
