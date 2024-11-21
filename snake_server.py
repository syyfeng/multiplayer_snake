import numpy as np
import socket
from _thread import *
import pickle
from snake import SnakeGame
import uuid
import time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Server configuration
server = "localhost"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
counter = 0
rows = 20

try:
    s.bind((server, port)) # Binding the socket to the server address and port
except socket.error as e:
    print(str(e))

s.listen(2)
print("Waiting for a connection, Server Started")

# Initialize the SnakeGame instance
game = SnakeGame(rows)
game_state = "" # Initialize game state as an empty string
last_move_timestamp = time.time()
interval = 0.2
moves_queue = set()

# Dictionary to store client public keys
client_public_keys = {}

# Function to generate RSA key pair
def generate_key_pair():
    key = RSA.generate(2048) # Generate an RSA key of 2048 bits
    return key.publickey(), key # Return the public and private keys

# List to store client connections
clients = []
client_ids = {}

broadcasting = False

# Function to broadcast a chat message to all connected clients
def broadcast_message(message, sender_id):
    global game, clients, broadcasting, client_public_keys
    broadcasting = True
    print(f"User {sender_id} says: {message}") # Print the sender's message
    
    for conn in clients:
        if message:  # Check if message is not empty
            # Get the recipient's unique_id
            recipient_id = client_ids[conn]
            
            # Retrieve the recipient's public key
            recipient_public_key = client_public_keys[recipient_id]
            
            # Retrieve colors of players in the game
            color_dict = {user_id: game.players[user_id].color for user_id in game.players}

            # Encrypt color_dict with recipient's public key
            encrypted_color_dict = PKCS1_OAEP.new(recipient_public_key).encrypt(pickle.dumps(color_dict))
            
            # Encrypt chat message with recipient's public key
            encrypted_chat_message = PKCS1_OAEP.new(recipient_public_key).encrypt((f"User {sender_id} says: {message}").encode())

            # Prepare the data to be sent
            combined_data = {
                'color_dict': encrypted_color_dict, # Encrypted color dictionary
                'game_state': game_state, # Current game state
                'chat_message': encrypted_chat_message # Encrypted chat message
            }

            # Send the data to the recipient
            conn.send(pickle.dumps(combined_data))

    broadcasting = False # Broadcasting finished


# Function to handle the game loop for a thread
def game_thread():
    global game, moves_queue, game_state, last_move_timestamp
    while True:
        last_move_timestamp = time.time()
        game.move(moves_queue)
        moves_queue = set()
        game_state = game.get_state()
        while time.time() - last_move_timestamp < interval:
            time.sleep(0.1)

# RGB color definitions for players
rgb_colors = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
}
rgb_colors_list = list(rgb_colors.values())

# Function to generate a random color for a player
def generate_random_color(used_colors):
    rgb_colors_list = list(rgb_colors.values())

    # Exclude the color green and the colors already used by players
    available_colors = [color for color in rgb_colors_list if color not in used_colors and color != (0, 255, 0)]

    if not available_colors:
        # If all colors are used, return a random color
        return rgb_colors_list[np.random.randint(0, len(rgb_colors_list))]

    # Return a random available color
    return available_colors[np.random.randint(0, len(available_colors))]

# Modify the client_thread function to send the color dictionary, game_state and chat messages to the client
def client_thread(conn, addr, server_private_key):
    global game, moves_queue, game_state, client_ids, client_public_keys
    unique_id = str(uuid.uuid4()) # Generate a unique ID for the client

    # Receive client's public key
    client_public_key_bytes = conn.recv(4096)
    client_public_key = RSA.import_key(client_public_key_bytes)
    client_public_keys[unique_id] = client_public_key

    # Generate a random color for the player
    color = generate_random_color([player.color for player in game.players.values()])
    # Add the player with the generated color
    game.add_player(unique_id, color=color)
    
    client_ids[conn] = unique_id
    start_new_thread(game_thread, ())

    while True:
        # Receive data from the client
        data_received = conn.recv(4096)

        # Decrypt received data using server's private key
        data = PKCS1_OAEP.new(server_private_key).decrypt(data_received).decode()

        move = None
        # Get color info of players
        color_dict = {user_id: game.players[user_id].color for user_id in game.players}

        # Encrypt color_dict with recipient's public key
        encrypted_color_dict = PKCS1_OAEP.new(client_public_keys[unique_id]).encrypt(pickle.dumps(color_dict))
        
        message = ""
        # Encrypt message with recipient's public key
        encrypted_chat_message = PKCS1_OAEP.new(client_public_keys[unique_id]).encrypt(message.encode())

        # Prepare combined data (color dictionary, game state, and chat message) to be sent as one message
        combined_data = {
            'color_dict': encrypted_color_dict, # Encrypted color dictionary
            'game_state': game_state, # Current game state
            'chat_message': encrypted_chat_message # Encrypted chat message
        }
        conn.send(pickle.dumps(combined_data)) # Send the combined data to the client

        if not data:
            print("No data received from client")
            break

         # Process different types of received data from the client
        elif data.startswith("chat|"):
            parts = data.split('|')
            if len(parts) == 2:
                _, message = parts
                print(f"{message}")
                broadcast_message(message, unique_id)
            else:
                print("Invalid chat message format:", data)
        elif data == "get":
            print("Received get")
        elif data == "quit":
            print("Received quit")
            game.remove_player(unique_id)
            del client_ids[conn]
            clients.remove(conn)
            break
        elif data == "reset":
            game.reset_player(unique_id)
        elif data in ["up", "down", "left", "right"]:
            move = data
            moves_queue.add((unique_id, move))
        else:
            print("Invalid data received from client:", data)

    conn.close()


# Main function
def main():
    global s, game, clients

    # Server key pair generation
    server_public_key, server_private_key = generate_key_pair()

    try:
        while True:
            conn, addr = s.accept() # Accept a new connection
            clients.append(conn)
            # Send server public key to the client
            server_public_key_bytes = server_public_key.export_key()
            conn.send(server_public_key_bytes)

            print("Connected to:", addr)
            start_new_thread(client_thread, (conn, addr, server_private_key))

    except KeyboardInterrupt:
        print("Server shutting down...")
        s.close()  # Close the server socket

        # Close all client connections
        for conn in clients:
            conn.close()

        print("Server successfully shut down.")

if __name__ == "__main__":
    main()
