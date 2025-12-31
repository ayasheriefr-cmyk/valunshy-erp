import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import Carat, GoldPrice
from inventory.models import Item, RawMaterial
from manufacturing.models import ManufacturingOrder, WorkshopTransfer, WorkshopSettlement, InstallationTool
from django.db.models import ProtectedError

# Fix encoding for console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run():
    print("Starting Carat cleanup (DELETION MODE)...")

    # 1. Ensure target carats exist (We surely keep these)
    # Using 'get' to ensure we identify the existing ones correctly before deleting others
    
    # We want to keep ONLY "عيار 18" and "عيار 21"
    # Note: names might vary slightly (e.g. "18K", "21K"), so we need to be careful.
    # But the user's prompt specifically mentions "عيار 18" and "عيار 21".
    
    kept_carats_ids = []
    
    # helper to find or create
    def ensure_carat(name, purity):
        c, created = Carat.objects.get_or_create(name=name, defaults={'purity': purity})
        return c

    c18 = ensure_carat("عيار 18", 0.750)
    c21 = ensure_carat("عيار 21", 0.875)
    
    kept_carats_ids.append(c18.id)
    kept_carats_ids.append(c21.id)

    print(f"Keeping IDs: {kept_carats_ids} ({c18.name}, {c21.name})")

    # 2. Iterate and DELETE others
    all_carats = Carat.objects.exclude(id__in=kept_carats_ids)
    
    for carat in all_carats:
        print(f"Processing carat for deletion: {carat.name} (ID: {carat.id})")
        
        # We must delete related objects first because of on_delete=PROTECT
        
        # 1. Manufacturing Orders
        orders = ManufacturingOrder.objects.filter(carat=carat)
        count = orders.count()
        if count > 0:
            print(f" - Deleting {count} ManufacturingOrders...")
            orders.delete()
            
        # 2. Workshop Transfers
        transfers = WorkshopTransfer.objects.filter(carat=carat)
        count = transfers.count()
        if count > 0:
            print(f" - Deleting {count} WorkshopTransfers...")
            transfers.delete()
            
        # 3. Inventory Items
        items = Item.objects.filter(carat=carat)
        count = items.count()
        if count > 0:
            print(f" - Deleting {count} Items...")
            items.delete()
            
        # 4. Raw Materials
        raw_materials = RawMaterial.objects.filter(carat=carat)
        count = raw_materials.count()
        if count > 0:
            print(f" - Deleting {count} RawMaterials...")
            raw_materials.delete()
            
        # 5. Workshop Settlements (These are usually SET_NULL but let's check or delete if specific)
        # Based on models.py: carats can be null. But if the user wants to wipe the '24k' history, 
        # maybe we should just set them to null or delete? 
        # User said "delete related transactions". A settlement is a transaction.
        # But if we delete the settlement, we mess up the workshop balance history theoretically?
        # However, if the balance was 24k, the column on Workshop is 'gold_balance_24'. 
        # Deleting the transaction record doesn't automatically reset the float field on Workshop model.
        # Ideally we should reverse the balance, but that's complex. 
        # For now, we will just delete the FK reference to allow Carat deletion, or delete the object itself.
        # Given "امسح الحركات", let's delete the settlement object.
        settlements = WorkshopSettlement.objects.filter(carat=carat)
        count = settlements.count()
        if count > 0:
            print(f" - Deleting {count} WorkshopSettlements...")
            settlements.delete()

        # 6. Installation Tools (SET_NULL is likely safe, but let's see)
        # These are likely definitions of tools.
        tools = InstallationTool.objects.filter(carat=carat)
        count = tools.count()
        if count > 0:
            print(f" - Unlinking carat from {count} InstallationTools (keeping tools)...")
            tools.update(carat=None)

        # 7. Gold Prices
        prices = GoldPrice.objects.filter(carat=carat)
        count = prices.count()
        if count > 0:
            print(f" - Deleting {count} GoldPrices...")
            prices.delete()

        # Finally, delete the carat
        try:
            carat.delete()
            print(f"Successfully deleted carat: {carat.name}")
        except ProtectedError as e:
            print(f"CRITICAL: Could not delete '{carat.name}' due to protected references: {e}")
        except Exception as e:
            print(f"Error deleting '{carat.name}': {e}")

    print("Cleanup complete.")

if __name__ == "__main__":
    run()
