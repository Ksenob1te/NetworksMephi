import socket
import asyncio

def feed_cat_udp(server_ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (server_ip, port))
    data, _ = sock.recvfrom(1024)
    print("Response:", data.decode())

async def pet_cat_tcp(server_ip, port, ids):
    reader, writer = await asyncio.open_connection(server_ip, port)
    writer.write(''.join(ids).encode())
    await writer.drain()
    data = await reader.read(1024)
    print("Response:", data.decode())
    writer.close()
    await writer.wait_closed()

if __name__ == '__main__':
    feed_cat_udp('127.0.0.1', 12345, "@Alex - Milk~")
    feed_cat_udp('127.0.0.1', 12345, "@007 - Beer~")

    asyncio.run(pet_cat_tcp('127.0.0.1', 54321, ["@Alex~", "@007~", "@Alex~"]))
