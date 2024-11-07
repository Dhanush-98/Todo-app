from django.db import models
from accounts.models import User

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-id"]


class Todo(BaseModel):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title
