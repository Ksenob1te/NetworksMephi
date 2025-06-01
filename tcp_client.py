import asyncio
from config import *


async def pet_cat_tcp(server_ip, port, ids=None):
    reader, writer = await asyncio.open_connection(server_ip, port)
    print("Connected to the Cat (TCP). Type 'yourID' to pet the Cat. Type 'exit' to quit.")

    if ids:
        writer.write(''.join(ids).encode())
        await writer.drain()
        data = await reader.read(1024)
        print("Response:", data.decode())

    try:
        while True:
            user_input = input("Send ID: ")
            if user_input.lower() == 'exit':
                break
            # user_input = f"@{user_input}~"
            writer.write(user_input.encode())
            await writer.drain()

            if user_input.endswith("~"):
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
    asyncio.run(pet_cat_tcp(SERVER_IP, 54321, []))
