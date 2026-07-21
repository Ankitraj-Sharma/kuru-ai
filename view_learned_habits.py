import sqlite3
import os
import sys
import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def display_report():
    print("="*65)
    print(" [*] KURU AI - SILENT LEARNING & OBSERVED HABITS REPORT")
    print("="*65)

    conn = sqlite3.connect("kuru_memory.db")
    cur = conn.cursor()

    # 1. User Profile & Learned Facts
    print("\n[1] LEARNED USER FACTS & PREFERENCES:")
    cur.execute("SELECT category, key, value, updated_at FROM user_facts ORDER BY category")
    facts = cur.fetchall()
    if facts:
        for f in facts:
            print(f"  • [{f[0].upper()}] {f[1]}: {f[2]} (Updated: {f[3][:16]})")
    else:
        print("  (No facts recorded yet)")

    # 2. App Usage Habits (Sorted by frequency)
    print("\n[2] DAILY APP USAGE HABITS (Frequency of Use):")
    cur.execute("SELECT app_name, usage_count, last_used FROM app_habits ORDER BY usage_count DESC LIMIT 10")
    apps = cur.fetchall()
    if apps:
        for a in apps:
            print(f"  • {a[0]}: used {a[1]} times (Last: {a[2][:16] if a[2] else 'recent'})")
    else:
        print("  (No app habits recorded yet)")

    # 3. Memorized Autonomous Workflows
    print("\n[3] AUTONOMOUS WORKFLOWS (Tasks KURU knows how to do):")
    cur.execute("SELECT task_trigger, target_app, success_count, last_used FROM learned_workflows")
    workflows = cur.fetchall()
    if workflows:
        for w in workflows:
            print(f"  • Task: '{w[0]}' | Target App: {w[1]} (Successes: {w[2]})")
    else:
        print("  (No workflows recorded yet)")

    conn.close()

    # 4. Recent Monitor Log
    if os.path.exists("shadow_monitor.log"):
        print("\n[4] RECENT OBSERVATION LOG (Last 5 events):")
        try:
            with open("shadow_monitor.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
                for l in lines[-5:]:
                    print("  " + l.strip())
        except Exception:
            pass

    print("\n" + "="*65)

if __name__ == "__main__":
    display_report()
