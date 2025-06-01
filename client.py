import socket
import asyncio

def feed_cat_udp(server_ip, port, message, max_chunk_size=8):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    chunks = [message[i:i + max_chunk_size] for i in range(0, len(message), max_chunk_size)]

    if len(chunks) > 1:
        for i, chunk in enumerate(chunks):
            fragment = f"{chunk}~{i}"
            sock.sendto(fragment.encode(), (server_ip, port))
            try:
                data, _ = sock.recvfrom(1024)
                print(f"Response to fragment #{i}:", data.decode())
            except socket.timeout:
                print(f"No response for fragment #{i}")
    else:
        sock.sendto(message.encode(), (server_ip, port))
        try:
            data, _ = sock.recvfrom(1024)
            print("Response:", data.decode())
        except socket.timeout:
            print("No response from server")

    sock.close()


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
