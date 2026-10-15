#!/usr/bin/env python3
"""
POC Participant Randomization Script
Ensures balanced assignment of tasks and tools
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

def randomize_participants(participant_names: List[str]) -> List[Dict]:
    """
    Randomize participant assignments ensuring:
    1. Each participant does 2 different tasks
    2. Each participant uses both tool types
    3. Balanced distribution across conditions
    """
    
    # Define all possible task combinations
    task_combinations = [
        ('A: Onboarding', 'B: Refactoring'),
        ('B: Refactoring', 'C: Spike'),
        ('C: Spike', 'A: Onboarding'),
        ('A: Onboarding', 'C: Spike'),
        ('B: Refactoring', 'A: Onboarding'),
        ('C: Spike', 'B: Refactoring')
    ]
    
    # Ensure we have enough combinations
    if len(participant_names) > len(task_combinations):
        # Duplicate combinations if more participants than combinations
        task_combinations = task_combinations * (len(participant_names) // len(task_combinations) + 1)
    
    # Randomize task combinations
    random.shuffle(task_combinations)
    
    # Assign tools (alternating to ensure balance)
    tool_assignments = []
    for i in range(len(participant_names)):
        if i % 2 == 0:
            tools = ('Vibe Coding', 'Assisted Coding')
        else:
            tools = ('Assisted Coding', 'Vibe Coding')
        tool_assignments.append(tools)
    
    # Randomize tool order
    random.shuffle(tool_assignments)
    
    # Create participant assignments
    assignments = []
    for i, name in enumerate(participant_names):
        participant = {
            'id': f'P{i+1:03d}',
            'name': name,
            'task_1': task_combinations[i][0],
            'tool_1': tool_assignments[i][0],
            'task_2': task_combinations[i][1],
            'tool_2': tool_assignments[i][1],
            'randomization_date': datetime.now().isoformat()
        }
        assignments.append(participant)
    
    return assignments

def generate_schedule(assignments: List[Dict], start_date: datetime) -> List[Dict]:
    """
    Generate a schedule for task completion
    Spreads tasks across the week to avoid conflicts
    """
    
    scheduled_assignments = []
    current_date = start_date
    
    for i, participant in enumerate(assignments):
        # Assign dates based on participant number
        # Half do task 1 on Monday/Tuesday, half on Wednesday/Thursday
        if i < len(assignments) // 2:
            task_1_date = start_date + timedelta(days=i % 2)
            task_2_date = start_date + timedelta(days=3 + (i % 2))
        else:
            task_1_date = start_date + timedelta(days=2 + (i % 2))
            task_2_date = start_date + timedelta(days=4 + (i % 2))
        
        participant['task_1_date'] = task_1_date.strftime('%Y-%m-%d')
        participant['task_2_date'] = task_2_date.strftime('%Y-%m-%d')
        scheduled_assignments.append(participant)
    
    return scheduled_assignments

def validate_randomization(assignments: List[Dict]) -> bool:
    """
    Validate that randomization meets all criteria
    """
    
    # Check each participant has different tasks
    for participant in assignments:
        if participant['task_1'] == participant['task_2']:
            print(f"Error: {participant['name']} has same task twice")
            return False
    
    # Check each participant uses both tool types
    for participant in assignments:
        if participant['tool_1'] == participant['tool_2']:
            print(f"Error: {participant['name']} uses same tool twice")
            return False
    
    # Check balance across conditions
    task_counts = {}
    tool_counts = {}
    
    for participant in assignments:
        for task, tool in [(participant['task_1'], participant['tool_1']), 
                          (participant['task_2'], participant['tool_2'])]:
            key = f"{task}_{tool}"
            task_counts[task] = task_counts.get(task, 0) + 1
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
    
    print("\nTask distribution:")
    for task, count in sorted(task_counts.items()):
        print(f"  {task}: {count}")
    
    print("\nTool distribution:")
    for tool, count in sorted(tool_counts.items()):
        print(f"  {tool}: {count}")
    
    return True

def export_to_markdown(assignments: List[Dict]) -> str:
    """
    Export assignments to markdown table format
    """
    
    markdown = """# Randomized Participant Assignments

Generated: {}

| ID | Name | Task 1 | Tool 1 | Date 1 | Task 2 | Tool 2 | Date 2 |
|----|------|--------|--------|--------|--------|--------|--------|
""".format(datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    for p in assignments:
        markdown += f"| {p['id']} | {p['name']} | {p['task_1']} | {p['tool_1']} | {p['task_1_date']} | {p['task_2']} | {p['tool_2']} | {p['task_2_date']} |\n"
    
    return markdown

def main():
    """
    Main randomization workflow
    """
    
    print("POC Participant Randomization Tool")
    print("=" * 40)
    
    # Get participant names
    print("\nEnter participant names (one per line, empty line to finish):")
    participants = []
    while True:
        name = input().strip()
        if not name:
            break
        participants.append(name)
    
    if len(participants) < 4:
        print("Warning: POC works best with 6-8 participants")
        print(f"You have {len(participants)} participants")
    
    # Get start date
    start_date_str = input("\nEnter POC start date (YYYY-MM-DD): ").strip()
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    except:
        print("Invalid date, using next Monday")
        today = datetime.now()
        days_ahead = 0 - today.weekday()  # Monday is 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        start_date = today + timedelta(days=days_ahead)
    
    # Perform randomization
    print("\nRandomizing assignments...")
    assignments = randomize_participants(participants)
    assignments = generate_schedule(assignments, start_date)
    
    # Validate
    if validate_randomization(assignments):
        print("\n✅ Randomization valid!")
    else:
        print("\n❌ Randomization failed validation")
        return
    
    # Export results
    print("\nExporting results...")
    
    # JSON export
    with open('participant_assignments.json', 'w') as f:
        json.dump(assignments, f, indent=2)
    print("  Saved to participant_assignments.json")
    
    # Markdown export
    markdown = export_to_markdown(assignments)
    with open('participant_assignments.md', 'w') as f:
        f.write(markdown)
    print("  Saved to participant_assignments.md")
    
    # Display summary
    print("\n" + "=" * 40)
    print("ASSIGNMENT SUMMARY")
    print("=" * 40)
    for p in assignments:
        print(f"\n{p['name']} ({p['id']}):")
        print(f"  {p['task_1_date']}: {p['task_1']} with {p['tool_1']}")
        print(f"  {p['task_2_date']}: {p['task_2']} with {p['tool_2']}")

if __name__ == "__main__":
    main()