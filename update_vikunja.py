
import re
import json
import os

# Vikunja API configuration
VIKUNJA_API_URL = "http://localhost:3456/api/v1"
VIKUNJA_TOKEN = "tk_9e0971a67b4bf02e4e736bfa027372a0da7dfb08"

# Priority mapping
PRIORITY_MAPPING = {
    "Krytyczny": 3,
    "Wysoki": 2,
    "Średni": 1,
}

def get_all_tasks():
    """Fetches all tasks from the Vikunja API."""
    command = f'curl -X GET -H "Authorization: Bearer {VIKUNJA_TOKEN}" {VIKUNJA_API_URL}/tasks/all'
    tasks_json = os.popen(command).read()
    return json.loads(tasks_json)

def update_task(task_id, title, priority):
    """Updates a task in Vikunja."""
    # The title in the payload should not contain the priority keyword
    clean_title = re.sub(r"^\s*[(Krytyczny|Wysoki|Średni)]\s*", "", title).strip()
    
    payload = {
        "title": clean_title,
        "priority": priority,
    }
    
    # Properly escape the JSON payload for the curl command
    payload_str = json.dumps(payload)
    
    command = f'curl -X POST -H "Authorization: Bearer {VIKUNJA_TOKEN}" -H "Content-Type: application/json" -d \'{payload_str}\' {VIKUNJA_API_URL}/tasks/{task_id}'
    os.system(command)
    print(f"Updated task {task_id}: {clean_title} with priority {priority}")

def main():
    """Main function to update Vikunja tasks."""
    with open("target-version/STATUS.md", "r") as f:
        status_md = f.read()

    # Find the priorities section
    priorities_section_match = re.search(r"Priorytety:\s*\n((?:\s*\*\s*.*(?:\n|$))+)", status_md, re.DOTALL)
    if not priorities_section_match:
        print("Could not find the priorities section in STATUS.md")
        return

    priorities_text = priorities_section_match.group(1)

    # Find all list items in the priorities section
    priority_tasks = re.findall(r"^\s*\*\s*(.*?)$", priorities_text, re.MULTILINE)
", priorities_text, re.MULTILINE)

    if not priority_tasks:
        print("No priority tasks found in STATUS.md")
        return

    all_vikunja_tasks = get_all_tasks()

    for task_text in priority_tasks:
        match = re.match(r"^\s*[(Krytyczny|Wysoki|Średni)]?\s*:\s*(.*)", task_text)
        if not match:
            continue

        priority_keyword, title = match.groups()
        priority = PRIORITY_MAPPING.get(priority_keyword)

        if priority is None:
            continue

        # Find the corresponding task in Vikunja
        for vikunja_task in all_vikunja_tasks:
            # A simple title match should be enough for this script
            if title.strip().lower() in vikunja_task["title"].lower():
                update_task(vikunja_task["id"], vikunja_task["title"], priority)
                break

if __name__ == "__main__":
    main()
