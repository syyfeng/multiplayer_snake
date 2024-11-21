import pygame
import socket
import pickle
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import time

# Client configuration
server = "localhost"
port = 5555
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server, port))
pygame.init()
window_display = pygame.display.set_mode((500, 500)) # Set up the game window size
pygame.display.set_caption("Multiplayer Snake Game") # Set the window title
clock = pygame.time.Clock()

# Function to generate RSA key pair for the client
def generate_key_pair():
    key = RSA.generate(2048) # Generate an RSA key pair of 2048 bits
    return key.publickey(), key # Return the public and private keys


# Define predefined messages and their corresponding hotkeys
predefined_messages = {
    'z': "Congratulations!",
    'x': "It works!",
    'c': "Ready?",
}

# Flag to track whether a chat key has been pressed
chat_key_pressed = False

# Dictionary to store the last time each hotkey was pressed
last_message_time = {key: 0 for key in predefined_messages.keys()}

# Function to draw the grid on the game window
def draw_grid(wid, row, window_dis):
    size = wid // row
    x, y = 0, 0
    for lines in range(row):
        x += size
        y += size
        pygame.draw.line(window_dis, (255, 255, 255), (x, 0), (x, wid))
        pygame.draw.line(window_dis, (255, 255, 255), (0, y), (wid, y))

# Function to draw the game state (players and snacks) on the window
def draw_snakegame(window_dis, game_state, color_dict):
    window_dis.fill((0, 0, 0))
    draw_grid(500, 20, window_dis)
    players, snacks = game_state.split("|")
    players_positions = players.split("**")
    snacks_positions = snacks.split("**")
    for user_id, pos in zip(color_dict.keys(), players_positions):
        player_coords = pos.split("*")
        color = color_dict[user_id]
        for coord in player_coords:
            x, y = map(int, coord.strip("()").split(","))
            pygame.draw.rect(window_dis, color, (x * 25, y * 25, 25, 25))
    for snack_pos in snacks_positions:
        x, y = map(int, snack_pos.strip("()").split(","))
        pygame.draw.rect(window_dis, (0, 255, 0), (x * 25, y * 25, 25, 25))
    pygame.display.update() # Update the display to show changes

# Main game loop
def main():
    global chat_key_pressed, client_socket, window_display, client_public_key
    
    # Client key pair generation
    client_public_key, client_private_key = generate_key_pair()
    
    # Send client public key to the server
    client_public_key_bytes = client_public_key.export_key()
    client_socket.send(client_public_key_bytes)

    # Receive server's public key
    server_public_key_bytes = client_socket.recv(4096)
    server_public_key = RSA.import_key(server_public_key_bytes)
    
    running = True
    
    while running:
        pygame.time.delay(50)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Encrypt and send quit message to the server
                encrypted_quit_message = PKCS1_OAEP.new(server_public_key).encrypt("quit".encode())
                client_socket.send(encrypted_quit_message)
                running = False # Exit the loop when the window is closed
                
        keys = pygame.key.get_pressed() # Get the currently pressed keys
        current_time = time.time() # Get the current time
        
        # Check for arrow key presses and send corresponding commands to the server
        if keys[pygame.K_LEFT]:
            # Encrypt and send control message for moving left
            encrypted_control_message = PKCS1_OAEP.new(server_public_key).encrypt("left".encode())
            client_socket.send(encrypted_control_message)
        elif keys[pygame.K_RIGHT]:
            # Encrypt and send control message for moving right
            encrypted_control_message = PKCS1_OAEP.new(server_public_key).encrypt("right".encode())
            client_socket.send(encrypted_control_message)
        elif keys[pygame.K_UP]:
            # Encrypt and send control message for moving up
            encrypted_control_message = PKCS1_OAEP.new(server_public_key).encrypt("up".encode())
            client_socket.send(encrypted_control_message)
        elif keys[pygame.K_DOWN]:
            # Encrypt and send control message for moving down
            encrypted_control_message = PKCS1_OAEP.new(server_public_key).encrypt("down".encode())
            client_socket.send(encrypted_control_message)
        elif keys[pygame.K_SPACE]:
            # Encrypt and send reset message to the server
            encrypted_reset_message = PKCS1_OAEP.new(server_public_key).encrypt("reset".encode())
            client_socket.send(encrypted_reset_message)
        else:
            # Check for predefined message key presses
            for key, message in predefined_messages.items():
                if keys[pygame.key.key_code(key)] and not chat_key_pressed and current_time - last_message_time[key] > 1.0:
                    # Encrypt and send predefined chat message to the server
                    messageFinal = f"chat|{message}"
                    encrypted_chat_message = PKCS1_OAEP.new(server_public_key).encrypt(messageFinal.encode())
                    client_socket.send(encrypted_chat_message)
                    chat_key_pressed = True
                    # Update the last sent time for this hotkey
                    last_message_time[key] = current_time
                    break  # Exit the loop once a key is pressed

            # If no predefined message key is pressed, request the game state from the server
            else:
                chat_key_pressed = False
                # Encrypt and send get message to the server
                encrypted_get_message = PKCS1_OAEP.new(server_public_key).encrypt("get".encode())
                client_socket.send(encrypted_get_message)
              
        # Receive combined data containing color dictionary, game state, and chat message from the server
        combined_data = pickle.loads(client_socket.recv(4096)) 
        
        # Decrypt and extract color dictionary from the received data
        color_dict1 = PKCS1_OAEP.new(client_private_key).decrypt(combined_data['color_dict'])
        color_dict = pickle.loads(color_dict1)
        # Extract game state from the received data
        game_state = combined_data['game_state']
        # Decrypt and extract chat message from the received data
        chat_message = PKCS1_OAEP.new(client_private_key).decrypt(combined_data['chat_message']).decode()
        
        # Display chat message if not empty
        if chat_message:
            print(chat_message)
        
        # Draw the updated game state
        draw_snakegame(window_display, game_state, color_dict)
    
    client_socket.close()
    pygame.quit()
    
if __name__ == "__main__":
    main()
