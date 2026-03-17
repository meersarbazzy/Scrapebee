path = "c:/Project-DQ/Validata/Scrapper/debug_strat0_v2.txt"
found = False
try:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "DEBUG Strat 0" in line:
                print(line.strip())
                found = True
except Exception as e:
    print(f"Error: {e}")

if not found:
    print("No debug panel logs found.")
