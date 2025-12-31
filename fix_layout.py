import os

path = r'c:\Users\COMPU LINE\Desktop\mm\final\gold\templates\dashboard.html'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Precise replacements for layout fixes
    changes = {
        'class="main-wrapper"': 'class="main-wrapper" style="padding: 20px; display: flex; flex-direction: column; gap: 20px;"',
        'class="stats-grid"': 'class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px;"',
        'class="gold-price-bar"': 'class="gold-price-bar" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;"'
    }
    
    for old, new in changes.items():
        content = content.replace(old, new)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Dashboard Layout Repaired Successfully.")
else:
    print("File not found.")
