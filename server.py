import socket
import threading
import pickle
import tictactoe as ttt
import time

class TicTacToeServer:
    def __init__(self, host='192.168.22.71', port=8000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.clients = []
        self.games = {}  # Dictionary to store game states: {game_id: (board, player1_conn, player2_conn)}
        self.lock = threading.Lock()  # Add lock for thread safety
        
    def start(self):
        self.server_socket.listen()
        print(f"[SERVER] Started on {self.host}:{self.port}")
        print(f"[SERVER] Waiting for connections...")
        
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"[CONNECTION] New connection from {address}")
                
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.daemon = True  # Make thread daemon so it closes when main thread exits
                client_thread.start()
                print(f"[THREADING] Active threads: {threading.active_count()}")
        except KeyboardInterrupt:
            print("[SERVER] Shutting down server...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        print("[SERVER] Cleaning up resources...")
        # Close all game connections
        for game_id, (_, p1, p2) in self.games.items():
            try:
                if p1: p1.close()
                if p2: p2.close()
            except:
                pass
        # Close server socket
        self.server_socket.close()
        print("[SERVER] Server shutdown complete")
    
    def handle_client(self, client_socket, address):
        """Handle a client connection by either creating a new game or joining an existing one"""
        game_id = None
        try:
            # First message should be either 'new' or 'join'
            data = client_socket.recv(1024)
            request = data.decode('utf-8')
            
            if request.startswith('new'):
                # Create a new game
                with self.lock:
                    game_id = self.create_new_game(client_socket)
                print(f"[GAME] New game created: Game ID {game_id} by {address}")
                client_socket.send(f"new_game:{game_id}".encode('utf-8'))
                print(f"[GAME:{game_id}] Waiting for opponent to join...")
                
            elif request.startswith('join'):
                # Join an existing game
                _, game_id = request.split(':')
                with self.lock:
                    success = self.join_game(client_socket, game_id)
                if success:
                    print(f"[GAME:{game_id}] Player {address} joined")
                    client_socket.send(f"joined:{game_id}".encode('utf-8'))
                    print(f"[GAME:{game_id}] Game is ready to start")
                else:
                    print(f"[ERROR] Failed to join game {game_id} - game not found or full")
                    client_socket.send("error:game_not_found".encode('utf-8'))
                    return
            else:
                print(f"[ERROR] Unknown request from {address}: {request}")
                client_socket.send("error:invalid_request".encode('utf-8'))
                return
                    
            # Now handle game moves
            self.handle_game_moves(client_socket, game_id, address)
                
        except Exception as e:
            print(f"[ERROR] Error handling client {address}: {e}")
        finally:
            print(f"[CONNECTION] Client {address} disconnected")
            if game_id:
                print(f"[GAME:{game_id}] Game ended due to player disconnect")
            client_socket.close()
    
    def create_new_game(self, client_socket):
        """Create a new game and return its ID"""
        game_id = str(len(self.games) + 1)
        board = ttt.initial_state()
        self.games[game_id] = (board, client_socket, None)
        return game_id
    
    def join_game(self, client_socket, game_id):
        """Join an existing game if it exists and is not full"""
        if game_id in self.games and self.games[game_id][2] is None:
            board, player1, _ = self.games[game_id]
            self.games[game_id] = (board, player1, client_socket)
            
            # Notify first player that someone joined
            player1.send("opponent_joined".encode('utf-8'))
            return True
        return False
    
    def handle_game_moves(self, client_socket, game_id, address):
        """Handle moves for a specific game"""
        # Find which player number this client is (1 or 2)
        board, p1, p2 = self.games[game_id]
        player_num = 1 if client_socket == p1 else 2
        player_symbol = ttt.X if player_num == 1 else ttt.O
            
        print(f"[GAME:{game_id}] Player {player_num} ({player_symbol}) ready at {address}")
            
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    print(f"[GAME:{game_id}] Player {player_num} disconnected")
                    break
                    
                message = data.decode('utf-8')
                if message.startswith('move'):
                    # Process move: move:i,j
                    _, coords = message.split(':')
                    i, j = map(int, coords.split(','))
                    print(f"[GAME:{game_id}] Player {player_num} attempts move at ({i},{j})")
                    
                    with self.lock:
                        board, p1, p2 = self.games[game_id]
                    
                        # Check if it's this player's turn
                        current_player = ttt.player(board)
                        
                        if current_player == player_symbol:
                            # Make the move
                            try:
                                new_board = ttt.result(board, (i, j))
                                self.games[game_id] = (new_board, p1, p2)
                                print(f"[GAME:{game_id}] Valid move by Player {player_num} at ({i},{j})")
                                
                                # Send updated board to both players
                                board_data = pickle.dumps(new_board)
                                p1.send(f"board_update:{len(board_data)}".encode('utf-8'))
                                time.sleep(0.1)  # Small delay to ensure message separation
                                p1.send(board_data)
                                
                                if p2:
                                    p2.send(f"board_update:{len(board_data)}".encode('utf-8'))
                                    time.sleep(0.1)  # Small delay to ensure message separation
                                    p2.send(board_data)
                                    
                                # Check if game is over
                                if ttt.terminal(new_board):
                                    winner = ttt.winner(new_board)
                                    if winner is None:
                                        print(f"[GAME:{game_id}] Game ended in a tie")
                                        result = "tie"
                                    else:
                                        winner_num = 1 if winner == ttt.X else 2
                                        print(f"[GAME:{game_id}] Player {winner_num} wins")
                                        result = f"winner:{winner}"
                                    
                                    p1.send(f"game_over:{result}".encode('utf-8'))
                                    if p2:
                                        p2.send(f"game_over:{result}".encode('utf-8'))
                                    
                                    # Clean up the game
                                    print(f"[GAME:{game_id}] Game completed successfully")
                                    del self.games[game_id]
                                    return
                                
                            except ValueError as ve:
                                print(f"[GAME:{game_id}] Invalid move by Player {player_num}: {ve}")
                                client_socket.send("error:invalid_move".encode('utf-8'))
                        else:
                            print(f"[GAME:{game_id}] Not Player {player_num}'s turn")
                            client_socket.send("error:not_your_turn".encode('utf-8'))
                else:
                    print(f"[GAME:{game_id}] Unknown message from Player {player_num}: {message}")
                        
            except Exception as e:
                print(f"[ERROR] Error in game {game_id} with Player {player_num}: {e}")
                break
        
        # Clean up the game if a player disconnects
        with self.lock:
            if game_id in self.games:
                board, p1, p2 = self.games[game_id]
                if client_socket == p1 and p2:
                    print(f"[GAME:{game_id}] Player 1 disconnected, notifying Player 2")
                    p2.send("opponent_disconnected".encode('utf-8'))
                elif client_socket == p2 and p1:
                    print(f"[GAME:{game_id}] Player 2 disconnected, notifying Player 1")
                    p1.send("opponent_disconnected".encode('utf-8'))
                print(f"[GAME:{game_id}] Game ended due to player disconnect")
                del self.games[game_id]

if __name__ == "__main__":
    try:
        server = TicTacToeServer()
        print("[SERVER] TicTacToe Server Initializing...")
        server.start()
    except Exception as e:
        print(f"[FATAL] Server failed to start: {e}")