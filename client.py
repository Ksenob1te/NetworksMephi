import socket
import asyncio
from random import shuffle

from config import *


def feed_cat_mixed_udp(server_ip, port, message, max_chunk_size=2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    chunks = [message[i:i + max_chunk_size] for i in range(0, len(message), max_chunk_size)]

    for i, chunk in enumerate(chunks):
        if chunk[-1] != "~":
            chunks[i] = f"{chunk}~{i}"
        else:
            chunks[i] = chunk

    chunk_2 = chunks.pop(2)
    chunks.append(chunk_2)

    for i, chunk in enumerate(chunks):
        sock.sendto(chunk.encode(), (server_ip, port))
        try:
            data, _ = sock.recvfrom(1024)
            print(f"Response to fragment #{chunk[-1]}:", data.decode())
        except socket.timeout:
            print(f"No response for fragment #{i}")


def feed_cat_udp(server_ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    sock.sendto(message.encode(), (server_ip, port))
    try:
        data, _ = sock.recvfrom(1024)
        print("Response:", data.decode())
    except socket.timeout:
        print("No response from server")

    sock.close()


async def pet_cat_tcp(server_ip, port, ids=None):
    reader, writer = await asyncio.open_connection(server_ip, port)
    print("Connected to the Cat (TCP). Type '@yourID~' to pet the Cat. Type 'exit' to quit.")

    if ids:
        # Если переданы изначально ID — отправляем их сразу
        writer.write(''.join(ids).encode())
        await writer.drain()
        data = await reader.read(1024)
        print("Response:", data.decode())

    try:
        while True:
            user_input = input("Send ID: ")
            if user_input.lower() == 'exit':
                break
            if not user_input.endswith('~'):
                print("ID must end with '~'")
                continue

            writer.write(user_input.encode())
            await writer.drain()

            data = await reader.read(1024)
            if not data:
                print("Connection closed by the server.")
                break
            print("Response:", data.decode())
    finally:
        writer.close()
        await writer.wait_closed()
        print("Connection closed.")


if __name__ == '__main__':
    feed_cat_udp(SERVER_IP, 12345, "@Alex - Milk~")
    feed_cat_udp(SERVER_IP, 12345, "@007 - Beer~")

    asyncio.run(pet_cat_tcp(SERVER_IP, 54321, ["@Alex~", "@007~", "@Alex~"]))
