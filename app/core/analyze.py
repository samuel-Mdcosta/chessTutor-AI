def classify_error(eval_diff):
    if eval_diff <= -3.0:
        return "blunder"
    elif eval_diff <= -1.5:
        return "mistake"
    elif eval_diff <= -0.5:
        return "inaccuracy"
    return "ok"
