import pygame
import sys
import time
import socket
import pickle
import threading

import tictactoe as ttt

pygame.init()
size = width, height = 600, 400

# Colors
black = (0, 0, 0)
white = (255, 255, 255)

screen = pygame.display.set_mode(size)

mediumFont = pygame.font.Font("OpenSans-Regular.ttf", 28)
largeFont = pygame.font.Font("OpenSans-Regular.ttf", 40)
moveFont = pygame.font.Font("OpenSans-Regular.ttf", 60)

# Game variables
user = None
board = ttt.initial_state()
ai_turn = False
game_mode = None  # "ai", "host", or "join"
client_socket = None
game_id = None
player_symbol = None
network_turn = False
waiting_for_opponent = False
opponent_disconnected = False

# Network message queue
message_queue = []

def connect_to_server(host='127.0.0.1', port=65432):
    """Connect to the game server"""
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        return True
    except Exception as e:
        print(f"Failed to connect: {e}")
        return False

def create_game():
    """Create a new network game"""
    global game_id, player_symbol, waiting_for_opponent
    if client_socket:
        client_socket.send("new".encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        if response.startswith("new_game"):
            _, game_id = response.split(":")
            player_symbol = ttt.X
            waiting_for_opponent = True
            return True
    return False

def join_game(game_to_join):
    """Join an existing network game"""
    global game_id, player_symbol
    if client_socket:
        client_socket.send(f"join:{game_to_join}".encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        if response.startswith("joined"):
            _, game_id = response.split(":")
            player_symbol = ttt.O
            return True
    return False

def listen_for_messages():
    """Background thread to listen for server messages"""
    global board, network_turn, message_queue, client_socket
    while client_socket:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
                
            message = data.decode('utf-8')
            
            # Handle binary board data specially
            if message.startswith("board_update:"):
                try:
                    _, board_data_str = message.split(":", 1)
                    board_data = pickle.loads(eval(board_data_str))
                    message = "board_updated"
                    board = board_data
                except Exception as e:
                    print(f"Error unpickling board: {e}")
            
            message_queue.append(message)
            
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    
    print("Disconnected from server")
    if client_socket:
        client_socket.close()
        client_socket = None

def process_messages():
    """Process any messages in the queue"""
    global board, network_turn, message_queue, game_mode, waiting_for_opponent, opponent_disconnected
    
    if not message_queue:
        return
    
    new_queue = []
    for message in message_queue:
        if message == "board_updated":
            # Board was already updated in the listener
            network_turn = False
            
        elif message == "opponent_joined":
            waiting_for_opponent = False
            network_turn = False
            
        elif message == "opponent_disconnected":
            opponent_disconnected = True
            
        elif message.startswith("game_over"):
            # Handle game over - keep message for display purpose
            new_queue.append(message)
            
        elif message.startswith("error:"):
            # Keep error messages
            new_queue.append(message)
    
    message_queue = new_queue

def send_move(i, j):
    """Send a move to the server"""
    if client_socket:
        try:
            client_socket.send(f"move:{i},{j}".encode('utf-8'))
            return True
        except:
            return False
    return False

def reset_game():
    """Reset the game state"""
    global user, board, ai_turn, game_mode, client_socket, game_id, player_symbol, network_turn, waiting_for_opponent, opponent_disconnected
    user = None
    board = ttt.initial_state()
    ai_turn = False
    game_mode = None
    game_id = None
    player_symbol = None
    network_turn = False
    waiting_for_opponent = False
    opponent_disconnected = False
    if client_socket:
        try:
            client_socket.close()
        except:
            pass
        client_socket = None

def get_game_id_input():
    """Show an input field for game ID"""
    input_text = ""
    input_active = True
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_text
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if event.unicode.isdigit():
                        input_text += event.unicode
        
        screen.fill(black)
        
        # Draw title
        title = largeFont.render("Enter Game ID", True, white)
        titleRect = title.get_rect()
        titleRect.center = ((width / 2), 50)
        screen.blit(title, titleRect)
        
        # Draw input box
        input_box = pygame.Rect(width/4, height/2, width/2, 50)
        pygame.draw.rect(screen, white, input_box, 2)
        
        # Render input text
        text_surface = mediumFont.render(input_text, True, white)
        text_rect = text_surface.get_rect()
        text_rect.center = input_box.center
        screen.blit(text_surface, text_rect)
        
        # Draw submit button
        submit_button = pygame.Rect(width/3, 3*height/4, width/3, 50)
        pygame.draw.rect(screen, white, submit_button)
        submit_text = mediumFont.render("Join", True, black)
        submit_text_rect = submit_text.get_rect()
        submit_text_rect.center = submit_button.center
        screen.blit(submit_text, submit_text_rect)
        
        # Check if button is clicked
        click, _, _ = pygame.mouse.get_pressed()
        if click == 1:
            mouse = pygame.mouse.get_pos()
            if submit_button.collidepoint(mouse):
                time.sleep(0.2)
                return input_text
        
        pygame.display.flip()

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if client_socket:
                client_socket.close()
            sys.exit()

    screen.fill(black)

    # Let user choose a game mode if not chosen
    if game_mode is None:
        # Draw title
        title = largeFont.render("Tic-Tac-Toe", True, white)
        titleRect = title.get_rect()
        titleRect.center = ((width / 2), 50)
        screen.blit(title, titleRect)

        # Draw buttons for game modes
        aiButton = pygame.Rect((width / 8), (height / 2) - 60, width / 4, 50)
        aiText = mediumFont.render("Play vs AI", True, black)
        aiTextRect = aiText.get_rect()
        aiTextRect.center = aiButton.center
        pygame.draw.rect(screen, white, aiButton)
        screen.blit(aiText, aiTextRect)

        hostButton = pygame.Rect(5 * (width / 8), (height / 2) - 60, width / 4, 50)
        hostText = mediumFont.render("Host Game", True, black)
        hostTextRect = hostText.get_rect()
        hostTextRect.center = hostButton.center
        pygame.draw.rect(screen, white, hostButton)
        screen.blit(hostText, hostTextRect)

        joinButton = pygame.Rect((width / 3), (height / 2) + 20, width / 3, 50)
        joinText = mediumFont.render("Join Game", True, black)
        joinTextRect = joinText.get_rect()
        joinTextRect.center = joinButton.center
        pygame.draw.rect(screen, white, joinButton)
        screen.blit(joinText, joinTextRect)

        # Check if button is clicked
        click, _, _ = pygame.mouse.get_pressed()
        if click == 1:
            mouse = pygame.mouse.get_pos()
            if aiButton.collidepoint(mouse):
                time.sleep(0.2)
                game_mode = "ai"
                user = None  # Let user choose X or O as in original game
            elif hostButton.collidepoint(mouse):
                time.sleep(0.2)
                if connect_to_server():
                    if create_game():
                        game_mode = "network"
                        user = player_symbol
                        # Start listening for messages
                        threading.Thread(target=listen_for_messages, daemon=True).start()
            elif joinButton.collidepoint(mouse):
                time.sleep(0.2)
                game_id_to_join = get_game_id_input()
                if game_id_to_join and connect_to_server():
                    if join_game(game_id_to_join):
                        game_mode = "network"
                        user = player_symbol
                        # Start listening for messages
                        threading.Thread(target=listen_for_messages, daemon=True).start()

    # AI game mode (similar to original code)
    elif game_mode == "ai" and user is None:
        # Let user choose a player.
        # Draw title
        title = largeFont.render("Play Tic-Tac-Toe", True, white)
        titleRect = title.get_rect()
        titleRect.center = ((width / 2), 50)
        screen.blit(title, titleRect)

        # Draw buttons
        playXButton = pygame.Rect((width / 8), (height / 2), width / 4, 50)
        playX = mediumFont.render("Play as X", True, black)
        playXRect = playX.get_rect()
        playXRect.center = playXButton.center
        pygame.draw.rect(screen, white, playXButton)
        screen.blit(playX, playXRect)

        playOButton = pygame.Rect(5 * (width / 8), (height / 2), width / 4, 50)
        playO = mediumFont.render("Play as O", True, black)
        playORect = playO.get_rect()
        playORect.center = playOButton.center
        pygame.draw.rect(screen, white, playOButton)
        screen.blit(playO, playORect)

        # Check if button is clicked
        click, _, _ = pygame.mouse.get_pressed()
        if click == 1:
            mouse = pygame.mouse.get_pos()
            if playXButton.collidepoint(mouse):
                time.sleep(0.2)
                user = ttt.X
            elif playOButton.collidepoint(mouse):
                time.sleep(0.2)
                user = ttt.O

    # Network game waiting for opponent
    elif game_mode == "network" and waiting_for_opponent:
        # Process any network messages
        process_messages()
        
        # Draw waiting message
        title = largeFont.render(f"Game ID: {game_id}", True, white)
        titleRect = title.get_rect()
        titleRect.center = ((width / 2), 50)
        screen.blit(title, titleRect)
        
        waiting = mediumFont.render("Waiting for opponent...", True, white)
        waitingRect = waiting.get_rect()
        waitingRect.center = ((width / 2), height / 2)
        screen.blit(waiting, waitingRect)
    
    # Check if opponent disconnected
    elif game_mode == "network" and opponent_disconnected:
        title = largeFont.render("Opponent Disconnected", True, white)
        titleRect = title.get_rect()
        titleRect.center = ((width / 2), 50)
        screen.blit(title, titleRect)
        
        # Back button
        backButton = pygame.Rect((width / 3), (height / 2) + 20, width / 3, 50)
        backText = mediumFont.render("Back to Menu", True, black)
        backTextRect = backText.get_rect()
        backTextRect.center = backButton.center
        pygame.draw.rect(screen, white, backButton)
        screen.blit(backText, backTextRect)
        
        click, _, _ = pygame.mouse.get_pressed()
        if click == 1:
            mouse = pygame.mouse.get_pos()
            if backButton.collidepoint(mouse):
                time.sleep(0.2)
                reset_game()
                
    # Game play (both AI and network)
    elif user is not None:
        # Process network messages if in network mode
        if game_mode == "network":
            process_messages()
        
        # Draw game board
        tile_size = 80
        tile_origin = (width / 2 - (1.5 * tile_size),
                       height / 2 - (1.5 * tile_size))
        tiles = []
        for i in range(3):
            row = []
            for j in range(3):
                rect = pygame.Rect(
                    tile_origin[0] + j * tile_size,
                    tile_origin[1] + i * tile_size,
                    tile_size, tile_size
                )
                pygame.draw.rect(screen, white, rect, 3)

                if board[i][j] != ttt.EMPTY:
                    move = moveFont.render(board[i][j], True, white)
                    moveRect = move.get_rect()
                    moveRect.center = rect.center
                    screen.blit(move, moveRect)
                row.append(rect)
            tiles.append(row)

        game_over = ttt.terminal(board)
        player = ttt.player(board)

        # Show title
        if game_over:
            winner = ttt.winner(board)
            if winner is None:
                title = f"Game Over: Tie."
            else:
                title = f"Game Over: {winner} wins."
        elif (game_mode == "ai" and user == player) or \
             (game_mode == "network" and player_symbol == player and not network_turn):
            title = f"Play as {user}"
        elif game_mode == "network" and player_symbol != player:
            title = "Opponent's turn..."
        else:
            title = f"Computer thinking..."
            
        title = largeFont.render(title, True, white)
        titleRect = title.get_rect()
        titleRect.center = ((width / 2), 30)
        screen.blit(title, titleRect)

        # Show game ID if in network mode
        if game_mode == "network" and game_id:
            id_text = mediumFont.render(f"Game ID: {game_id}", True, white)
            id_rect = id_text.get_rect()
            id_rect.center = ((width / 2), height - 30)
            screen.blit(id_text, id_rect)

        # Check for AI move
        if game_mode == "ai" and user != player and not game_over:
            if ai_turn:
                time.sleep(0.5)
                move = ttt.minimax(board)
                board = ttt.result(board, move)
                ai_turn = False
            else:
                ai_turn = True

        # Check for a user move
        click, _, _ = pygame.mouse.get_pressed()
        if click == 1 and not game_over:
            if (game_mode == "ai" and user == player) or \
               (game_mode == "network" and player_symbol == player and not network_turn):
                mouse = pygame.mouse.get_pos()
                for i in range(3):
                    for j in range(3):
                        if (board[i][j] == ttt.EMPTY and tiles[i][j].collidepoint(mouse)):
                            if game_mode == "network":
                                # Send move to server
                                if send_move(i, j):
                                    network_turn = True
                            else:
                                # Make move locally for AI game
                                board = ttt.result(board, (i, j))

        if game_over:
            againButton = pygame.Rect(width / 3, height - 65, width / 3, 50)
            again = mediumFont.render("Play Again", True, black)
            againRect = again.get_rect()
            againRect.center = againButton.center
            pygame.draw.rect(screen, white, againButton)
            screen.blit(again, againRect)
            click, _, _ = pygame.mouse.get_pressed()
            if click == 1:
                mouse = pygame.mouse.get_pos()
                if againButton.collidepoint(mouse):
                    time.sleep(0.2)
                    reset_game()

    pygame.display.flip()