from pathlib import Path

path = Path(r"c:\Users\COMPU LINE\Desktop\mm\final\gold\templates\analytics\analytics_dashboard.html")
try:
    content = path.read_text(encoding="utf-8")
except UnicodeDecodeError:
    content = path.read_text(encoding="cp1256") # Fallback for windows

# 1. Fix missing spaces in if statements (The root cause of 500 Error)
replacements = {
    "days==7": "days == 7",
    "days==30": "days == 30",
    "days==90": "days == 90",
    "days==365": "days == 365",
    'selected_branch==branch.id|stringformat:"s"': 'selected_branch == branch.id|stringformat:"s"'
}

for old, new in replacements.items():
    content = content.replace(old, new)

# 2. Ensure slow_moving_count is clean (The root cause of display error)
# We make sure it's just a simple number display without complex styling that might break parsing
if "{{ slow_moving_count }}" in content:
    pass # It's already simplified, likely fine
else:
    # If it's the complex version, simplify it
    # We search for the span and replace it entirely if it looks complex
    import re
    # Match the span with style and the variable, loosely
    pattern = r'<span class="value-badge" style=".*?">{{\s*slow_moving_count\s*}}</span>'
    simple_version = '<span class="value-badge">{{ slow_moving_count }}</span>'
    content = re.sub(pattern, simple_version, content, flags=re.DOTALL)

path.write_text(content, encoding="utf-8")
print("Successfully applied fixes for days== and slow_moving_count.")
