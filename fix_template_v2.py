from pathlib import Path
import re

path = Path(r"c:\Users\COMPU LINE\Desktop\mm\final\gold\templates\analytics\analytics_dashboard.html")
content = path.read_text(encoding="utf-8")

# 1. Fix missing spaces in if statements
fixed = content.replace("days==7", "days == 7")
fixed = fixed.replace("days==30", "days == 30")
fixed = fixed.replace("days==90", "days == 90")
fixed = fixed.replace("days==365", "days == 365")
fixed = fixed.replace('selected_branch==branch.id|stringformat:"s"', 'selected_branch == branch.id|stringformat:"s"')

# 2. Fix the split slow_moving_count tag using regex to be flexible
# Matches the specific pattern of the split tag and replaces it with a single line version
pattern = r'style="{% if slow_moving_count > 10 %}(.*?){\% endif \%}">\s*{{' + '\n' + r'\s*slow_moving_count }}\s*</span>'
replacement = r'style="{% if slow_moving_count > 10 %}\1{% endif %}">{{ slow_moving_count }}</span>'

# Simple string replace for the specific case if regex is too complex/brittle
target_split = 'style="{% if slow_moving_count > 10 %}background: rgba(244,67,54,0.2); color:#f44336;{% endif %}">{{\n                                slow_moving_count }}</span>'
fixed_solid = 'style="{% if slow_moving_count > 10 %}background: rgba(244,67,54,0.2); color:#f44336;{% endif %}">{{ slow_moving_count }}</span>'

# Try strict string replace first for the slow_moving_count part finding the exact multispace version might be tricky, 
# so let's try to just normalize the specific block if found.
# Actually, let's read the file line by line or allow for variation?
# The findstr output showed:
# style="{% if slow_moving_count > 10 %}background: rgba(244,67,54,0.2); color:#f44336;{% endif %}">{{
#                                 slow_moving_count }}</span></td>

# Let's try to construct a cleaner replace
if 'slow_moving_count }}\n' in fixed or 'slow_moving_count }}</span>' not in fixed:
    # It seems split. Let's try to collapse it.
    fixed = re.sub(r'">\s*{{\s*\n\s*slow_moving_count\s*}}\s*</span>', '">{{ slow_moving_count }}</span>', fixed)

path.write_text(fixed, encoding="utf-8")
print("Applied comprehensive fixes.")
