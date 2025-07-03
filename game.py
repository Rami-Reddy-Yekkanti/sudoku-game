from flask import Flask, render_template, request, jsonify, session
import numpy as np

app = Flask(__name__)
app.secret_key = 'sudoku_game_secret_key'

# Initial board state
INITIAL_BOARD = np.array([[0, 0, 0, 8, 0, 0, 6, 0, 2],
                          [6, 4, 0, 5, 0, 7, 0, 0, 0],
                          [8, 0, 7, 0, 6, 0, 0, 0, 0],
                          [4, 9, 6, 3, 0, 2, 1, 0, 7],
                          [2, 0, 0, 4, 7, 0, 0, 9, 6],
                          [7, 5, 3, 9, 0, 0, 0, 0, 4],
                          [1, 0, 0, 2, 0, 9, 0, 0, 0],
                          [0, 6, 0, 7, 0, 0, 0, 0, 0],
                          [0, 7, 4, 0, 5, 1, 9, 2, 0]])

def initialize_board():
    return INITIAL_BOARD.copy()

# Sudoku Rule Validations
def is_valid_row(board, row_number, value):
    for i in range(9):
        if board[row_number][i] == value:
            return False
    return True

def is_valid_column(board, column_number, value):
    for i in range(9):
        if board[i][column_number] == value:
            return False
    return True

def is_valid_box(board, row_number, column_number, value):
    row_start = row_number - (row_number % 3)
    col_start = column_number - (column_number % 3)
    for i in range(3):
        for j in range(3):
            if board[row_start + i][col_start + j] == value:
                return False
    return True

def is_board_complete(board):
    return not np.any(board == 0)

def is_initial_cell(row, col):
    return INITIAL_BOARD[row][col] != 0

# ---------------------------------------------------------------------------------------------------------------
# Home Page Route
@app.route('/')
def index():
    # If this is the user's first visit, initialize the board in their session
    if 'board' not in session:
        session['board'] = initialize_board().tolist()

    # Show the HTML page
    return render_template('index.html')


# Get the current game board
@app.route('/get_board')
def get_board():
    # If the board isn't already stored in session, create one
    if 'board' not in session:
        session['board'] = initialize_board().tolist()

    # Prepare board and which cells are original (cannot be changed)
    board_data = {
        'board': session['board'],
        'initial_cells': [
            [bool(is_initial_cell(i, j)) for j in range(9)] for i in range(9)
        ]
    }
    
    return jsonify(board_data)


# Handle a move
@app.route('/make_move', methods=['POST'])
def make_move():
    # Get move details from frontend
    data = request.get_json()
    row = data['row']        
    col = data['col']        
    value = data['value']

    # Make sure the board exists in session
    if 'board' not in session:
        session['board'] = initialize_board().tolist()
    board = np.array(session['board'])

    # Prevent editing the original puzzle cells
    if is_initial_cell(row, col):
        return jsonify({
            'success': False,
            'message': 'Cannot modify initial puzzle cells!'
        })

    # Block attempts to overwrite non-empty cells
    if board[row][col] != 0 and value != 0:
        return jsonify({
            'success': False,
            'message': 'Cell already filled!'
        })

    # If the user wants to clear the cell (enter 0)
    if value == 0:
        board[row][col] = 0
        session['board'] = board.tolist()

        return jsonify({
            'success': True,
            'message': 'Cell cleared!',
            'board': session['board'],
            'game_won': False
        })

    # Validate the new number using Sudoku rules
    is_row_ok = is_valid_row(board, row, value)
    is_col_ok = is_valid_column(board, col, value)
    is_box_ok = is_valid_box(board, row, col, value)

    if is_row_ok and is_col_ok and is_box_ok:
        # Valid move: update the board
        board[row][col] = value
        session['board'] = board.tolist()

        # Check if game is won
        has_won = is_board_complete(board)

        return jsonify({
            'success': True,
            'message': 'Congratulations! You won!' if has_won else 'Valid move!',
            'board': session['board'],
            'game_won': has_won
        })

    else:
        # Show specific rule errors
        errors = []
        if not is_row_ok:
            errors.append('Row rule violated')
        if not is_col_ok:
            errors.append('Column rule violated')
        if not is_box_ok:
            errors.append('Box rule violated')

        return jsonify({
            'success': False,
            'message': 'Invalid move: ' + ', '.join(errors)
        })


# Reset the game to initial state
@app.route('/reset_game', methods=['POST'])
def reset_game_server_side():
    session['board'] = initialize_board().tolist()

    response_data = {
        'success': True,
        'message': 'Game Reset Done!',
        'board'  : session['board'] 
    }
    return jsonify(response_data)

# Run the server\
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
