with open(r"d:\CodeBase\student_learn\frontend\src\views\Profile.vue", "r", encoding="utf-8") as f:
    content = f.read()

# Extract the layout structure (only template parts to see hierarchy)
in_template = False
depth = 0
for line in content.splitlines():
    s = line.strip()
    if '<template>' in s:
        in_template = True
        continue
    if '</template>' in s:
        break
    if not in_template: continue
    if s.startswith('<!--'):
        print(f'  {s}')
        continue
    # Show only div/class structure
    if any(t in s for t in ['class="layout"', 'class="sidebar"', 'class="chat-area-wrap"',
                             'class="profile-card"', 'class="chat-box"', 'class="self-assess"',
                             'class="insights"', 'class="wizard"', 'class="history"',
                             '<ProfileRadar']):
        indent = '  ' * (len(line) - len(line.lstrip()))
        print(f'{indent}{s[:120]}')
