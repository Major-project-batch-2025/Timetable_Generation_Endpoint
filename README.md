# 📅 Timetable Generation

An intelligent **automated timetable generator** built using **Constraint Programming** and exposed via a **Flask API Endpoint**. This project generates valid weekly timetables based on predefined **constraints** and makes it easy to retrieve schedules on-demand.

## 🎯 Project Purpose

The goal of this project is to automatically generate an optimal timetable that satisfies real-world academic scheduling rules using **Google OR-Tools**. This ensures fairness, efficiency, and flexibility in academic planning.
With just one API call, the system builds an efficient weekly schedule for all sections, avoiding conflicts and overloads.

## ✅ Constraints Handled

### 🧑‍🏫 Teacher Conflict Constraints
- No teacher can be assigned to multiple sections in the same time slot
- Each teacher can teach at most one theory class per day per section when not conducting labs

### 🏫 Classroom & Lab Availability
- Maximum of `num_of_classrooms` concurrent theory classes at any time
- Maximum of `num_of_labrooms` concurrent lab sessions
- Lab sessions require dedicated lab rooms

### ⏱ Schedule Optimization
- Minimizes internal idle periods (gaps between classes) within each day
- Lab sessions are scheduled in continuous 2-hour blocks using predefined pairs:
  - 8:30-10:30
  - 11:00-1:00
  - 2:00-4:00

### 🕐 Time Constraints
- Classes run Monday through Saturday
- No classes after 1:00 PM on Saturdays
- Fixed break period from 10:30 AM to 11:00 AM
- Daily time slots:
  ```
  8:30-9:30  | 9:30-10:30 | 11:00-12:00
  12:00-1:00 | 2:00-3:00  | 3:00-4:00
  ```

## 🔧 Technical Features

- **Constraint Solver**: Google OR-Tools CP-SAT solver with randomized seed
- **Dynamic Scheduling**: Handles variable sections, courses, and teachers
- **Flexible API**: JSON-based REST API
- **Lab Management**: Special handling for consecutive lab slots
- **Optimization**: Quadratic penalty function for minimizing schedule gaps
- **Validation**: Comprehensive constraint checking

## 🧪 Tech Stack

- 🐍 **Python**: Core programming language
- 🧩 **Google OR-Tools**: Constraint programming solver
- 🌐 **Flask**: API endpoint framework
- 📊 **Tabulate**: Output formatting

## 🚀 Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/Major-project-batch-2025/Timetable_Generation_Endpoint.git
```

2. Navigate to project directory:
```bash
cd Timetable_Generation_Endpoint
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the Flask server:
```bash
python app.py
```

## 📡 API Usage

Send a POST request to `/generate-timetable` with the following JSON structure:

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
