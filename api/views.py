from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .serializer import LoginSerializer, UserRegisterSerializer, UserProfileSerializer, FriendRequestSerializer, AcceptFriendRequestSerializer, chatSerializer, inboxSerializer
from .custom_auth import CustomAuth
from django.db import transaction
from .models import User, FriendRequest, Inbox
from uuid import uuid4
from rest_framework.permissions import IsAuthenticated


@api_view(['POST'])
def loginView(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors)
    token = CustomAuth.generate_token(serializer.data)
    return Response({"token": token, "data": serializer.data})
    

@api_view(['POST'])
def userRegisterView(request):
    print(request.data)
    serializer = UserRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors)

    try:
        with transaction.atomic():
            user = serializer.save()
            profile_data = {**request.data, 'user': user.id}
            profile_serializer = UserProfileSerializer(data=profile_data)
            if not profile_serializer.is_valid():
                transaction.set_rollback(True)
                return Response(profile_serializer.errors, status=400)
            profile_serializer.save()
            token = CustomAuth.generate_token({"email": user.email, "id": user.id})
            return Response({
                "user": serializer.data,
                "profile": profile_serializer.data,
                "token": token
            })
    except Exception as e:
        print(e)
        return Response({"error": "server error"}, status=500)
    

@api_view(['GET'])
def searchUserView(request):
    params =  request.query_params
    user_id = params.get("id", None)
    if user_id is None:
        return Response({"error": "user id param not found!"})
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile.username
        return Response({"user":profile})
    except Exception as e:
        print(e)
        return Response({"error": "User not exist"})




class friendRequestView(APIView):

    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated]

    # To get friend request
    def get(self, request, *args, **kwargs):
        try:
            user_id = request.query_params.get('id', None)
            if not user_id:
                return Response({"error" : "user id param not found"})
            friendRequests = FriendRequest.objects.filter(receiver=user_id)
            serializer = FriendRequestSerializer(friendRequests, many=True)
            return Response({"requests": serializer.data})
        except Exception as e:
            print(e)
            return Response({"error": "Server error"}, status=500)

    # To send friend request
    def post(self, request, *args, **kwargs):
        try:
            params = request.query_params
            receiver_id = params.get("id", None)
            if receiver_id is None:
                return Response({"error": "user id param not found!"})
            sender_id = request.user.id
            if sender_id == int(receiver_id):
                return Response({"error": "sender and receiver cannot be same"}, status=400)
            serializer = FriendRequestSerializer(data={"sender": sender_id, "receiver": receiver_id})
            if not serializer.is_valid():
                return Response(serializer.errors, status=400)
            serializer.save()
            return Response({"request": serializer.data})
        
        except Exception as e:
            print(e)
            return Response({"error": "Server error"}, status=500)

    # To accept friend request
    def patch(self, request, *args, **kwargs):
        try:
            request_data = request.data
            data = {
                'id': request_data.get("id", None),
                'sender': request_data.get("sender", None),
                'receiver': request_data.get("receiver", None),
            }
            serializer = AcceptFriendRequestSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors)
            success = serializer.save()
            if not success:
                return Response({"error": "bad request"}, status=400)
            return Response({"message": "success"})

        except Exception as e:
            print(e)
            return Response({"error": "Server error"}, status=500)



class inboxView(APIView):
    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        inboxes = user.inbox.prefetch_related('members', 'members__profile')
        serializer = inboxSerializer(inboxes, many=True, context={"user_id": user.id})
        return Response(serializer.data)



class chatView(APIView):

    def get(self, request, *args, **kwargs):
        inbox_id = request.query_params.get("inbox_id", None)
        if inbox_id is None:
            return Response({"error": "inbox_id query param required"}, status=400)
        try:
            inbox = Inbox.objects.get(id=inbox_id)
            messages = inbox.messages
            serializer = chatSerializer(messages, many=True)
            return Response({"chat": serializer.data})

        except Exception as e:
            print(e)
            return Response({"error": "Inbox not found"}, status=400)
    
