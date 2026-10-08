# ---------------------------------------------------------
# Employee Attendance and Leave Manager - BrightPath Solutions
# ---------------------------------------------------------
from datetime import datetime, timedelta
from collections import defaultdict

DATE_FORMAT = "%d-%m-%Y"          # one fixed date format everywhere (dd-mm-yyyy)
HOLIDAYS = {"02-10-2026"}         # a set of company holidays
ATTENDANCE_FILE = "attendance.txt"
EMPLOYEES_FILE = "employees.txt"
LEAVES_FILE = "leaves.txt"

# Employee data: a dictionary of dictionaries
employees = {
    "E01": {"name": "Anand R",   "dept": "Development", "CL": 8, "SL": 6},
    "E02": {"name": "Bhavani K", "dept": "Development", "CL": 8, "SL": 6},
    "E03": {"name": "Charles D", "dept": "Testing",     "CL": 8, "SL": 6},
    "E04": {"name": "Deepa S",   "dept": "Testing",     "CL": 8, "SL": 6},
    "E05": {"name": "Imran A",   "dept": "HR",          "CL": 8, "SL": 6},
    "E06": {"name": "Janani P",  "dept": "Finance",     "CL": 8, "SL": 6},
}

# Attendance: date -> {employee id: status}
# Example: "01-10-2026" -> {"E01": "P", "E02": "WFH"}
attendance = defaultdict(dict)
# Approved leave: date -> {employee id: "CL" or "SL"}
leaves = defaultdict(dict)


def read_date(prompt):
    """Keep asking until the user types a real date in dd-mm-yyyy format."""
    while True:
        text = input(prompt).strip()
        try:
            date_obj = datetime.strptime(text, DATE_FORMAT)
            return date_obj.strftime(DATE_FORMAT)   # e.g. "1-10-2026" becomes "01-10-2026"
        except ValueError:
            print("  Invalid date. Please use dd-mm-yyyy (example: 01-10-2026).")


def is_working_day(date_text):
    """True if the date is Monday to Friday and not a company holiday."""
    date_obj = datetime.strptime(date_text, DATE_FORMAT)
    return date_obj.weekday() < 5 and date_text not in HOLIDAYS


def working_days_between(start, end):
    """Return (working_days, skipped) between two dates, both included.
    skipped is a list of (date, reason) like ('03-10-2026', 'Saturday')."""
    working_days = []
    skipped = []
    current = datetime.strptime(start, DATE_FORMAT)
    last = datetime.strptime(end, DATE_FORMAT)

    while current <= last:
        day_text = current.strftime(DATE_FORMAT)
        if day_text in HOLIDAYS:
            skipped.append((day_text, "holiday"))
        elif current.weekday() >= 5:
            skipped.append((day_text, current.strftime("%A")))   # Saturday or Sunday
        else:
            working_days.append(day_text)
        current += timedelta(days=1)      # move to the next day

    return working_days, skipped


def view_employees():
    """Option 1: show ID, name, department and remaining CL and SL for everyone."""
    print("\n" + "-" * 62)
    print(f"{'ID':<6}{'Name':<14}{'Department':<14}{'CL left':>8}{'SL left':>8}")
    print("-" * 62)
    for emp_id, info in employees.items():
        print(f"{emp_id:<6}{info['name']:<14}{info['dept']:<14}{info['CL']:>8}{info['SL']:>8}")
    print("-" * 62)

def get_day_problem(date_text):
    """Return the reason a date is not a working day, or None if it is a working day."""
    if date_text in HOLIDAYS:
        return "a company holiday"
    day_obj = datetime.strptime(date_text, DATE_FORMAT)
    if day_obj.weekday() >= 5:                      # 5 = Saturday, 6 = Sunday
        return "a " + day_obj.strftime("%A")
    return None


def mark_attendance():
    """Option 2: mark P / WFH / A for every employee on one working day."""
    # Step 1: keep asking until the date is a valid working day
    while True:
        date_text = read_date("Date (dd-mm-yyyy) : ")
        problem = get_day_problem(date_text)
        if problem:
            print(f"  {date_text} is {problem}. Please enter a working day.")
        else:
            break

    # Step 2: no double marking
    if attendance.get(date_text):
        print(f"  Attendance for {date_text} is already marked. It cannot be marked again.")
        return

    # Step 3: ask for each employee (skip anyone on approved leave)
    on_leave_today = leaves.get(date_text, {})
    todays = {}
    print()
    for emp_id, info in employees.items():
        if emp_id in on_leave_today:
            leave_type = on_leave_today[emp_id]
            todays[emp_id] = leave_type
            print(f"{emp_id} {info['name']:<10}: on leave ({leave_type}) - marked automatically")
        else:
            while True:
                status = input(f"{emp_id} {info['name']:<10} (P/WFH/A) : ").strip().upper()
                if status in ("P", "WFH", "A"):
                    break
                print("  Please type only P, WFH or A.")
            todays[emp_id] = status

    # Step 4: save the day and show a summary
    attendance[date_text] = todays
    statuses = list(todays.values())
    print(f"\nSaved {date_text} -> Present {statuses.count('P')} | WFH {statuses.count('WFH')} "
          f"| Absent {statuses.count('A')} | Leave {statuses.count('CL') + statuses.count('SL')}")

def apply_leave():
    """Option 3: apply CL/SL for a date range, check rules, then approve."""
    # Step 1: read and validate the inputs
    emp_id = input("Employee ID      : ").strip().upper()
    if emp_id not in employees:
        print("  Employee ID not found.")
        return

    leave_type = input("Leave type CL/SL : ").strip().upper()
    if leave_type not in ("CL", "SL"):
        print("  Leave type must be CL or SL.")
        return

    start = read_date("From date        : ")
    end = read_date("To date          : ")
    if datetime.strptime(end, DATE_FORMAT) < datetime.strptime(start, DATE_FORMAT):
        print("  To date cannot be before From date.")
        return

    # Step 2: count only working days
    leave_days, skipped = working_days_between(start, end)
    if skipped:
        text = ", ".join(f"{d} ({reason})" for d, reason in skipped)
        print(f"\nSkipping {text}")
    if not leave_days:
        print("  No working days in this range, so no leave is needed.")
        return
    print(f"Working days of leave : {len(leave_days)}  ({', '.join(leave_days)})")

    # Step 3: no overlap with marked attendance or existing leave
    for day in leave_days:
        if attendance.get(day):
            print(f"  Rejected: {day} is already marked.")
            return
        if emp_id in leaves.get(day, {}):
            print(f"  Rejected: {employees[emp_id]['name']} is already on leave on {day}.")
            return

    # Step 4: check the balance
    balance = employees[emp_id][leave_type]
    if balance < len(leave_days):
        print(f"  Rejected: {employees[emp_id]['name']} needs {len(leave_days)} day(s) "
              f"but has only {balance} {leave_type} left.")
        return

    # Step 5: approve, store the leave, reduce the balance
    for day in leave_days:
        leaves[day][emp_id] = leave_type
    employees[emp_id][leave_type] = balance - len(leave_days)
    print(f"Leave approved for {employees[emp_id]['name']}. "
          f"{leave_type} balance: {balance} -> {employees[emp_id][leave_type]}")

def names(emp_ids):
    """Turn a set of employee IDs into readable text like 'E01 Anand R, E04 Deepa S'."""
    return ", ".join(f"{e} {employees[e]['name']}" for e in sorted(emp_ids)) or "-"


def view_day():
    """Option 4: for one date, show who was present, on WFH, absent and on leave."""
    date_text = read_date("Date (dd-mm-yyyy) : ")
    day = attendance.get(date_text)
    if not day:
        print(f"  No attendance has been marked for {date_text}.")
        return

    # Sets: each one holds the employee IDs with that status
    present = {e for e, s in day.items() if s == "P"}
    wfh = {e for e, s in day.items() if s == "WFH"}
    absent = {e for e, s in day.items() if s == "A"}
    on_leave = {e for e, s in day.items() if s in ("CL", "SL")}

    day_name = datetime.strptime(date_text, DATE_FORMAT).strftime("%A")
    print(f"\n------ {date_text} ({day_name}) ------")
    print(f"Present  : {names(present)}")
    print(f"WFH      : {names(wfh)}")
    print(f"Absent   : {names(absent)}")
    print(f"On leave : {names(on_leave)}")


def read_month(prompt):
    """Keep asking until the user types a real month in mm-yyyy format."""
    while True:
        text = input(prompt).strip()
        try:
            month_obj = datetime.strptime(text, "%m-%Y")
            return month_obj.year, month_obj.month
        except ValueError:
            print("  Invalid month. Please use mm-yyyy (example: 10-2026).")


def working_days_in_month(year, month):
    """Return a list of all working days (Mon-Fri, not holidays) in a month."""
    days = []
    current = datetime(year, month, 1)
    while current.month == month:               # stop when the next month starts
        day_text = current.strftime(DATE_FORMAT)
        if is_working_day(day_text):
            days.append(day_text)
        current += timedelta(days=1)
    return days


def month_stats(emp_id, year, month):
    """Count present, WFH, absent, leave days and attendance % for one employee."""
    days = working_days_in_month(year, month)
    counts = {"P": 0, "WFH": 0, "A": 0, "Leave": 0, "Unmarked": 0}

    for day in days:
        if emp_id in leaves.get(day, {}):       # approved leave counts as leave
            counts["Leave"] += 1
        else:
            status = attendance.get(day, {}).get(emp_id)
            if status is None:
                counts["Unmarked"] += 1         # this day has not been marked yet
            else:
                counts[status] += 1

    # Formula from the brief: (P + WFH) / (working days - leave days) x 100
    usable_days = len(days) - counts["Leave"]
    if usable_days > 0:
        percent = round((counts["P"] + counts["WFH"]) / usable_days * 100, 2)
    else:
        percent = 0.0

    counts["Working days"] = len(days)
    counts["Percent"] = percent
    return counts


def employee_summary():
    """Option 5: monthly summary for one employee."""
    emp_id = input("Employee ID : ").strip().upper()
    if emp_id not in employees:
        print("  Employee ID not found.")
        return
    year, month = read_month("Month (mm-yyyy) : ")

    stats = month_stats(emp_id, year, month)
    title = datetime(year, month, 1).strftime("%B %Y").upper()
    print(f"\n------ {title} : {employees[emp_id]['name']} ({emp_id}) ------")
    print(f"Working days   : {stats['Working days']}")
    print(f"Present        : {stats['P']}")
    print(f"Work from home : {stats['WFH']}")
    print(f"Absent         : {stats['A']}")
    print(f"Leave          : {stats['Leave']}")
    if stats["Unmarked"] > 0:
        print(f"Not marked yet : {stats['Unmarked']}")
    print(f"Attendance     : {stats['Percent']:.2f}%")
    print("-" * 44)

def team_report():
    """Option 6: attendance % of all employees for a month, highest first."""
    year, month = read_month("Month (mm-yyyy) : ")

    # Get the statistics for every employee (dictionary comprehension)
    stats = {emp_id: month_stats(emp_id, year, month) for emp_id in employees}
    pct = {emp_id: s["Percent"] for emp_id, s in stats.items()}

    # Sort employee IDs by attendance %, highest first
    ranked = sorted(employees, key=lambda e: pct[e], reverse=True)

    title = datetime(year, month, 1).strftime("%B %Y").upper()
    print(f"\n------ TEAM REPORT : {title} ------")
    print(f"{'Rank':<6}{'ID':<6}{'Name':<12}{'Present':>8}{'WFH':>6}{'Absent':>8}"
          f"{'Leave':>7}{'Attendance':>12}  Flag")
    print("-" * 74)
    for rank, emp_id in enumerate(ranked, start=1):
        s = stats[emp_id]
        flag = "LOW (<75%)" if pct[emp_id] < 75 else ""
        print(f"{rank:<6}{emp_id:<6}{employees[emp_id]['name']:<12}{s['P']:>8}{s['WFH']:>6}"
              f"{s['A']:>8}{s['Leave']:>7}{pct[emp_id]:>11.2f}%  {flag}")
    print("-" * 74)



def save_all():
    """Save every marked day to attendance.txt and every balance to employees.txt."""
    with open(ATTENDANCE_FILE, "w") as f:
        for date_text in sorted(attendance, key=lambda d: datetime.strptime(d, DATE_FORMAT)):
            for emp_id, status in attendance[date_text].items():
                f.write(f"{date_text},{emp_id},{status}\n")

    with open(EMPLOYEES_FILE, "w") as f:
        for emp_id, info in employees.items():
            f.write(f"{emp_id},{info['name']},{info['dept']},{info['CL']},{info['SL']}\n")

    with open(LEAVES_FILE, "w") as f:
        for date_text in sorted(leaves, key=lambda d: datetime.strptime(d, DATE_FORMAT)):
            for emp_id, leave_type in leaves[date_text].items():
                f.write(f"{date_text},{emp_id},{leave_type}\n")

    print("Data saved to attendance.txt, employees.txt and leaves.txt.")


def load_all():
    """Load attendance.txt and employees.txt when the program starts, if they exist."""
    try:
        with open(ATTENDANCE_FILE, "r") as f:
            for line in f:
                date_text, emp_id, status = line.strip().split(",")
                attendance[date_text][emp_id] = status
    except FileNotFoundError:
        pass   # first run - no file yet, that's fine

    try:
        with open(EMPLOYEES_FILE, "r") as f:
            for line in f:
                emp_id, name, dept, cl, sl = line.strip().split(",")
                employees[emp_id] = {"name": name, "dept": dept, "CL": int(cl), "SL": int(sl)}
    except FileNotFoundError:
        pass

    try:
        with open(LEAVES_FILE, "r") as f:
            for line in f:
                date_text, emp_id, leave_type = line.strip().split(",")
                leaves[date_text][emp_id] = leave_type
    except FileNotFoundError:
        pass

def show_menu():
    """Print the main menu."""
    print("\n===== BrightPath Attendance and Leave Manager =====")
    print("1. View employees")
    print("2. Mark attendance")
    print("3. Apply leave")
    print("4. View a day")
    print("5. Employee summary")
    print("6. Team report")
    print("7. Save / Load")
    print("8. Exit")


def main():
    """Keep showing the menu until the user chooses Exit."""
    while True:
        show_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            view_employees()
        elif choice == "2":
            mark_attendance()
        elif choice == "3":
            apply_leave()
        elif choice == "4":
            view_day()
        elif choice == "5":
            employee_summary()
        elif choice == "6":
            team_report()
        elif choice == "7":
            save_all()
        elif choice == "8":
            save_all()
            print("Goodbye! Data saved.")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 8.")


if __name__ == "__main__":
    load_all()
    main()
