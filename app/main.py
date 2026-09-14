import os
import sys

# Thêm thư mục gốc GemmaTraining vào Python Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.gem import Gem

gem = Gem()

print()
print("===================================")
print("         TECHNICAL GEM")
print("          Gemma 4 E2B")
print("===================================")
print()
print("Gõ 'exit' để thoát.")
print()

while True:
    question = input("You: ").strip()

    if question.lower() == "exit":
        break

    if not question:
        continue

    print()
    print("Gemma:")

    answer = gem.ask(question)

    print(answer)
    print()