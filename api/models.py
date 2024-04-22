from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager




class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email not provided")
        email = self.normalize_email(email=email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self,email, password, **extra_fileds):
        user = self.create_user(email, password, **extra_fileds)
        user.is_staff= True
        user.is_superuser = True
        user.save(using=self.db)
        return user
    

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = None
    first_name = None
    last_name = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']
    objects = UserManager()



class Profile(models.Model):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    username = models.CharField(max_length=60, default="Unknown user")
    bio = models.CharField(max_length=100, null=True)
    image = models.URLField(default="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Default_pfp.svg/340px-Default_pfp.svg.png")

    def __str__(self):
        return self.user.email



class Inbox(models.Model):
    members = models.ManyToManyField(User, related_name="inbox")
    last_message = models.CharField(max_length=50, null=True)

    def __str__(self):
        return f"Inbox -> {str(self.id)}"

class Chat(models.Model):
    inbox = models.ForeignKey(Inbox, related_name="messages", on_delete=models.CASCADE)
    message = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="chat_send")
    seen = models.BooleanField(default=False)

    def __str__(self):
        return f"chat of {str(self.inbox.id)}"


class FriendRequest(models.Model):
    receiver = models.ForeignKey(User, related_name="friend_request", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="friend_request_send", on_delete=models.CASCADE)

    class Meta:
        unique_together = [('receiver', 'sender')]
    
    def __str__(self):
        return f"{self.receiver.profile.username} -> {self.sender.profile.username}"