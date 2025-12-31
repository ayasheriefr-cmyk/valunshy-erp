from decimal import Decimal
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Sum
from .models import ManufacturingOrder, Workshop, WorkshopTransfer, OrderStone, WorkshopSettlement
from inventory.models import Item, Carat

@receiver(pre_save, sender=ManufacturingOrder)
def calculate_workshop_loss(sender, instance, **kwargs):
    """
    Automated Loss Calculation Logic
    ------------------------------
    Automatically calculates scrap weight when output weight is provided.
    """
    if instance.input_weight and instance.output_weight:
        # If output is set, calculate the loss automatically: Input - Output - Powder
        powder = instance.powder_weight or 0
        stones_g = instance.total_stone_weight or 0
        # Scrap = Input - (Net Gold + Powder)
        # Net Gold = Output Weight - Stones Weight
        calculated_scrap = instance.input_weight - (instance.output_weight - stones_g + powder)
        
        # Only update if it makes sense (positive loss)
        if calculated_scrap >= 0:
            instance.scrap_weight = calculated_scrap
            
            # Simple alerting logic (can be expanded to notifications)
            loss_percentage = (calculated_scrap / instance.input_weight) * 100
            if loss_percentage > 1.0: # 1.0% Tolerance
                print(f"WARNING: High Loss Percentage detected on Order {instance.order_number}: {loss_percentage:.2f}%")

@receiver(post_save, sender=ManufacturingOrder)
def issue_order_materials(sender, instance, created, **kwargs):
    """
    Automated Material Issuance Logic
    --------------------------------
    When an order moves from 'draft' to an active state, we:
    1. Add the input gold weight to the workshop's balance.
    2. Deduct the gold weight from the input raw material stock.
    """
    is_active = instance.status != 'draft'
    was_draft = getattr(instance, '_original_status', None) == 'draft' or created
    
    # Only process if it's becoming active for the first time
    if is_active and was_draft and instance.input_weight > 0 and instance.workshop:
        with transaction.atomic():
            # 1. Add gold to Workshop balance
            carat_name = instance.carat.name
            if '18' in carat_name:
                instance.workshop.gold_balance_18 += instance.input_weight
            elif '21' in carat_name:
                instance.workshop.gold_balance_21 += instance.input_weight
            elif '24' in carat_name:
                instance.workshop.gold_balance_24 += instance.input_weight
            
            instance.workshop.save()
            
            # 2. Deduct from RawMaterial if provided
            if instance.input_material:
                instance.input_material.current_weight -= instance.input_weight
                instance.input_material.save()
            
            # Prevent re-triggering if same instance is saved again
            instance._original_status = instance.status

@receiver(post_save, sender=ManufacturingOrder)
def complete_manufacturing_order(sender, instance, created, **kwargs):
    """
    Closing Logic for Workshops
    ---------------------------
    1. Deduct Gold from Workshop Balance.
    2. Add Labor cost to Workshop Balance (Labor Credit).
    3. Auto-Create Finished Item in Inventory.
    """
    # Only execute when status changes from something else to 'completed'
    is_completed = instance.status == 'completed'
    was_completed = getattr(instance, '_original_status', None) == 'completed'

    if is_completed and not was_completed and instance.output_weight > 0:
        
        # 1. Update Workshop Balances
        if instance.workshop:
            # Credit the Workshop Labor Balance ONLY for external workshops
            if instance.workshop.workshop_type == 'external' and instance.manufacturing_pay > 0:
                instance.workshop.labor_balance += instance.manufacturing_pay
            
            # Update Filings (Powder) Balance
            if instance.powder_weight > 0:
                carat_name = instance.carat.name
                if '18' in carat_name:
                    instance.workshop.filings_balance_18 += instance.powder_weight
                elif '21' in carat_name:
                    instance.workshop.filings_balance_21 += instance.powder_weight
                elif '24' in carat_name:
                    instance.workshop.filings_balance_24 += instance.powder_weight
            
            # --- NEW: Deduct used gold (Net Gold + Powder) from Workshop Balance ---
            # NOTE: We do NOT deduct 'scrap_weight' automatically here.
            # Rationale: Scrap/Loss is a liability on the workshop until they either return it as powder
            # or it is written off via a specific settlement.
            # User Scenario: "I receive powder at end of day". So we leave the difference in their balance.
            
            # Net Gold = output_weight - total_stone_weight
            total_gold_consumed = (instance.output_weight - instance.total_stone_weight) + (instance.powder_weight or 0)

            # Special Logic for Laser Workshop (Weight Gain from Welding)
            # If output > input, the extra weight is welding wire/solder consumed from treasury
            is_laser = 'ليزر' in instance.workshop.name or 'Laser' in instance.workshop.name
            if is_laser and instance.output_weight > instance.input_weight:
                welding_gain = instance.output_weight - instance.input_weight
                # For Laser, consumption from workshop perspective is just input, 
                # but technically they returned more. 
                # Let's keep simpler logic: Deduct what they returned.
                # If they returned 102 (Input 100), balance becomes -2 (We owe them / they have credit).
                # This is correct for Laser if they added their own material, 
                # but if they used OUR wire (which is separate tool), we should account for that.
                # (Existing logic handled treasury deduction, we keep that)
                
                # Logic: Deduct the gain from the linked Treasury's stock
                total_gold_consumed = instance.input_weight + (instance.powder_weight or 0) # Cap deduction at Input + Powder? 
                # No, let's stick to standard: Deduct Output. If Output > Balance (due to added solder), 
                # their balance improves (goes negative/credit).
                total_gold_consumed = (instance.output_weight - instance.total_stone_weight) + (instance.powder_weight or 0)
                
                # Logic: Deduct the gain from the linked Treasury's stock
                linked_treasury = instance.workshop.treasuries.first()
                if linked_treasury:
                    from finance.treasury_models import TreasuryTool, TreasuryTransaction
                    # Find a gold tool (wire/solder) in this treasury of the same carat
                    tool_stock = TreasuryTool.objects.filter(
                        treasury=linked_treasury, 
                        tool__carat=instance.carat,
                        tool__tool_type__in=['gold_wire', 'gold_solder']
                    ).first()
                    
                    if tool_stock:
                        tool_stock.weight -= welding_gain
                        tool_stock.save()
                        tool_stock.tool.weight -= welding_gain
                        tool_stock.tool.save()
                        
                        # Determine created_by
                        created_by = getattr(linked_treasury, 'responsible_user', None) or \
                                     getattr(instance.workshop, 'responsible_user', None)
                        
                        if not created_by:
                            from django.contrib.auth.models import User
                            created_by = User.objects.filter(is_superuser=True).first()

                        # Record a treasury transaction for the consumption
                        TreasuryTransaction.objects.create(
                            treasury=linked_treasury,
                            transaction_type='gold_out',
                            gold_weight=welding_gain,
                            gold_carat=instance.carat,
                            description=f"استهلاك تلقائي للحام (زيادة وزن): {instance.order_number}",
                            reference_type='manufacturing_order',
                            reference_id=instance.id,
                            created_by=created_by
                        )

            carat_name = instance.carat.name
            if '18' in carat_name:
                instance.workshop.gold_balance_18 -= total_gold_consumed
            elif '21' in carat_name:
                instance.workshop.gold_balance_21 -= total_gold_consumed
            elif '24' in carat_name:
                instance.workshop.gold_balance_24 -= total_gold_consumed

            instance.workshop.save()
            
            # Prevent re-triggering completion logic if same instance is saved again
            instance._original_status = instance.status




        # 2. Auto-Create Item in Inventory (If needed and doesn't exist)
        if instance.auto_create_item and not instance.resulting_item:
            try:
                import random
                from finance.models import FinanceSettings
                from finance.treasury_models import TreasuryTransaction

                # Generate a unique barcode if not strictly defined
                barcode = f"MFG-{instance.order_number}-{random.randint(1000, 9999)}"
                
                # Calculate Total Labor Cost (Technician Pay + Factory Profit Margin)
                total_labor_cost = (instance.manufacturing_pay or 0) + (instance.factory_margin or 0)

                new_item = Item.objects.create(
                    name=instance.item_name_pattern or f"منتج مصنع - {instance.order_number}",
                    barcode=barcode,
                    carat=instance.carat,
                    gross_weight=instance.output_weight,
                    net_gold_weight=instance.output_weight - instance.total_stone_weight,
                    stone_weight=instance.total_stone_weight / Decimal('0.2'),
                    # Financials: Factory Price (Cost + Factory Margin)
                    fixed_labor_fee=total_labor_cost, 
                    labor_fee_per_gram=0,
                    # Status
                    status='available',
                    current_branch=instance.target_branch
                )
                
                # Link it back
                instance.resulting_item = new_item
                instance.save(update_fields=['resulting_item'])

                # 3. Record in Sales Treasury (Value Transfer)
                settings = FinanceSettings.objects.first()
                if settings and settings.sales_treasury:
                    TreasuryTransaction.objects.create(
                        treasury=settings.sales_treasury,
                        transaction_type='finished_goods_in',
                        cash_amount=total_labor_cost, # Recording the labor value component
                        gold_weight=instance.output_weight,
                        gold_carat=instance.carat,
                        description=f"استلام إنتاج تام: {instance.order_number} - {new_item.name}",
                        reference_type='manufacturing_order',
                        reference_id=instance.id,
                        created_by=instance.target_branch.manager if (instance.target_branch and instance.target_branch.manager) else instance.workshop.responsible_user if instance.workshop else None
                    )
                
                # 4. Deduct Materials Stock (Stones and Tools)
                # Stones
                for os in instance.orderstone_set.all():
                    if os.stone:
                        os.stone.current_stock -= os.quantity
                        os.stone.save()
                
                # Tools
                for ot in instance.order_tools_list.all():
                    if ot.tool:
                        if ot.tool.unit == 'gram':
                            ot.tool.weight -= ot.weight
                        else:
                            ot.tool.quantity -= int(ot.quantity)
                        ot.tool.save()
                
            except Exception as e:
                print(f"Error creating auto-inventory item / treasury sync: {e}")


@receiver(post_save, sender=WorkshopTransfer)
def process_workshop_transfer(sender, instance, created, **kwargs):
    """
    Automated balance adjustment when a workshop transfer is completed.
    """
    # Only process if status changed from something else to 'completed'
    is_completed = instance.status == 'completed'
    was_completed = getattr(instance, '_original_status', None) == 'completed'
    
    if is_completed and not was_completed:
        with transaction.atomic():
            source = instance.from_workshop
            dest = instance.to_workshop
            weight = instance.weight
            carat_name = instance.carat.name
            
            # Determine which field to update based on carat
            field_map = {
                '18': 'gold_balance_18',
                '21': 'gold_balance_21',
                '24': 'gold_balance_24',
            }
            
            field_to_update = None
            for key, field in field_map.items():
                if key in carat_name:
                    field_to_update = field
                    break
            
            if not field_to_update:
                raise ValueError(f"العيار {carat_name} غير مدعوم في تحويلات الورش")
            
            # Deduct from source
            current_source_bal = getattr(source, field_to_update)
            if current_source_bal < weight:
                raise ValueError(f"الرصيد المتاح في {source.name} ({current_source_bal} جم) أقل من الوزن المطلوب تحويله")
            
            setattr(source, field_to_update, current_source_bal - weight)
            source.save(update_fields=[field_to_update])
            
            # Add to destination
            current_dest_bal = getattr(dest, field_to_update)
            setattr(dest, field_to_update, current_dest_bal + weight)
            dest.save(update_fields=[field_to_update])


@receiver([post_save, post_delete], sender=OrderStone)
def update_order_stone_weight(sender, instance, **kwargs):
    """
    Automatically updates the parent ManufacturingOrder's total_stone_weight 
    whenever a stone is added, modified, or removed from an order.
    Applies 'Tahyaaf' (Carats to Grams conversion) only for carat-based stones.
    """
    order = instance.order
    # Recalculate total weight using the weight_in_gold property (respects unit)
    total_weight = sum([os.weight_in_gold for os in order.orderstone_set.all()])
    order.total_stone_weight = total_weight
    # Save only the updated field
    order.save(update_fields=['total_stone_weight'])


from django.utils import timezone
from .models import ProductionStage

@receiver(pre_save, sender=ProductionStage)
def set_production_stage_timestamps(sender, instance, **kwargs):
    """
    Automated Time Tracking:
    1. Sets 'start_datetime' to NOW when the stage is first created (Entry Time).
    2. Sets 'end_datetime' to NOW when 'output_weight' is entered (Exit Time).
    """
    # 1. Entry Time (Start)
    if not instance.pk and not instance.start_datetime:
        instance.start_datetime = timezone.now()
    
    # 2. Exit Time (End)
    # If output is entered and we haven't stamped the end time yet
    if instance.output_weight and instance.output_weight > 0 and not instance.end_datetime:
        instance.end_datetime = timezone.now()



from .models import ProductionStage

@receiver(post_save, sender=ProductionStage)
def handle_production_stage_balances(sender, instance, created, **kwargs):
    """
    Handles Detailed Manufacturing Logic per State:
    1. Calculates Loss (Khasia) automatically.
    2. Updates Workshop Balances (Gold Debt, Powder Stock, Scrap Stock).
    3. Auto-Transfers to Next Workshop if requested.
    """
    # 1. Calculate Loss (Khasia) if I/O/P are present
    if instance.input_weight and instance.output_weight:
        # Standard: Loss = Input - Output - Powder
        # This allows negative values (Gain) which is correct for Laser (Solder addition) or Errors.
        calc_loss = instance.input_weight - instance.output_weight - (instance.powder_weight or 0)
        
        # Update loss field if changed (avoid recursion loop by checking)
        if instance.loss_weight != calc_loss:
            instance.loss_weight = calc_loss
            # Update without triggering signals to avoid infinite loop
            ProductionStage.objects.filter(pk=instance.pk).update(loss_weight=calc_loss)

    # 3. Auto-Transfer Logic
    if instance.next_workshop and not instance.is_transferred and instance.output_weight > 0:
        # Require User context for "initiated_by" if possible, or use system user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        system_user = User.objects.filter(is_superuser=True).first()

        with transaction.atomic():
            # Create Transfer Record
            # From: Current Workshop (instance.workshop)
            # To: Next Workshop (instance.next_workshop)
            
            # Verify we have a current workshop
            if not instance.workshop:
                # Fallback: Use Order's current workshop if stage has none
                from_ws = instance.order.workshop
            else:
                from_ws = instance.workshop
                
            if from_ws:
                # Create the Transfer
                transfer = WorkshopTransfer.objects.create(
                    transfer_number=f"TRF-{instance.order.order_number}-{instance.id}",
                    from_workshop=from_ws,
                    to_workshop=instance.next_workshop,
                    carat=instance.order.carat,
                    weight=instance.output_weight,
                    status='completed', # Auto-complete the transfer
                    initiated_by=system_user,
                    confirmed_by=system_user, 
                    notes=f"Auto-transfer from Stage: {instance.get_stage_name_display()}"
                )
                
                # Update Flags
                instance.is_transferred = True
                ProductionStage.objects.filter(pk=instance.pk).update(is_transferred=True)
                
                # Update Order's Current Location
                instance.order.workshop = instance.next_workshop
                instance.order.save(update_fields=['workshop'])



@receiver(post_save, sender=WorkshopSettlement)
def process_workshop_settlement(sender, instance, created, **kwargs):
    """
    Automated Balance Adjustment for Workshop Settlements
    ---------------------------------------------------
    1. Gold Payment: Treasury -> Workshop (Increases Workshop Debt/Balance)
    2. Scrap/Powder Receive: Workshop -> Treasury (Decreases Workshop Debt/Balance)
    """
    # Only process newly created settlements to avoid double counting on edits
    # (For a real production system, we'd handle updates/deletes too, but focusing on creation for now)
    if created and instance.workshop:
        with transaction.atomic():
            ws = instance.workshop
            
            # Determine which balance field to touch based on Carat (if applicable)
            gold_field = None
            filings_field = None
            
            if instance.carat:
                if '18' in instance.carat.name:
                    gold_field = 'gold_balance_18'
                    filings_field = 'filings_balance_18'
                elif '21' in instance.carat.name:
                    gold_field = 'gold_balance_21'
                    filings_field = 'filings_balance_21'
                elif '24' in instance.carat.name:
                    gold_field = 'gold_balance_24'
                    filings_field = 'filings_balance_24'

            # --- Logic based on Settlement Type ---
            
            # 1. We PAID Gold to the Workshop (They owe us more)
            if instance.settlement_type == 'gold_payment' and gold_field:
                current = getattr(ws, gold_field)
                setattr(ws, gold_field, current + instance.weight)
                
            # 2. We Custom Paid Labor (Cash) (They owe us / We paid off debt)
            elif instance.settlement_type == 'labor_payment':
                # Assuming 'amount' is paid TO workshop, reducing our debt to them 
                # OR increasing their cash debt to us if they work on credit.
                # Standard convention: Workshop Labor Balance is "Credit" (Money we owe them).
                # So Paying them reduces that balance.
                ws.labor_balance -= instance.amount

            # 3. We RECEIVED Scrap (Clear Gold Debt)
            elif instance.settlement_type == 'scrap_receive' and gold_field:
                current = getattr(ws, gold_field)
                setattr(ws, gold_field, current - instance.weight)

            # 4. We RECEIVED Powder (Clear Gold Debt)
            # User wants to deduct powder weight from the workshop's gold liability
            elif instance.settlement_type == 'powder_receive' and gold_field:
                # Deduct from Gold Balance (Debt)
                current_gold = getattr(ws, gold_field)
                setattr(ws, gold_field, current_gold - instance.weight)
                
                # OPTIONAL: Add to Filings Balance if you want to track how much powder they generated?
                # User scenario: "I receive powder... remove liability". 
                # If we want to track stock of powder *at the workshop*, we'd add it. 
                # But here we RECEIVED it, so it's gone from them.
                # If 'filings_balance' represents "Powder held BY Workshop", we don't add.
                # If 'filings_balance' represents "Total Powder Returned by Workshop", we add.
                # Let's stick to the financial implication: Debt Reduced.

            ws.save()

