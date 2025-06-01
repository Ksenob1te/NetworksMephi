from collections import Counter
from aiohttp import web

cat_stats = {
    'feed': {},
    'pet': {},
    'fed_users': set()
}


async def stats_page(request):
    html = """
    <html>
    <head>
        <title>Cat Stats</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f8f8f8; padding: 20px; }
            h1 { color: #444; }
            h2 { color: #666; margin-top: 30px; }
            ul { list-style: none; padding-left: 0; }
            li { background: #fff; border: 1px solid #ddd; padding: 10px; margin-bottom: 5px; border-radius: 5px; }
            .username { font-weight: bold; color: #333; }
            .item-list { color: #555; }
            .count { font-weight: bold; color: #222; }
        </style>
    </head>
    <body>
        <h1>🐱 Cat Stats</h1>

        <h2>🍽️ Feeding</h2>
        <ul>
    """

    for user, foods in cat_stats['feed'].items():
        food_counts = Counter(foods)
        food_str = ', '.join(f"{food} <span class='count'>×{count}</span>" for food, count in food_counts.items())
        html += f"<li><span class='username'>{user}</span>: <span class='item-list'>{food_str}</span></li>"

    html += """
        </ul>

        <h2>🤚 Petting</h2>
        <ul>
    """

    for user, results in cat_stats['pet'].items():
        pet_counts = Counter(results)
        pet_str = ', '.join(f"{status} <span class='count'>×{count}</span>" for status, count in pet_counts.items())
        html += f"<li><span class='username'>{user}</span>: <span class='item-list'>{pet_str}</span></li>"

    html += """
        </ul>
    </body>
    </html>
    """

    return web.Response(content_type='text/html', text=html)
