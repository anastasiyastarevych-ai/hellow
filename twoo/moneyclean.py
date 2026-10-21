def get_amount(line):
    parts = line.split()
    if len(parts) != 2:
        return None
    try:
        return float(parts[1])
    except ValueError:
        return None


def shadow(limit=200):
    def decorator(gen_func):
        def wrapper(*args, **kwargs):
            gen = gen_func(*args, **kwargs)
            total = 0
            activated = False
            while True:
                try:
                    line = next(gen)
                except StopIteration as e:
                    return e.value
                print("Рядок:", line)
                amount = get_amount(line)
                if amount is not None:
                    total += amount
                    if total > limit and not activated:
                        print("Тіньовий ліміт перевищено. Активую схему.")
                        activated = True
                yield line
        return wrapper
    return decorator


def suspicious_counter(threshold=300):
    def decorator(gen_func):
        def wrapper(*args, **kwargs):
            gen = gen_func(*args, **kwargs)
            total = 0
            suspicious_sum = 0
            while True:
                try:
                    line = next(gen)
                except StopIteration as e:
                    print("Підозріла сума за весь час:", suspicious_sum)
                    return e.value
                amount = get_amount(line)
                if amount is not None:
                    total += amount
                    if total > threshold:
                        suspicious_sum += amount
                        print("Увага! Підозріла транзакція:", line)
                yield line
        return wrapper
    return decorator


@shadow(limit=200)
@suspicious_counter(threshold=300)
def transactions(data):
    total = 0
    for line in data:
        yield line
        amount = get_amount(line)
        if amount is not None:
            total += amount
    return total


data = [
    "payment 120",
    "refund 50",
    "hello",
    "transfer 300",
    "payment abc",
    "payment 80",
]

gen = transactions(data)
while True:
    try:
        next(gen)
    except StopIteration as e:
        print("Фінальна сума:", e.value)
        break