import socket
import threading
import pickle
import tictactoe as ttt

class TicTacToeServer:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.clients = []
        self.games = {}  # Dictionary to store game states: {game_id: (board, player1_conn, player2_conn)}
        
    def start(self):
        self.server_socket.listen()
        print(f"Server started on {self.host}:{self.port}")
        
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Connected to {address}")
            
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()
    
    def handle_client(self, client_socket):
        """Handle a client connection by either creating a new game or joining an existing one"""
        try:
            # First message should be either 'new' or 'join'
            data = client_socket.recv(1024)
            request = data.decode('utf-8')
            
            if request.startswith('new'):
                # Create a new game
                game_id = self.create_new_game(client_socket)
                client_socket.send(f"new_game:{game_id}".encode('utf-8'))
                
            elif request.startswith('join'):
                # Join an existing game
                _, game_id = request.split(':')
                success = self.join_game(client_socket, game_id)
                if success:
                    client_socket.send(f"joined:{game_id}".encode('utf-8'))
                else:
                    client_socket.send("error:game_not_found".encode('utf-8'))
                    
            # Now handle game moves
            self.handle_game_moves(client_socket)
                
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
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
    
    def handle_game_moves(self, client_socket):
        """Handle moves for a specific game"""
        game_id = None
        
        # Find which game this client belongs to
        for gid, (board, p1, p2) in self.games.items():
            if client_socket in (p1, p2):
                game_id = gid
                break
                
        if not game_id:
            return
            
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                message = data.decode('utf-8')
                if message.startswith('move'):
                    # Process move: move:i,j
                    _, coords = message.split(':')
                    i, j = map(int, coords.split(','))
                    
                    board, p1, p2 = self.games[game_id]
                    
                    # Check if it's this player's turn
                    current_player = ttt.player(board)
                    player_symbol = ttt.X if client_socket == p1 else ttt.O
                    
                    if current_player == player_symbol:
                        # Make the move
                        try:
                            new_board = ttt.result(board, (i, j))
                            self.games[game_id] = (new_board, p1, p2)
                            
                            # Send updated board to both players
                            board_data = pickle.dumps(new_board)
                            p1.send(f"board_update:{board_data}".encode('utf-8'))
                            if p2:
                                p2.send(f"board_update:{board_data}".encode('utf-8'))
                                
                            # Check if game is over
                            if ttt.terminal(new_board):
                                winner = ttt.winner(new_board)
                                result = "tie" if winner is None else f"winner:{winner}"
                                p1.send(f"game_over:{result}".encode('utf-8'))
                                if p2:
                                    p2.send(f"game_over:{result}".encode('utf-8'))
                        except ValueError:
                            client_socket.send("error:invalid_move".encode('utf-8'))
                    else:
                        client_socket.send("error:not_your_turn".encode('utf-8'))
                        
            except Exception as e:
                print(f"Error in game {game_id}: {e}")
                break
        
        # Clean up the game if a player disconnects
        if game_id in self.games:
            board, p1, p2 = self.games[game_id]
            if client_socket == p1 and p2:
                p2.send("opponent_disconnected".encode('utf-8'))
            elif client_socket == p2 and p1:
                p1.send("opponent_disconnected".encode('utf-8'))
            del self.games[game_id]

if __name__ == "__main__":
    server = TicTacToeServer()
    server.start()