import os
root = "/home/changshu/experiments/evaluation/verified/20250511_sweagent_lm_32b/trajs"
for d in os.listdir(root):
    problem_id = d.split(".")[0]
    new_folder = f"{root}/{problem_id}"
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)
    os.system(f"mv {root}/{d} {new_folder}/{d}")