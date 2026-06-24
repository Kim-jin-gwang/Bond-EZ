from django.db import models
from django.conf import settings

class UserSearchLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="search_logs"
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    keyword = models.CharField(max_length=255, null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_search_log"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["session_key", "created_at"]),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else f"Guest({self.session_key})"
        return f"{user_str} searched '{self.keyword}' at {self.created_at}"
