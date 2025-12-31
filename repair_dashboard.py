import os

path = r'c:\Users\COMPU LINE\Desktop\mm\final\gold\templates\dashboard.html'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Join split {% if ... %} tags
        if '{% if' in line and '%}' not in line:
            j = i + 1
            combined = line.strip()
            while j < len(lines) and '%}' not in lines[j]:
                combined += " " + lines[j].strip()
                j += 1
            if j < len(lines):
                combined += " " + lines[j].strip()
            new_lines.append(combined + "\n")
            i = j + 1
        # Join split {{ ... }} tags
        elif '{{' in line and '}}' not in line:
            j = i + 1
            combined = line.strip()
            while j < len(lines) and '}}' not in lines[j]:
                combined += " " + lines[j].strip()
                j += 1
            if j < len(lines):
                combined += " " + lines[j].strip()
            new_lines.append(combined + "\n")
            i = j + 1
        else:
            new_lines.append(line)
            i += 1
            
    # Final cleanup of the structure for "everything under each other" problem
    content = "".join(new_lines)
    
    # Force grid layout to be horizontal consistently
    content = content.replace('minmax(280px, 1fr)', 'minmax(220px, 1fr)')
    # Ensure stats-grid has enough space and proper display
    if 'class="stats-grid"' in content and 'display: grid' not in content:
        content = content.replace('class="stats-grid"', 'class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; width: 100%;"')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed syntax and forced grid layout.")
else:
    print("File not found.")
