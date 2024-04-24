from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Profile, User, FriendRequest, Inbox, Chat
from django.db import transaction


class UserRegisterSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    class Meta:
        model = User
        fields = ['email', 'password', 'id']
        extra_kwargs = {'password': {'write_only': True}}


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    id = serializers.CharField(read_only=True)
    password = serializers.CharField(max_length=225, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', None)
        password = attrs.get('password', None)

        if email is None:
            raise serializers.ValidationError("Email is required")
        
        if password is None:
            raise serializers.ValidationError("Password is required")
        
        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password")
        
        return {
            'email': user.email,
            'id': user.id
        }


class UserProfileSerializer(serializers.ModelSerializer):
    image = serializers.URLField()
    bio = serializers.CharField()
    username = serializers.CharField()
    class Meta:
        model = Profile
        fields = "__all__"

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = "__all__"


class AcceptFriendRequestSerializer(serializers.Serializer):
    id = serializers.CharField()
    sender = serializers.CharField()
    receiver = serializers.CharField()

    def save(self):
        with transaction.atomic():
            try:
                sender = User.objects.get(id=self.validated_data['sender'])
                receiver = User.objects.get(id=self.validated_data['receiver'])
                inbox = Inbox.objects.create()
                inbox.members.add(sender, receiver)
                friend_request = FriendRequest.objects.get(id=self.validated_data['id'])
                friend_request.delete()
                return True
            except Exception as e:
                print(e)
                transaction.set_rollback(True)
                return False
                raise serializers.ValidationError("Unable to create inbox")


    def validate(self, attrs):
        id = attrs.get("id", None)
        if id is None:
            raise serializers.ValidationError("Id is required")
        
        sender = attrs.get("sender", None)
        if sender is None:
            raise serializers.ValidationError("Sender is required")
        
        receiver = attrs.get("receiver", None)
        if receiver is None:
            raise serializers.ValidationError("Receiver is required")
        
        
        return {
            'id': id,
            'sender': sender,
            'receiver': receiver
        }


class chatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ['message', 'sender', 'inbox', 'id', 'seen']
        read_only_fields = ['id', 'seen']


class inboxSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField('get_username')
    class Meta:
        model = Inbox
        fields = ['id', 'last_message', 'user']
    
    def get_username(self, inbox):
        member = inbox.members.all()
        user_id = self.context.get("user_id")

        for user in member:
            if user.id != user_id:
                member = user
        return {"id": member.id, "username": member.profile.username, "profile": member.profile.image}