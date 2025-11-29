import os
import json
from collections import Counter

BASE_PATH = "/content/ML4SWE-Group4"

def locate_reproduction_code(traj_id: str):
    """Find steps where the agent creates reproduction tests"""
    agent, sub = traj_id.split("@")
    traj_dir = os.path.join(BASE_PATH, agent, "trajs", sub)
    try:
        traj_files = [f for f in os.listdir(traj_dir) if f.endswith(".traj")]
        if not traj_files:
            return f"ERROR: no .traj file in {traj_dir}"
        path = os.path.join(traj_dir, traj_files[0])
        with open(path) as f:
            data = json.load(f)["trajectory"]
    except Exception as e:
        return f"ERROR: {e}"

    steps = []
    for i, step in enumerate(data):
        act = step.get("action", "").lower()
        thought = step.get("thought", "").lower()
        if ("create" in act and any(k in act for k in ["reproduce", "debug", "test"])) or "reproduc" in thought:
            steps.append(i)
    return steps


def locate_search(traj_id: str):
    """Find steps where the agent searches or navigates codebase"""
    agent, sub = traj_id.split("@")
    traj_dir = os.path.join(BASE_PATH, agent, "trajs", sub)
    try:
        traj_files = [f for f in os.listdir(traj_dir) if f.endswith(".traj")]
        if not traj_files:
            return f"ERROR: no .traj file in {traj_dir}"
        path = os.path.join(traj_dir, traj_files[0])
        with open(path) as f:
            data = json.load(f)["trajectory"]
    except Exception as e:
        return f"ERROR: {e}"

    steps = []
    search_terms = ["find", "grep", "cat", "ls", "cd", "search_file", "search_dir", "find_file"]
    for i, step in enumerate(data):
        act = step.get("action", "").lower()
        if any(cmd in act for cmd in search_terms):
            steps.append(i)
    return steps


def locate_tool_use(traj_id: str):
    """Count how many times each tool is called"""
    agent, sub = traj_id.split("@")
    traj_dir = os.path.join(BASE_PATH, agent, "trajs", sub)
    try:
        traj_files = [f for f in os.listdir(traj_dir) if f.endswith(".traj")]
        if not traj_files:
            return f"ERROR: no .traj file in {traj_dir}"
        path = os.path.join(traj_dir, traj_files[0])
        with open(path) as f:
            data = json.load(f)["trajectory"]
    except Exception as e:
        return f"ERROR: {e}"

    tools = Counter()
    for step in data:
        act = step.get("action", "")
        if act:
            first = act.split()[0]
            tools[first] += 1
    return dict(tools)


TRAJ_IDS = [
    "20250522_sweagent_claude-4-sonnet-20250514@sphinx-doc__sphinx-7985",
    "20250522_sweagent_claude-4-sonnet-20250514@sphinx-doc__sphinx-8548",
    "20250522_sweagent_claude-4-sonnet-20250514@matplotlib__matplotlib-23299",
    "20250522_sweagent_claude-4-sonnet-20250514@sphinx-doc__sphinx-8265",
    "20250522_sweagent_claude-4-sonnet-20250514@astropy__astropy-8707",
    "20250522_sweagent_claude-4-sonnet-20250514@django__django-11087",
    "20250522_sweagent_claude-4-sonnet-20250514@matplotlib__matplotlib-20676",
    "20250522_sweagent_claude-4-sonnet-20250514@sympy__sympy-15976",
    "20250522_sweagent_claude-4-sonnet-20250514@pytest-dev__pytest-5840",
    "20250522_sweagent_claude-4-sonnet-20250514@django__django-15280",
    "20250522_sweagent_claude-4-sonnet-20250514@django__django-14534",
    "20250522_sweagent_claude-4-sonnet-20250514@pytest-dev__pytest-10356",
    "20250522_sweagent_claude-4-sonnet-20250514@matplotlib__matplotlib-26208",
    "20250522_sweagent_claude-4-sonnet-20250514@matplotlib__matplotlib-25479",
    "20250522_sweagent_claude-4-sonnet-20250514@django__django-14011",
    "20250522_sweagent_claude-4-sonnet-20250514@django__django-16560",
    "20250522_sweagent_claude-4-sonnet-20250514@django__django-15695",
    "20250511_sweagent_lm_32b@scikit-learn__scikit-learn-25747",
    "20250511_sweagent_lm_32b@sympy__sympy-19783",
    "20250511_sweagent_lm_32b@matplotlib__matplotlib-22865",
]

def main():
    with open("/content/ML4SWE-Group4/task1_Sanya/locate_reproduction_code.log", "w") as log1, \
         open("/content/ML4SWE-Group4/task1_Sanya/locate_search.log", "w") as log2, \
         open("/content/ML4SWE-Group4/task1_Sanya/locate_tool_use.log", "w") as log3:

        for tid in TRAJ_IDS:
            rep = locate_reproduction_code(tid)
            sea = locate_search(tid)
            tools = locate_tool_use(tid)

            log1.write(f"{tid}: {rep}\n")
            log2.write(f"{tid}: {sea}\n")
            log3.write(f"{tid}: {tools}\n")

    print("Logs generated successfully")

if __name__ == "__main__":
    main()
