import asyncio
from aiohttp import web
from config import *
import re
from html_page import *
from dnslib.server import DNSServer, DNSHandler, BaseResolver
from dnslib import DNSRecord, RR, QTYPE, SRV, A
import socket



class CatUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.sessions = {}  # addr: { 'received': {}, 'next_expected': int, 'last_fragment': str or None }
        self.fragment_pattern = re.compile(r'~(\d+)$')
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    @staticmethod
    def _has_all_fragments(session):
        return session['received'] and len(session['received']) == session['next_expected'] and session['last_fragment'] is not None

    def datagram_received(self, data, addr):
        message = data.decode()

        match = self.fragment_pattern.search(message)
        is_fragment = bool(match)

        if not message.endswith('~') and not is_fragment:
            session = self.sessions.get(addr)
            if session:
                last_seq = session['next_expected'] - 1
                response = f"The Cat is amused by #{last_seq}"
                self.transport.sendto(response.encode(), addr)
            return

        if is_fragment or self.sessions.get(addr):
            # SESSION MODE
            session = self.sessions.setdefault(addr, {
                'received': {},
                'next_expected': 0,
                'last_fragment': None,
            })

            if is_fragment:
                frag_id = int(match.group(1))
                content = message[:match.start()]
                session['received'][frag_id] = content

                while session['next_expected'] in session['received']:
                    session['next_expected'] += 1
            elif message.endswith('~'):
                session['last_fragment'] = message.strip('~')

            if not self._has_all_fragments(session):
                response = f"The Cat is amused by #{session['next_expected'] - 1}"
                self.transport.sendto(response.encode(), addr)
                return

            try:
                parts = [session['received'][i] for i in range(session['next_expected'])]
                full_msg = ''.join(parts) + session['last_fragment']
                user, food = full_msg.split(' - ')
                response = self.feed_cat(user.strip('@'), food)
            except Exception:
                response = "Invalid format"

            self.transport.sendto(response.encode(), addr)
            self.sessions.pop(addr, None)
        else:
            # NON-SESSION MODE
            try:
                user, food = message.split(' - ')
                response = self.feed_cat(user.strip('@'), food.strip('~'))
            except Exception:
                response = "Invalid format"
            self.transport.sendto(response.encode(), addr)

    @staticmethod
    def feed_cat(user, food):
        cat_stats['feed'].setdefault(user, []).append(food)
        if food in CAT_FAVORITE_FOODS:
            cat_stats['fed_users'].add(user)
            return "Eaten by the Cat"
        return "Ignored by the Cat"


# TCP Server
async def handle_tcp(reader, writer):
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
            if not segment.startswith('@'):
                continue
            user = segment.strip('@')
            count += 1

            if user in cat_stats['fed_users']:
                status = "Tolerated by the Cat"
            else:
                status = "Scratched by the Cat"

            cat_stats['pet'].setdefault(user, []).append(status)
            responses.append(status)

        if responses:
            writer.write(''.join(responses).encode())
            await writer.drain()

        if count >= tired_threshold:
            writer.close()
            await writer.wait_closed()
            break


class CatDNSResolver(BaseResolver):
    def resolve(self, request, handler):
        reply = request.reply()
        qname = str(request.q.qname)
        qtype = QTYPE[request.q.qtype]

        if qtype == 'SRV':
            if qname == "_feed-the-cat._udp.example.com.":
                reply.add_answer(RR(qname, QTYPE.SRV, ttl=86400, rdata=SRV(5, 5, UDP_PORT, "your-cat-server.example.com.")))
            elif qname == "_pet-the-cat._tcp.example.com.":
                reply.add_answer(RR(qname, QTYPE.SRV, ttl=86400, rdata=SRV(5, 5, TCP_PORT, "your-cat-server.example.com.")))
        elif qtype == 'A' and qname == "your-cat-server.example.com.":
            ip = socket.gethostbyname(socket.gethostname())
            reply.add_answer(RR(qname, QTYPE.A, ttl=86400, rdata=A(ip)))

        return reply


def start_dns_server():
    resolver = CatDNSResolver()
    dns_server = DNSServer(resolver, address="0.0.0.0", port=DNS_PORT)
    dns_server.start_thread()
    print(f"DNS server started on port {DNS_PORT}")


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

    print("Starting DNS Server")
    start_dns_server()

    async with tcp_server:
        await tcp_server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
