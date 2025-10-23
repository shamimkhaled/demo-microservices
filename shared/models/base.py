
import uuid
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at timestamps
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Abstract base model with UUID primary key
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base model for soft deletion
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete the object"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def restore(self):
        """Restore soft deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class AuditModel(models.Model):
    """
    Abstract base model for audit trail
    """
    created_by_id = models.UUIDField(blank=True, null=True)
    updated_by_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """
    Combination of UUID and timestamp models
    Most commonly used base model
    """
    
    class Meta:
        abstract = True