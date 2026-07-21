import sqlite3
import datetime
import json
import os

DB_PATH = "kuru_memory.db"

class KuruMemory:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # User facts & preferences (self-learning)
        cur.execute('''
        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            key TEXT UNIQUE,
            value TEXT,
            updated_at TIMESTAMP
        )''')

        # Interaction log (to learn habits from usage)
        cur.execute('''
        CREATE TABLE IF NOT EXISTS interaction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT,
            action_taken TEXT,
            success INTEGER,
            timestamp TIMESTAMP
        )''')

        # App shortcuts / habits learned
        cur.execute('''
        CREATE TABLE IF NOT EXISTS app_habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT UNIQUE,
            usage_count INTEGER DEFAULT 1,
            last_used TIMESTAMP
        )''')

        # Self-learning: Memorized multi-step workflows for autonomous execution
        cur.execute('''
        CREATE TABLE IF NOT EXISTS learned_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_trigger TEXT UNIQUE,
            target_app TEXT,
            action_steps TEXT,
            success_count INTEGER DEFAULT 1,
            last_used TIMESTAMP
        )''')

        conn.commit()
        conn.close()

    def save_fact(self, category, key, value):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cur.execute('''
        INSERT INTO user_facts (category, key, value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            category=excluded.category,
            value=excluded.value,
            updated_at=excluded.updated_at
        ''', (category, key, value, now))
        conn.commit()
        conn.close()
        print(f"[KURU Memory Learned]: {key} -> {value}")

    def get_all_facts(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT category, key, value FROM user_facts")
        rows = cur.fetchall()
        conn.close()
        return [{"category": r[0], "key": r[1], "value": r[2]} for r in rows]

    def save_workflow(self, task_trigger, target_app, action_steps):
        """Saves a successfully learned multi-step UI workflow."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        now = datetime.datetime.now().isoformat()
        steps_json = json.dumps(action_steps) if isinstance(action_steps, (list, dict)) else str(action_steps)
        cur.execute('''
        INSERT INTO learned_workflows (task_trigger, target_app, action_steps, success_count, last_used)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(task_trigger) DO UPDATE SET
            target_app=excluded.target_app,
            action_steps=excluded.action_steps,
            success_count=learned_workflows.success_count + 1,
            last_used=excluded.last_used
        ''', (task_trigger.lower().strip(), target_app, steps_json, now))
        conn.commit()
        conn.close()
        print(f"[KURU Learned Workflow]: '{task_trigger}' saved ({len(action_steps) if isinstance(action_steps, list) else 1} steps)!")

    def get_workflow(self, task_trigger):
        """Finds if a task has already been learned."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        task_norm = task_trigger.lower().strip()
        cur.execute("SELECT task_trigger, target_app, action_steps FROM learned_workflows WHERE task_trigger = ?", (task_norm,))
        row = cur.fetchone()
        if not row:
            # Fuzzy match: if any known trigger is contained in user query
            cur.execute("SELECT task_trigger, target_app, action_steps FROM learned_workflows")
            all_rows = cur.fetchall()
            for r in all_rows:
                if r[0] in task_norm or task_norm in r[0]:
                    row = r
                    break
        conn.close()
        if row:
            try:
                steps = json.loads(row[2])
            except Exception:
                steps = []
            return {"task_trigger": row[0], "target_app": row[1], "steps": steps}
        return None

    def log_interaction(self, command, action_taken, success=1):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cur.execute('''
        INSERT INTO interaction_logs (command, action_taken, success, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (command, json.dumps(action_taken) if isinstance(action_taken, (dict, list)) else str(action_taken), success, now))
        conn.commit()
        conn.close()

    def track_app_usage(self, app_name):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cur.execute('''
        INSERT INTO app_habits (app_name, usage_count, last_used)
        VALUES (?, 1, ?)
        ON CONFLICT(app_name) DO UPDATE SET
            usage_count = usage_count + 1,
            last_used = excluded.last_used
        ''', (app_name.lower(), now))
        conn.commit()
        conn.close()

    def get_context_for_prompt(self):
        facts = self.get_all_facts()
        summary = ["User habits & remembered facts:"]
        if facts:
            for f in facts:
                summary.append(f"- [{f['category'].upper()}] {f['key']}: {f['value']}")
        else:
            summary.append("- No basic profile facts stored yet.")

        # Add list of learned workflows
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT task_trigger, target_app FROM learned_workflows")
        workflows = cur.fetchall()
        conn.close()
        if workflows:
            summary.append("\nLearned Autonomous Phone Workflows:")
            for w in workflows:
                summary.append(f"- Task: '{w[0]}' (App: {w[1]})")

        return "\n".join(summary)
