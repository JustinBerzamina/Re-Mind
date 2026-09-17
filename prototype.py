tasks = []
next_id = 1

while True:
    print("\n=== Re:Mind Task Manager ===")
    print("1. View Tasks")
    print("2. Add Task")
    print("3. Delete Task")
    print("4. Exit")

    choice = input("\nSelect option: ").strip()

    if choice == "1":
        if len(tasks) == 0:
            print("No tasks found.")
        else:
            sorted_tasks = sorted(tasks, key=lambda x: x["priority"], reverse=True)
            print("\nID   Priority   Deadline        Title")
            print("-" * 45)
            for t in sorted_tasks:
                if t["priority"] == 3:
                    p_name = "URGENT"
                elif t["priority"] == 2:
                    p_name = "MEDIUM"
                else:
                    p_name = "LOW"
                print(f"{t['id']:<4} {p_name:<10} {t['deadline']:<15} {t['title']}")

    elif choice == "2":
        title = input("Title: ").strip()
        while title == "":
            print("Title cannot be empty.")
            title = input("Title: ").strip()

        p_input = input("Priority (1=Low, 2=Med, 3=Urgent): ").strip()
        if p_input in ["1", "2", "3"]:
            priority = int(p_input)
        else:
            priority = 1

        deadline = input("Deadline (optional): ").strip()
        if deadline == "":
            deadline = "None"

        task = {
            "id": next_id,
            "title": title,
            "priority": priority,
            "deadline": deadline
        }
        tasks.append(task)
        print(f"Task #{next_id} added.")
        next_id = next_id + 1

    elif choice == "3":
        if len(tasks) == 0:
            print("No tasks to delete.")
        else:
            del_id = input("Enter Task ID to delete: ").strip()
            if not del_id.isdigit():
                print("Invalid input. Must be a number.")
            else:
                target = int(del_id)
                found = False
                for i in range(len(tasks)):
                    if tasks[i]["id"] == target:
                        tasks.pop(i)
                        print(f"Task #{target} deleted.")
                        found = True
                        break
                if not found:
                    print("Task not found.")

    elif choice == "4":
        print("Goodbye!")
        break

    else:
        print("Invalid choice.")