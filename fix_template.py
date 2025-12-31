import re

filepath = r'c:\Users\COMPU LINE\Desktop\mm\final\gold\templates\finance\monthly_analytics_report.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix template syntax: add spaces around == in if tags
content = re.sub(r"report_type=='(\w+)'", r'report_type == "\1"', content)
content = re.sub(r"month==m\.value", r"month == m.value", content)
content = re.sub(r"year==y", r"year == y", content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed template syntax with proper UTF-8 encoding!")
