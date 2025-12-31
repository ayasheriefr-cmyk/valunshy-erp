from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import ItemTransfer, MaterialTransfer, RawMaterial

@receiver(post_save, sender=ItemTransfer)
def process_item_transfer_completion(sender, instance, created, **kwargs):
    """
    Update item locations when a transfer is completed.
    """
    if instance.status == 'completed':
        with transaction.atomic():
            for item in instance.items.all():
                item.current_branch = instance.to_branch
                item.save(update_fields=['current_branch'])

@receiver(post_save, sender=MaterialTransfer)
def process_material_transfer_completion(sender, instance, created, **kwargs):
    """
    Update raw material balances when a transfer is completed.
    """
    if instance.status == 'completed':
        with transaction.atomic():
            source_material = instance.material
            
            # 1. Deduct from source
            if source_material.current_weight < instance.weight:
                # This should ideally be caught by validation, but being safe here
                raise ValueError(f"الوزن المتاح في {source_material.name} أقل من الوزن المطلوب تحويله")
            
            source_material.current_weight -= instance.weight
            source_material.save(update_fields=['current_weight'])
            
            # 2. Add to destination
            # Check if destination already has this material type/carat
            dest_material = RawMaterial.objects.filter(
                branch=instance.to_branch,
                material_type=source_material.material_type,
                carat=source_material.carat,
                name=source_material.name # Matching by name as well
            ).first()
            
            if dest_material:
                dest_material.current_weight += instance.weight
                dest_material.save(update_fields=['current_weight'])
            else:
                RawMaterial.objects.create(
                    name=source_material.name,
                    material_type=source_material.material_type,
                    carat=source_material.carat,
                    current_weight=instance.weight,
                    branch=instance.to_branch
                )
