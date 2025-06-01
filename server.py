import asyncio
from aiohttp import web
from config import CAT_FAVORITE_FOODS, UDP_PORT, TCP_PORT, WEB_PORT

cat_stats = {
    'feed': {},
    'pet': {},
    'fed_users': set()
}

# UDP Server
class CatUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.fragments = {}

    def datagram_received(self, data, addr):
        message = data.decode()
        if message.endswith('~'):
            full_msg = self.fragments.pop(addr, '') + message
            user, food = full_msg.strip('~').split(' - ')
            response = self.feed_cat(user.strip('@'), food)
            self.transport.sendto(response.encode(), addr)
        elif message[-1].isdigit():
            frag_id = int(message[-1])
            self.fragments[addr] = self.fragments.get(addr, '') + message[:-1]
            self.transport.sendto(f"The Cat is amused by #{frag_id}".encode(), addr)

    def feed_cat(self, user, food):
        cat_stats['feed'].setdefault(user, []).append(food)
        if food in CAT_FAVORITE_FOODS:
            cat_stats['fed_users'].add(user)
            return "Eaten by the Cat"
        return "Ignored by the Cat"

    def connection_made(self, transport):
        self.transport = transport


# TCP Server
async def handle_tcp(reader, writer):
    addr = writer.get_extra_info('peername')
    buffer = ''
    tired_threshold = 6
    count = 0

    while not reader.at_eof():
        data = await reader.read(100)
        if not data:
            break
        buffer += data.decode()

        responses = []
        while '~' in buffer:
            segment, buffer = buffer.split('~', 1)
            user = segment.strip('@')
            count += 1
            status = "Tolerated by the Cat" if user in cat_stats['fed_users'] else "Scratched by the Cat"
            cat_stats['pet'].setdefault(user, []).append(status)
            responses.append(status)

        if responses:
            writer.write(''.join(responses).encode())
            await writer.drain()

        if count >= tired_threshold:
            writer.close()
            await writer.wait_closed()
            break


# Web Interface
async def stats_page(request):
    lines = ["<h1>Cat Stats</h1>", "<h2>Feeding</h2>", "<ul>"]
    for user, foods in cat_stats['feed'].items():
        lines.append(f"<li>{user}: {foods}</li>")
    lines.append("</ul><h2>Petting</h2><ul>")
    for user, results in cat_stats['pet'].items():
        lines.append(f"<li>{user}: {results}</li>")
    lines.append("</ul>")
    return web.Response(content_type='text/html', text='\n'.join(lines))


async def start_web_server():
    app = web.Application()
    app.router.add_get('/', stats_page)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', WEB_PORT)
    await site.start()


async def main():
    loop = asyncio.get_running_loop()

    print(f"Starting UDP on port {UDP_PORT}")
    await loop.create_datagram_endpoint(CatUDPProtocol, local_addr=('0.0.0.0', UDP_PORT))

    print(f"Starting TCP on port {TCP_PORT}")
    tcp_server = await asyncio.start_server(handle_tcp, '0.0.0.0', TCP_PORT)

    print("Starting Web Server")
    await start_web_server()

    async with tcp_server:
        await tcp_server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
