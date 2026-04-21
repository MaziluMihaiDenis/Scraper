import random

def calculate_ean13_checksum(number: str) -> str:
    """Compute the EAN-13 checksum digit for a 12-digit string."""
    assert len(number) == 12 and number.isdigit()
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(number))
    checksum = (10 - (total % 10)) % 10
    return str(checksum)

def generate_ean13(prefix="594"):  # Romania's country prefix
    """Generate a single valid EAN-13 code with the given prefix."""
    # Generate random digits to reach 12 total (checksum added later)
    base = prefix + ''.join(str(random.randint(0, 9)) for _ in range(12 - len(prefix)))
    return base + calculate_ean13_checksum(base)

def generate_ean13_list(count=10, prefix="594"):
    """Generate a list of valid EAN-13 codes."""
    return [generate_ean13(prefix) for _ in range(count)]

def save_to_txt(codes, filename="ean13_codes.txt"):
    """Save EAN-13 codes to a text file, one per line."""
    with open(filename, "w") as f:
        for code in codes:
            f.write(code + "\n")
    print(f"Saved {len(codes)} EAN-13 codes to {filename}")

if __name__ == "__main__":
    count = int(input("How many EAN-13 codes do you want to generate? "))
    codes = generate_ean13_list(count)
    for code in codes:
        print(code)
    save_to_txt(codes)
