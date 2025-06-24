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
  > No teacher can be assigned to multiple sections in the same time slot.

- 🏫 **Classroom & Lab Availability**  
  > - Maximum of `num_of_classrooms` concurrent theory classes at any time
  > - Maximum of `num_of_labrooms` concurrent lab sessions
  > - Lab sessions require dedicated lab rooms

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
  "sections": ["Section A", "Section B", "Section C"],
  "num_of_classrooms": 2,
  "num_of_labrooms": 1,
  "course_req": {
    "CS101": 3,
    "CS102": 3,
    "CS103": 3,
    "CS107": 2
  },
  "section_course_teacher": {
    "Section A": {
      "CS101": "Mr. Madhu",
      "CS102": "Mrs. Chandana",
      "CS103": "Dr. Ramesh",
      "CS105": "Mrs. Shobha chandra K",
      "CS106": "Dr. Chandrika J",
      "CS107": "Mr. Keerthi K S"
    },
    "Section B": {
      "CS101": "Ms. Harshita",
      "CS102": "Dr. Ramesh",
      "CS103": "Ms. Ayeesha",
      "CS105": "Mr. Ravi Kumar D",
      "CS106": "Mrs. Shruthi A S",
      "CS107": "Mrs. Chandana"
    },
    "Section C": {
      "CS101": "Mr. Ravi Kumar D",
      "CS102": "Mr. Tejonidhi M R",
      "CS103": "Mr. Keerthi K S",
      "CS105": "Mrs. Nithyashree R",
      "CS106": "Ms. Harshita",
      "CS107": "Ms. Ayeesha"
    }
  },
  "all_lab_course_names": ["CS105", "CS106"],
  "lab_course_sessions_needed": {
    "CS105": 2,
    "CS106": 2
  }
}

```
