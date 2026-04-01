import chess.pgn
import re
import numpy as np
from collections import defaultdict

def extract_wv(comment):
    """Extract the 'wv' value from a move comment string."""
    if not comment:
        return None
    match = re.search(r'wv=([-+]?\d+\.?\d*)', comment)
    if match:
        return float(match.group(1))
    return None

def is_book_move(comment):
    """Check if the move comment indicates a book move."""
    return comment and "book" in comment

def normalize_sequence(vals):
    """
    vals: list of floats.
    Returns the normalized sequence: first remove linear trend (first -> last),
    then scale to unit variance.
    """
    n = len(vals)
    if n < 2:
        return None
    first, last = vals[0], vals[-1]
    trend = [first + (last - first) * i / (n - 1) for i in range(n)]
    detrended = [v - t for v, t in zip(vals, trend)]
    std = np.std(detrended)
    if std == 0:
        return np.zeros(n)  # all constant after detrending
    return np.array(detrended) / std

def cross_correlation(w, b, max_lag=10):
    """
    Compute Pearson correlation between w and b for lags -max_lag..+max_lag.
    Returns the lag that maximizes the correlation.
    """
    n = len(w)
    if n != len(b):
        raise ValueError("Lengths of w and b must be equal")
    best_lag = 0
    best_corr = -np.inf
    for lag in range(-max_lag, max_lag+1):
        if lag >= 0:
            # w[0:n-lag] vs b[lag:n]
            if n - lag == 0:
                continue
            w_slice = w[0:n-lag]
            b_slice = b[lag:n]
        else:
            # w[-lag:n] vs b[0:n+lag]
            pos_lag = -lag
            if n - pos_lag == 0:
                continue
            w_slice = w[pos_lag:n]
            b_slice = b[0:n-pos_lag]
        # Pearson correlation coefficient
        if len(w_slice) < 2:
            continue
        corr = np.corrcoef(w_slice, b_slice)[0,1]
        if np.isnan(corr):
            continue
        if corr > best_corr:
            best_corr = corr
            best_lag = lag
    return best_lag

def process_game(game):
    """Extract evaluation sequences and compute cross-correlation lag."""
    white_elo = int(game.headers.get("WhiteElo", 0))
    black_elo = int(game.headers.get("BlackElo", 0))
    elo_diff = white_elo - black_elo

    # Traverse the mainline moves
    node = game
    white_vals = []
    black_vals = []
    stop = False
    first_non_book_found = False

    while node.variations and not stop:
        node = node.variation(0)   # take main line
        comment = node.comment
        if not comment:
            continue
        if is_book_move(comment):
            continue   # skip book moves entirely
        # Not a book move: use it
        wv = extract_wv(comment)
        if wv is None:
            continue   # no evaluation, skip
        # Determine side: ply is 1-indexed
        ply = node.ply()
        if ply % 2 == 1:   # white's move
            white_vals.append(wv)
        else:              # black's move
            black_vals.append(wv)
        # Check stop condition: absolute evaluation exceeds 4.0
        if abs(wv) > 4.0:
            stop = True   # we include this move, but stop after processing it

    # If we didn't get any moves, skip
    if not white_vals or not black_vals:
        return None, None

    # Trim to equal length (drop extra from the side that made the last move)
    min_len = min(len(white_vals), len(black_vals))
    if min_len < 2:
        return None, None
    white_vals = white_vals[:min_len]
    black_vals = black_vals[:min_len]

    # Normalize
    w_norm = normalize_sequence(white_vals)
    b_norm = normalize_sequence(black_vals)
    if w_norm is None or b_norm is None:
        return None, None

    # Compute best lag
    lag = cross_correlation(w_norm, b_norm)
    return lag, elo_diff

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py games.pgn")
        sys.exit(1)
    filename = sys.argv[1]

    pos_lags = []
    neg_lags = []

    with open(filename) as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
            lag, elo_diff = process_game(game)
            if lag is not None:
                if elo_diff > 0:
                    pos_lags.append(lag)
                elif elo_diff < 0:
                    neg_lags.append(lag)

    avg_pos = np.mean(pos_lags) if pos_lags else float('nan')
    avg_neg = np.mean(neg_lags) if neg_lags else float('nan')

    print(f"Average maximal correlation position (positive Elo diff): {avg_pos:.2f}")
    print(f"Average maximal correlation position (negative Elo diff): {avg_neg:.2f}")

if __name__ == "__main__":
    main()
