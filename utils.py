def try_until_complete(func):
    while True:
        try:
            result = func()
        except Exception:
            continue
        else:
            return result
