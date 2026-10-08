import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(page_title="BrightPath Attendance Manager", layout="wide")

DATE_FORMAT = "%d-%m-%Y"
HOLIDAYS = {"02-10-2026"}

ATTENDANCE_FILE = "attendance.txt"
EMPLOYEES_FILE = "employees.txt"
LEAVES_FILE = "leaves.txt"


def load_employees():
    """Load employees.txt, or start with default balances if it doesn't exist."""
    employees = {
        "E01": {"name": "Anand R",   "dept": "Development", "CL": 8, "SL": 6},
        "E02": {"name": "Bhavani K", "dept": "Development", "CL": 8, "SL": 6},
        "E03": {"name": "Charles D", "dept": "Testing",     "CL": 8, "SL": 6},
        "E04": {"name": "Deepa S",   "dept": "Testing",     "CL": 8, "SL": 6},
        "E05": {"name": "Imran A",   "dept": "HR",          "CL": 8, "SL": 6},
        "E06": {"name": "Janani P",  "dept": "Finance",     "CL": 8, "SL": 6},
    }
    try:
        with open(EMPLOYEES_FILE, "r") as f:
            for line in f:
                emp_id, name, dept, cl, sl = line.strip().split(",")
                employees[emp_id] = {"name": name, "dept": dept, "CL": int(cl), "SL": int(sl)}
    except FileNotFoundError:
        pass
    return employees


def load_attendance():
    attendance = defaultdict(dict)
    try:
        with open(ATTENDANCE_FILE, "r") as f:
            for line in f:
                date_text, emp_id, status = line.strip().split(",")
                attendance[date_text][emp_id] = status
    except FileNotFoundError:
        pass
    return attendance


def load_leaves():
    leaves = defaultdict(dict)
    try:
        with open(LEAVES_FILE, "r") as f:
            for line in f:
                date_text, emp_id, leave_type = line.strip().split(",")
                leaves[date_text][emp_id] = leave_type
    except FileNotFoundError:
        pass
    return leaves

def save_all():
    """Save every marked day, balance, and leave to the .txt files."""
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


# ---- Load data once per session, keep it in Streamlit's session_state ----
if "employees" not in st.session_state:
    st.session_state.employees = load_employees()
if "attendance" not in st.session_state:
    st.session_state.attendance = load_attendance()
if "leaves" not in st.session_state:
    st.session_state.leaves = load_leaves()

employees = st.session_state.employees
attendance = st.session_state.attendance
leaves = st.session_state.leaves

def get_month_stats(emp_id, month, year):
    """Count one employee's statuses for a month and return the numbers and attendance %."""
    # Collect every working day (Mon-Fri, not a holiday) in the month
    working_days = []
    current = datetime(year, month, 1)
    while current.month == month:
        day_text = current.strftime(DATE_FORMAT)
        if current.weekday() < 5 and day_text not in HOLIDAYS:
            working_days.append(day_text)
        current += timedelta(days=1)

    present = wfh = absent = leave = not_marked = 0
    for d in working_days:
        status = attendance.get(d, {}).get(emp_id) or leaves.get(d, {}).get(emp_id)
        if status == "P":
            present += 1
        elif status == "WFH":
            wfh += 1
        elif status == "A":
            absent += 1
        elif status in ("CL", "SL"):
            leave += 1
        else:
            not_marked += 1

    # Attendance % = (P + WFH) / (working days - leave days) * 100
    counted_days = len(working_days) - leave
    percent = round((present + wfh) / counted_days * 100, 2) if counted_days > 0 else 0.0

    return {
        "working_days": len(working_days),
        "present": present,
        "wfh": wfh,
        "absent": absent,
        "leave": leave,
        "not_marked": not_marked,
        "percent": percent,
    }

st.title("BrightPath Attendance and Leave Manager")

# Sidebar menu - lets the user pick which "page" to see
page = st.sidebar.radio(
    "Menu",
    ["View Employees", "Mark Attendance", "Apply Leave", "View a Day",
     "Employee Summary", "Team Report"]
)

if page == "View Employees":
    st.header("Employee List")
    rows = []
    for emp_id, info in employees.items():
        rows.append({
            "ID": emp_id,
            "Name": info["name"],
            "Department": info["dept"],
            "CL Left": info["CL"],
            "SL Left": info["SL"],
        })
    st.dataframe(rows, use_container_width=True)

elif page == "Mark Attendance":
    st.header("Mark Attendance")

    picked_date = st.date_input("Select a date", value=datetime(2026, 10, 1))
    date_text = picked_date.strftime(DATE_FORMAT)

    # Validation: holiday or weekend
    if date_text in HOLIDAYS:
        st.error(f"{date_text} is a company holiday. Please pick a working day.")
    elif picked_date.weekday() >= 5:
        st.error(f"{date_text} is a {picked_date.strftime('%A')}. Please pick a working day.")
    elif date_text in attendance:
        st.warning(f"Attendance for {date_text} is already marked. It cannot be marked again.")
        st.write(attendance[date_text])
    else:
        st.write(f"Marking attendance for **{date_text}**")
        on_leave_today = leaves.get(date_text, {})
        today_status = {}

        for emp_id, info in employees.items():
            if emp_id in on_leave_today:
                leave_type = on_leave_today[emp_id]
                today_status[emp_id] = leave_type
                st.write(f"**{emp_id} {info['name']}**: on leave ({leave_type}) - marked automatically")
            else:
                status = st.radio(
                    f"{emp_id} {info['name']}",
                    ["P", "WFH", "A"],
                    horizontal=True,
                    key=f"mark_{date_text}_{emp_id}",
                )
                today_status[emp_id] = status

        if st.button("Save Attendance"):
            attendance[date_text] = today_status
            st.session_state.attendance = attendance  # keep session_state in sync
            save_all()
            statuses = list(today_status.values())
            st.success(
                f"Saved {date_text} -> Present {statuses.count('P')} | "
                f"WFH {statuses.count('WFH')} | Absent {statuses.count('A')} | "
                f"Leave {statuses.count('CL') + statuses.count('SL')}"
        )

elif page == "Apply Leave":
    st.header("Apply Leave")

    with st.form("apply_leave_form"):
        emp_id = st.selectbox(
            "Employee",
            options=list(employees.keys()),
            format_func=lambda e: f"{e} - {employees[e]['name']}",
        )
        leave_type = st.radio("Leave type", ["CL", "SL"], horizontal=True)
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From date", value=datetime(2026, 10, 1))
        with col2:
            end_date = st.date_input("To date", value=datetime(2026, 10, 1))
        submitted = st.form_submit_button("Apply Leave")

    if submitted:
        start = start_date.strftime(DATE_FORMAT)
        end = end_date.strftime(DATE_FORMAT)

        if end_date < start_date:
            st.error("To date cannot be before From date.")
        else:
            # Count only working days
            leave_days = []
            skipped = []
            current = start_date
            while current <= end_date:
                day_text = current.strftime(DATE_FORMAT)
                if day_text in HOLIDAYS:
                    skipped.append((day_text, "holiday"))
                elif current.weekday() >= 5:
                    skipped.append((day_text, current.strftime("%A")))
                else:
                    leave_days.append(day_text)
                current += timedelta(days=1)

            if skipped:
                text = ", ".join(f"{d} ({reason})" for d, reason in skipped)
                st.info(f"Skipping {text}")

            if not leave_days:
                st.warning("No working days in this range, so no leave is needed.")
            else:
                st.write(f"Working days of leave: {len(leave_days)} ({', '.join(leave_days)})")

                # Check overlap
                overlap = False
                for day in leave_days:
                    if attendance.get(day):
                        st.error(f"Rejected: {day} is already marked.")
                        overlap = True
                        break
                    if emp_id in leaves.get(day, {}):
                        st.error(f"Rejected: {employees[emp_id]['name']} is already on leave on {day}.")
                        overlap = True
                        break

                if not overlap:
                    balance = employees[emp_id][leave_type]
                    if balance < len(leave_days):
                        st.error(
                            f"Rejected: {employees[emp_id]['name']} needs {len(leave_days)} day(s) "
                            f"but has only {balance} {leave_type} left."
                        )
                    else:
                        for day in leave_days:
                            leaves[day][emp_id] = leave_type
                        employees[emp_id][leave_type] = balance - len(leave_days)
                        st.session_state.leaves = leaves
                        st.session_state.employees = employees
                        save_all()
                        st.success(
                            f"Leave approved for {employees[emp_id]['name']}. "
                            f"{leave_type} balance: {balance} -> {employees[emp_id][leave_type]}"
                        )

elif page == "View a Day":
    st.header("View a Day")

    chosen = st.date_input("Select a date", value=datetime(2026, 10, 1))
    day_str = chosen.strftime(DATE_FORMAT)

    # .get() reads without creating empty entries in the defaultdicts
    marked = attendance.get(day_str, {})
    on_leave = leaves.get(day_str, {})

    # Combine marked attendance + approved leave
    day = dict(marked)
    day.update(on_leave)

    if not day:
        st.info(f"No attendance or leave recorded for {day_str}.")
    else:
        if not marked:
            st.caption("Attendance not marked yet for this date. Showing approved leave only.")

        # Sets: group employees by status
        present = {e for e, s in day.items() if s == "P"}
        wfh     = {e for e, s in day.items() if s == "WFH"}
        absent  = {e for e, s in day.items() if s == "A"}
        leave   = {e for e, s in day.items() if s in ("CL", "SL")}

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Present", len(present))
        c2.metric("WFH", len(wfh))
        c3.metric("Absent", len(absent))
        c4.metric("On Leave", len(leave))

        def show_group(title, group):
            st.subheader(title)
            if group:
                for e in sorted(group):
                    extra = f" ({day[e]})" if title == "On Leave" else ""
                    st.write(f"{e} - {employees[e]['name']}{extra}")
            else:
                st.write("None")

        show_group("Present", present)
        show_group("Work From Home", wfh)
        show_group("Absent", absent)
        show_group("On Leave", leave)

elif page == "Employee Summary":
    st.header("Employee Summary")

    emp_id = st.selectbox(
        "Employee",
        options=list(employees.keys()),
        format_func=lambda e: f"{e} - {employees[e]['name']}",
    )

    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox(
            "Month",
            options=list(range(1, 13)),
            index=9,  # October
            format_func=lambda m: datetime(2000, m, 1).strftime("%B"),
        )
    with col2:
        year = st.number_input("Year", min_value=2020, max_value=2100, value=2026, step=1)

    # Step 1: collect every working day of the chosen month
    working_days = []
    current = datetime(int(year), month, 1)
    while current.month == month:
        day_text = current.strftime(DATE_FORMAT)
        if current.weekday() < 5 and day_text not in HOLIDAYS:
            working_days.append(day_text)
        current += timedelta(days=1)

    # Step 2: count each status for this employee
    present = wfh = absent = leave = not_marked = 0
    for d in working_days:
        # .get() reads safely without creating empty entries
        status = attendance.get(d, {}).get(emp_id) or leaves.get(d, {}).get(emp_id)
        if status == "P":
            present += 1
        elif status == "WFH":
            wfh += 1
        elif status == "A":
            absent += 1
        elif status in ("CL", "SL"):
            leave += 1
        else:
            not_marked += 1

    # Step 3: attendance % = (P + WFH) / (working days - leave days) * 100
    counted_days = len(working_days) - leave
    if counted_days > 0:
        percent = round((present + wfh) / counted_days * 100, 2)
    else:
        percent = 0.0

    title = datetime(int(year), month, 1).strftime("%B %Y").upper()
    st.subheader(f"{title} : {employees[emp_id]['name']} ({emp_id})")

    c1, c2, c3 = st.columns(3)
    c1.metric("Working days", len(working_days))
    c2.metric("Present", present)
    c3.metric("Work from home", wfh)

    c4, c5, c6 = st.columns(3)
    c4.metric("Absent", absent)
    c5.metric("Leave", leave)
    c6.metric("Attendance", f"{percent:.2f}%")

    if not_marked:
        st.caption(f"{not_marked} working day(s) are not marked yet and count against the percentage.")

elif page == "Team Report":
    st.header("Team Report")

    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox(
            "Month",
            options=list(range(1, 13)),
            index=9,  # October
            format_func=lambda m: datetime(2000, m, 1).strftime("%B"),
        )
    with col2:
        year = st.number_input("Year", min_value=2020, max_value=2100, value=2026, step=1)

    # Build one row per employee
    rows = []
    for emp_id in employees:
        s = get_month_stats(emp_id, month, int(year))

        # No attended/absent days marked at all means there is no data yet
        if s["present"] + s["wfh"] + s["absent"] == 0:
            status = "No data"
        elif s["percent"] < 75:
            status = "Below 75%"
        else:
            status = "OK"

        rows.append({
            "ID": emp_id,
            "Name": employees[emp_id]["name"],
            "Present": s["present"],
            "WFH": s["wfh"],
            "Absent": s["absent"],
            "Leave": s["leave"],
            "Attendance %": s["percent"],
            "Status": status,
        })

    # Highest attendance first (lambda sort, as in the brief)
    rows.sort(key=lambda r: r["Attendance %"], reverse=True)
    df = pd.DataFrame(rows)

    # Flag anyone below 75%
    low = [r["Name"] for r in rows if r["Status"] == "Below 75%"]
    if low:
        st.warning("Below 75% attendance: " + ", ".join(low))
    else:
        st.success("Everyone is at or above 75% attendance.")

    st.dataframe(df, hide_index=True)

    st.subheader("Attendance % by employee")
    st.bar_chart(df.set_index("Name")["Attendance %"])

    # Download the report as a CSV file
    month_name = datetime(2000, month, 1).strftime("%B")
    st.download_button(
        label="Download report as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"team_report_{month_name}_{int(year)}.csv",
        mime="text/csv",
    )