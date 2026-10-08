# Employee Attendance and Leave Manager

A Python project for BrightPath Solutions (6 employees). It marks daily
attendance, handles leave with balances, skips weekends and holidays,
and produces monthly attendance reports.

## Features
- Mark attendance (P / WFH / A); approved leave is filled in automatically
- Apply CL / SL leave: counts only working days, checks the balance, blocks overlaps
- View a day, employee monthly summary, team report (flags below 75%)
- Data saved to text files and loaded when the program starts

## Built with
Python, datetime, defaultdict, sets, dictionaries, lambda, file handling.
Phase 2 web app: Streamlit and pandas.

## How to run
Console program: `python attendance_manager.py`

Web app: `pip install -r requirements.txt`, then `streamlit run app.py`

## Attendance % rule
(Present + WFH) / (Working days - Leave days) x 100

## Screenshots

### Console program
![View employees](screenshots/console_1_view_employees.png)
![Mark attendance](screenshots/console_2_mark_attendance.png)
![Leave approved](screenshots/console_3_leave_approved.png)
![Low balance rejection](screenshots/console_3_low_balance.png)
![View a day](screenshots/console_4_view_day.png)
![Employee summary](screenshots/console_5_summary.png)
![Team report](screenshots/console_6_team_report.png)
![Save data](screenshots/console_7_save_data.png)
![Holiday date](screenshots/console_holiday.png)
![Exit](screenshots/console_8_exit.png)

### Web app (Streamlit)
![View employees](screenshots/web_view_employees.png)
![Mark attendance](screenshots/web_mark_attendance.png)
![Apply leave](screenshots/web_apply_leave.png)
![Leave skipping weekend and holiday](screenshots/web_apply_leave_skipping_holiday.png)
![Leave rejected](screenshots/web_rejected_leave.png)
![View a day](screenshots/web_view_day.png)
![Employee summary](screenshots/web_employee_summary.png)
![Team report](screenshots/web_team_report.png)