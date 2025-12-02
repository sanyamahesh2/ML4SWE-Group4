# Mavericks Additions / refactoring
import os
import json
from collections import Counter

BASE_PATH = "/content/ML4SWE-Group4"


def _load_trajectory(traj_id: str):
    """
    Helper to load a single .traj file for a given trajectory id.
    Returns the list of steps (the "trajectory" field).
    """

    # Each traj_id has the format:
    #   "<agent_name>@<repo_issue>"
    agent, sub = traj_id.split("@", 1)

    # Construct the path where the .traj file live.
    traj_dir = os.path.join(BASE_PATH, agent, "trajs", sub)

    # Find all files ending in ".traj" inside that directory.
    traj_files = [f for f in os.listdir(traj_dir) if f.endswith(".traj")]

    if not traj_files:
        raise FileNotFoundError(f"No .traj file found in {traj_dir}")

    # There should only be one .traj per directory; take the first.
    path = os.path.join(traj_dir, traj_files[0])
    with open(path, "r") as f:
        data = json.load(f)

    if "trajectory" not in data:
        raise KeyError(f'"trajectory" key not found in {path}')
    return data["trajectory"]

def locate_reproduction_code(traj_id: str):
    """
    Find steps where the agent *creates* a reproduction / debug test.

    Heuristics:
    - Look for file-creation style actions (create / write / touch) where
      the filename contains keywords like "repro", "reproduce", "reproduction",
      "debug", or "test".
    """
    try:
        trajectory = _load_trajectory(traj_id)
    except Exception as e:
        return f"ERROR: {e}"

    # store the step indices we detect as reproduction-test creation
    repro_steps = []

    # Words that indicate the model is creating/writing a file
    creation_keywords = {"create", "write", "touch"}

    # Filename patterns that strongly signal a reproduction test
    filename_keywords = {"repro", "reproduce", "reproduction", "debug", "test"}

    # Loop over each step and its index
    for i, step in enumerate(trajectory):
        # Normalize fields to lowercase strings (avoid None)
        action = (step.get("action") or "").lower()
        thought = (step.get("thought") or "").lower()

        if not action:
            continue

        tokens = action.split()
        if not tokens:
            continue

        # Identify if this step contains a "create-like" command
        create_idx = None
        for idx, tok in enumerate(tokens):
            if tok in creation_keywords:
                create_idx = idx
                break

        if create_idx is None:
            # Not obviously creating a file; skip
            continue

        # Extract the filename that follows the creation verb
        filename = ""
        if create_idx + 1 < len(tokens):
            filename = tokens[create_idx + 1]

        # Filename-based heuristic for reproduction tests
        # If the filename contains any of our reproduction keywords,
        # this step definitely counts as a reproduction creation step.
        if any(kw in filename for kw in filename_keywords):
            repro_steps.append(i)
            continue

        # Thought-based heuristic
        # Even if the filename didn't match, sometimes the model's thought text
        # explicitly says something like "create a minimal reproduction script".
        thought_keywords = [
            "reproduction script",
            "reproduce the issue",
            "repro script",
            "reproduction test",
            "minimal repro",
            "debug script",
        ]

        # If any thought keyword matches, classify this step as reproduction creation.
        # We only allow thought-based detection *after* confirming this was a create-step
        # to avoid matching irrelevant thoughts elsewhere.
        if any(kw in thought for kw in thought_keywords):
            repro_steps.append(i)

    # Sort + deduplicate results before returning
    return [i + 1 for i in sorted(set(repro_steps))]


def locate_search(traj_id: str):
    """
    Find steps where the model searches or navigates inside the codebase.

    Heuristics:
    - SWE-Agent search tools: find_file, search_file, search_dir.
    - Shell search/navigation commands: grep, find, rg, ag, fd
    - The integrated editor "view" actions (e.g., 'str_replace_editor view ...')
      also count as navigation/search through the repo.
    """
    try:
        trajectory = _load_trajectory(traj_id)
    except Exception as e:
        return f"ERROR: {e}"

    search_steps = []

    swe_search_tools = {"find_file", "search_file", "search_dir", "view"}
    shell_search_cmds = {"grep", "find", "rg", "ag", "fd"}

    for i, step in enumerate(trajectory):
        action = (step.get("action") or "").lower()
        if not action:
            continue

        tokens = action.split()
        if not tokens:
            continue

        # First token is usually the tool or shell command
        first = tokens[0]

        is_search = False

        # Case 1: Dedicated SWE search tools as the first token
        if first in swe_search_tools:
            is_search = True

        # Case 2: Editor wrapper + "view" subcommand
        # Example: "str_replace_editor view /testbed/astropy/io/fits/header.py"
        if first == "str_replace_editor" and len(tokens) > 1 and tokens[1] == "view":
            is_search = True

        # Case 3: Shell search/navigation commands
        # ("grep", "find", etc.)
        if first in shell_search_cmds:
            is_search = True

        # Case 4: Compound shell commands like "grep ... && python ...".
        # We treat 'grep', 'find', etc. as navigation/search.
        if "&&" in tokens:
            parts = action.split("&&")
            for part in parts:
                part_tokens = part.strip().split()
                if not part_tokens:
                    continue
                cmd = part_tokens[0]
                if cmd in shell_search_cmds:
                    is_search = True
                    break

        if is_search:
            search_steps.append(i)

    return [i + 1 for i in sorted(set(search_steps))]


def locate_tool_use(traj_id: str):
    """
    Count how many times each tool/command is called.

    Heuristics:
    - For simple commands (e.g., 'grep -n ...'), count the first word ('grep').
    - For SWE editor actions (e.g., 'str_replace_editor view ...'),
      record both the high-level tool and the subcommand:
        - 'str_replace_editor'
        - 'str_replace_editor:view'
    - For compound shell commands joined with '&&', count each segment
      separately (e.g., 'cd', 'python').
    """
    try:
        trajectory = _load_trajectory(traj_id)
    except Exception as e:
        return {"ERROR": str(e)}

    tools = Counter()

    for step in trajectory:
        action = (step.get("action") or "").strip()
        if not action:
            continue

        # Split on '&&' to handle multiple commands in one action
        segments = [seg.strip() for seg in action.split("&&") if seg.strip()]

        for seg in segments:
            tokens = seg.split()
            if not tokens:
                continue

            first = tokens[0]

            # SWE editor wrapper: record both the wrapper and its subcommand
            if first == "str_replace_editor" and len(tokens) > 1:
                subcmd = tokens[1]
                tools[first] += 1
                tools[f"{first}:{subcmd}"] += 1
            else:
                tools[first] += 1

    # Convert Counter to a plain dict for JSON/log friendliness
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
    # Adjust paths here if needed; logs are expected under /content/task1/
    out_dir = os.path.join(BASE_PATH, "task1_Maverick")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "locate_reproduction_code_Maverick.log"), "w") as log1, \
         open(os.path.join(out_dir, "locate_search_Maverick.log"), "w") as log2, \
         open(os.path.join(out_dir, "locate_tool_use_Maverick.log"), "w") as log3:

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
