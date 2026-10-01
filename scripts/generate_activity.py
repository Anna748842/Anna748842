import json
import os
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

USERNAME = "Anna748842"
OUTPUT_DIR = Path("profile")

API_URL = "https://api.github.com/graphql"

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""

end_date = date.today()
start_date = end_date - timedelta(days=364)

payload = json.dumps({
    "query": query,
    "variables": {
        "login": USERNAME,
        "from": f"{start_date.isoformat()}T00:00:00Z",
        "to": f"{end_date.isoformat()}T23:59:59Z"
    }
}).encode("utf-8")

request = urllib.request.Request(
    API_URL,
    data=payload,
    headers={
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Content-Type": "application/json",
        "User-Agent": "Anna748842-profile-generator"
    },
    method="POST"
)

with urllib.request.urlopen(request) as response:
    data = json.loads(response.read().decode("utf-8"))

if "errors" in data:
    raise RuntimeError(data["errors"])

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

days = []

for week in weeks:
    for d in week["contributionDays"]:
        days.append(d)

# -------------------------------------------------------------
# STREAK
# -------------------------------------------------------------

day_counts = {
    d["date"]: d["contributionCount"]
    for d in days
}

cursor = end_date
current_streak = 0

while True:
    key = cursor.isoformat()

    if day_counts.get(key, 0) > 0:
        current_streak += 1
        cursor -= timedelta(days=1)
    else:
        break

longest_streak = 0
running = 0

sorted_dates = sorted(day_counts.keys())

for d in sorted_dates:
    if day_counts[d] > 0:
        running += 1
        longest_streak = max(longest_streak, running)
    else:
        running = 0

# -------------------------------------------------------------
# COLORS
# -------------------------------------------------------------

LEVEL_COLORS = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353"
}

# -------------------------------------------------------------
# ACTIVITY SVG
# -------------------------------------------------------------

WIDTH = 1200
HEIGHT = 245

svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 {WIDTH} {HEIGHT}">

<defs>
    <filter id="glow">
        <feGaussianBlur stdDeviation="5"/>
    </filter>

    <linearGradient id="lineGlow" x1="0" x2="1">
        <stop offset="0%" stop-color="#58a6ff"/>
        <stop offset="50%" stop-color="#7ee787"/>
        <stop offset="100%" stop-color="#bc8cff"/>
    </linearGradient>
</defs>

<rect width="{WIDTH}" height="{HEIGHT}"
      rx="12"
      fill="#0d1117"/>

<rect x="1" y="1"
      width="{WIDTH-2}"
      height="{HEIGHT-2}"
      rx="12"
      fill="none"
      stroke="#30363d"/>

<text x="28" y="34"
      font-family="Segoe UI,Arial,sans-serif"
      font-size="19"
      font-weight="700"
      fill="#f0f6fc">
    Contribution Activity
</text>

<text x="28" y="58"
      font-family="Segoe UI,Arial,sans-serif"
      font-size="12"
      fill="#8b949e">
    {total:,} contributions in the last year
</text>

'''

# Heatmap geometry
left = 28
top = 78
cell = 13
gap = 3

# Ensure at most 53 columns
max_weeks = min(len(weeks), 53)

for x, week in enumerate(weeks[-max_weeks:]):
    for y, d in enumerate(week["contributionDays"]):

        px = left + x * (cell + gap)
        py = top + y * (cell + gap)

        level = d["contributionLevel"]
        color = LEVEL_COLORS.get(level, "#161b22")

        svg += f'''
<rect x="{px}"
      y="{py}"
      width="{cell}"
      height="{cell}"
      rx="2"
      fill="{color}">
    <title>{d["date"]}: {d["contributionCount"]} contributions</title>
</rect>
'''

# animated scan
svg += f'''
<rect x="{left}"
      y="{top-4}"
      width="3"
      height="110"
      rx="2"
      fill="url(#lineGlow)"
      opacity=".85"
      filter="url(#glow)">
    <animate
        attributeName="x"
        values="{left};{left + (max_weeks-1)*(cell+gap)};{left}"
        dur="7s"
        repeatCount="indefinite"/>
</rect>
'''

# Legend
legend_y = 190

svg += f'''
<text x="{left}"
      y="{legend_y}"
      font-family="Segoe UI,Arial,sans-serif"
      font-size="11"
      fill="#8b949e">
    Less
</text>
'''

legend = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353"
]

for i, color in enumerate(legend):
    x = left + 48 + i * 18

    svg += f'''
<rect x="{x}"
      y="{legend_y-11}"
      width="12"
      height="12"
      rx="2"
      fill="{color}"/>
'''

svg += f'''
<text x="{left+150}"
      y="{legend_y}"
      font-family="Segoe UI,Arial,sans-serif"
      font-size="11"
      fill="#8b949e">
    More
</text>

<rect x="28"
      y="216"
      width="1144"
      height="2"
      fill="#21262d"/>

<rect x="28"
      y="216"
      width="150"
      height="2"
      fill="url(#lineGlow)">
    <animate
        attributeName="width"
        values="150;650;150"
        dur="5s"
        repeatCount="indefinite"/>
</rect>

</svg>
'''

OUTPUT_DIR.mkdir(exist_ok=True)

(OUTPUT_DIR / "activity.svg").write_text(svg, encoding="utf-8")

# -------------------------------------------------------------
# STREAK SVG
# -------------------------------------------------------------

streak_svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 900 190">

<defs>
    <linearGradient id="streak" x1="0" x2="1">
        <stop offset="0%" stop-color="#f78166"/>
        <stop offset="100%" stop-color="#ffb86c"/>
    </linearGradient>
</defs>

<rect width="900" height="190"
      rx="12"
      fill="#0d1117"/>

<rect x="1" y="1"
      width="898"
      height="188"
      rx="12"
      fill="none"
      stroke="#30363d"/>

<text x="450" y="35"
      text-anchor="middle"
      font-family="Segoe UI,Arial,sans-serif"
      font-size="18"
      font-weight="700"
      fill="#f0f6fc">
    GitHub Streak
</text>

<g font-family="Segoe UI,Arial,sans-serif"
   text-anchor="middle">

    <text x="220" y="85"
          font-size="36"
          font-weight="700"
          fill="#f78166">
        {current_streak}
    </text>

    <text x="220" y="110"
          font-size="12"
          fill="#8b949e">
        CURRENT STREAK
    </text>

    <line x1="450" y1="65"
          x2="450" y2="135"
          stroke="#30363d"/>

    <text x="680" y="85"
          font-size="36"
          font-weight="700"
          fill="#58a6ff">
        {longest_streak}
    </text>

    <text x="680" y="110"
          font-size="12"
          fill="#8b949e">
        LONGEST STREAK
    </text>
</g>

<rect x="150"
      y="145"
      width="600"
      height="3"
      rx="2"
      fill="#21262d"/>

<rect x="150"
      y="145"
      width="110"
      height="3"
      rx="2"
      fill="url(#streak)">
    <animate
        attributeName="width"
        values="110;500;110"
        dur="4s"
        repeatCount="indefinite"/>
</rect>

</svg>
'''

(OUTPUT_DIR / "streak.svg").write_text(
    streak_svg,
    encoding="utf-8"
)

print("Profile activity assets generated successfully.")