# 📅 Timetable Generation

An intelligent **automated timetable generator** built using **Constraint Programming** and exposed via a **Flask API Endpoint**. This project generates valid weekly timetables based on predefined **constraints** and makes it easy to retrieve schedules on-demand.

---

## 🎯 Project Purpose

The goal of this project is to automatically generate an optimal timetable that satisfies real-world academic scheduling rules using **Google OR-Tools**. This ensures fairness, efficiency, and flexibility in academic planning.
With just one API call, the system builds an efficient weekly schedule for all sections, avoiding conflicts and overloads.

---

## ✅ Constraints Handled

This system guarantees the generated timetable satisfies the following conditions:

- 🧑‍🏫 **Teacher Conflict Constraint**  
  > A teacher cannot teach in more than one section at the same time.

- 🏫 **Classroom Availability Constraint**  
  > Only `(number_of_sections - 1)` classrooms are available at any given time.

- ⏱ **2-Hour Gap Constraint**  
  > A teacher must have a **minimum 2-hour break** between two classes in a day.

- 🕐 **Saturday Constraint**  
  > No classes are allowed **after 1:00 PM** on Saturdays.

---

## 🧪 Tech Stack

- 🐍 **Python 3**
- 🧩 **Google OR-Tools**
- 🌐 **Flask**
- ⚙️ **uv** - ultra-fast Python package manager and runner

---

## 🚀 Setup & Run Instructions

### 1️⃣ Clone the Repository
```bash

git clone git clone https://github.com/Major-project-batch-2025/Timetable_Generation_Endpoint.git

```

###  Change Directory
```bash

cd Timetable_Generation_Endpoint

```

###  Install Dependencies
```bash

uv add -r requirements.txt

```

###  Run The Flask App
```bash

uv run ./app.py

```



