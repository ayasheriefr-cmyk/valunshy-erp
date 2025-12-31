from pathlib import Path
import re

path = Path(r"c:\Users\COMPU LINE\Desktop\mm\final\gold\templates\analytics\analytics_dashboard.html")
try:
    content = path.read_text(encoding="utf-8")
except UnicodeDecodeError:
    content = path.read_text(encoding="cp1256")

# 1. Fix missing spaces in if statements (The logical errors)
replacements = {
    "days==7": "days == 7",
    "days==30": "days == 30",
    "days==90": "days == 90",
    "days==365": "days == 365",
    'selected_branch==branch.id|stringformat:"s"': 'selected_branch == branch.id|stringformat:"s"',
    "slow_moving_count> 10": "slow_moving_count > 10",
    "slow_moving_count>10": "slow_moving_count > 10"
}

for old, new in replacements.items():
    content = content.replace(old, new)

# 2. Fix the split tag issue by collapsing whitespace within the specific span block
# We use regex to find the badge and ensure the variable is on one line
pattern = r'(<span class="value-badge"[^>]*>)\s*{{ slow_moving_count }}\s*(</span>)'
# Note: The regex above assumes the previous fix attempts might have left it cleaner.
# If it's still the messy split version:
# style="...background: ...;"... >{{
#                                slow_moving_count }}</span>

# Let's search for the variable with surrounding generic whitespace and collapse it.
content = re.sub(r'>\s*{{\s*slow_moving_count\s*}}\s*</span>', '>{{ slow_moving_count }}</span>', content)

path.write_text(content, encoding="utf-8")
print("Applied comprehensive fixes for all syntax errors.")
