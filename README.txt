Multiplayer Snake Game

This project consists of a multiplayer implementation of the classic Snake game.

File Descriptions
- snake.py: Implements the core gameplay, including collision detection, food placement, and rendering.
- snake_server.py: Manages multiplayer sessions, keeps track of player scores, and synchronizes game state.
- snake_client.py: Connects to the server, sends user inputs, and updates the game screen based on server responses.

Requirements
- Python 3.7 or higher
- Socket programming libraries (default in Python)
- Basic understanding of networking for setting up server-client connections.

How to Run
- Single-Player Mode
    1. Open a terminal or command prompt.
    2. Run the script.
    3. Use arrow keys to control the snake. The goal is to collect food and grow the snake while avoiding collisions with walls or itself.

- Multiplayer Mode
    Setting Up the Server
    1. Run the server script.
    2. The server will start listening on a specified port.

    Connecting Clients
    1. Run the client script.
    2. Enter the server's IP address and port when prompted.
    3. Use the arrow keys to control your snake in the multiplayer game.
