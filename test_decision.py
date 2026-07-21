from kuru.brain import KuruBrain
import time

print("Starting test...")
t0 = time.time()
brain = KuruBrain()
print(f"Brain init time: {time.time() - t0:.2f}s")

t1 = time.time()
brain.process_command("aaj ka mausam kaisa hai")
print(f"Command process time: {time.time() - t1:.2f}s")
