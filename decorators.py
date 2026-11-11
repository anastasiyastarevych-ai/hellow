from functools import wraps


def parse_amount(line):
    if not isinstance(line, str):
        return None
    parts = line.split()
    if len(parts) != 2 or not parts[0].isalpha():
        return None
    try:
        amount = float(parts[1])
    except ValueError:
        return None
    if not 0 <= amount < float("inf"):
        return None
    return amount


def shadow(limit=200):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            generator = func(*args, **kwargs)
            total = 0
            activated = False
            while True:
                try:
                    line = next(generator)
                except StopIteration:
                    return total
                amount = parse_amount(line)
                if amount is None:
                    continue
                print(f"Транзакція: {line}")
                total += amount
                if total > limit and not activated:
                    print("Тіньовий ліміт перевищено. Активую схему")
                    activated = True
                yield line
        return wrapper
    return decorator


def suspicious_counter(threshold=250):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            generator = func(*args, **kwargs)
            count = 0
            while True:
                try:
                    line = next(generator)
                except StopIteration as stop:
                    return stop.value
                amount = parse_amount(line)
                if amount is None:
                    continue
                if amount > threshold:
                    count += 1
                    print(f"Підозріла транзакція «{line}» (поріг {threshold}). Усього підозрілих: {count}")
                yield line
        return wrapper
    return decorator


@suspicious_counter(threshold=250)
@shadow(limit=200)
def transactions(lines):
    for line in lines:
        yield line


def run(generator):
    while True:
        try:
            next(generator)
        except StopIteration as stop:
            return stop.value


if __name__ == "__main__":
    data = ["payment 120", "refund 50", "oops", "transfer 300", "payment abc", "payment 40"]
    total = run(transactions(data))
    print(f"Фінальна сума: {total:.2f}")