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

- 🏫 **Classroom & Lab Availability**  
  > - Only `(number_of_sections - 1)` classrooms are available at any given time
  > - Lab sessions require dedicated lab rooms
  > - Limited number of lab rooms available simultaneously

- ⏱ **Schedule Optimization**  
  > - Minimizes idle periods between classes
  > - Lab sessions are scheduled in continuous 2-hour blocks
  > - Fair distribution of classes across the week

- 🕐 **Time Constraints**  
  > - No classes after 1:00 PM on Saturdays
  > - Classes scheduled between 8:30 AM to 4:00 PM
  > - Break period from 10:30 AM to 11:00 AM

---

## 🔧 Technical Features

- **Constraint Solver**: Uses Google OR-Tools CP-SAT solver
- **Dynamic Scheduling**: Handles variable numbers of sections, courses, and teachers
- **Flexible API**: JSON-based REST API for easy integration
- **Lab Management**: Special handling for lab courses requiring consecutive slots
- **Optimization**: Minimizes schedule gaps and maximizes resource utilization

---

## 🧪 Tech Stack

- 🐍 **Python 3.13+**
- 🧩 **Google OR-Tools**: For constraint programming
- 🌐 **Flask**: For API endpoints
- 📊 **Tabulate**: For formatted output
- ⚙️ **uv**: Ultra-fast Python package manager

---

## 🚀 Setup & Run Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Major-project-batch-2025/Timetable_Generation_Endpoint.git
```

### 2️⃣ Change Directory
```bash
cd Timetable_Generation_Endpoint
```

### 3️⃣ Install Dependencies
```bash
uv add -r requirements.txt
```

### 4️⃣ Run The Flask App
```bash
uv run ./app.py
```

## 📡 API Usage

Send a POST request to `/generate-timetable` with JSON payload containing:

```json
{
    "sections": ["SectionA", "SectionB", ...],
    "section_course_teacher": {
        "SectionA": {
            "Course1": "Teacher1",
            "LabCourse1": "LabTeacher1"
        }
    },
    "course_req": {
        "Course1": 3  // Weekly sessions needed
    },
    "num_of_classrooms": 2,
    "num_of_labrooms": 1,
    "all_lab_course_names": ["LabCourse1"],
    "lab_course_sessions_needed": {
        "LabCourse1": 2  // Weekly lab sessions needed
    }
}
