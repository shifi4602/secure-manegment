# Comp In-Office Coding Evaluation

Hey\! We are stoked that you are interested in joining the engineering team at Comp.io\!  
The following evaluation is designed to give you an opportunity to show your coding skills.  
The exercise is composed of 2 parts:

1. You will be given a coding exercise (the details below) and 2 hours to write your solution.  
2. We will conduct a short interview where you will present your solution and we will discuss it together. You will be expected to explain your code and the decisions you made when implementing the solution and the design.

## Usage of AI and External Resources

Google, StackOverflow and AI are allowed but **you will be expected to explain all the parts of your solution**.   
You are accountable for each class, line of code and test in the solution including logging and comments.   
In order to have a higher chance of acing the interview part, we recommend you write the code the way you think it should be written and not the way the AI writes it. 
  
## Programming Language

Use the programming language you feel most comfortable with. We provide starter projects for Java, Python, TypeScript and C\#. If you prefer another language, feel free to use it as long as you can set up a working environment on your laptop.

## What is the exercise?

You will be creating a simple calendar with one really cool feature: Given a list of people and a desired duration, find all the time slots in a day in which all persons are available to meet.

The input data is provided to you in a simple comma-separated values file (`calendar.csv`) and is structured in the following way:

```
Person name, Event subject, Event start time, Event end time
```

## Goals

Your goal is to design and create a simple calendar application, and implement the following method:

**Java:**
```java
List<LocalTime> findAvailableSlots(List<String> personList, Duration eventDuration);
```

**Python:**
```python
from typing import List
from datetime import time, timedelta

def find_available_slots(person_list: List[str], event_duration: timedelta) -> List[time]:
    pass
```

**TypeScript:**
```typescript
function findAvailableSlots(personList: string[], eventDuration: number): Date[];
```

**C#:**
```csharp
public List<DateTime> FindAvailableSlots(List<string> personList, TimeSpan eventDuration);
```

#### Requirements:

- This calendar has only one day. So to make things simple \- events have only start and end time (no dates)  
- The day starts at 07:00 and ends at 19:00. Take that into consideration when finding available time slots.

Wherever you feel the requirements are vague and leave room for interpretation \- take advantage of it\! You can make any choice you want as long as it makes sense in the context of the exercise and you can explain the rationale behind it. 

## Example

Attached is an example calendar file `calendar.csv`:

```
Alice,"Morning meeting",08:00,09:30
Alice,"Lunch with Jack",13:00,14:00
Alice,"Yoga",16:00,17:00
Jack,"Morning meeting",08:00,08:50
Jack,"Sales call",09:00,09:40
Jack,"Lunch with Alice",13:00,14:00
Jack,"Yoga",16:00,17:00
Bob,"Morning meeting",08:00,09:30
Bob,"Morning meeting 2",09:30,09:40
Bob,"Q3 review",10:00,11:30
Bob,"Lunch and siesta",13:00,15:00
Bob,"Yoga",16:00,17:00
```

For this input, and for a meeting of 60 minutes which Alice & Jack should attend the following output is expected:

```
Starting Time of available slots: 07:00
Starting Time of available slots: 09:40 - 12:00
Starting Time of available slots: 14:00 - 15:00
Starting Time of available slots: 17:00 - 18:00
```

## Give high Attention to Code Quality

Please address the following aspects in your code:

- Object oriented design \- the solution should be designed as a set of modular and decoupled classes. Based on your level of experience, you will be expected to provide a design that can be easily extended where it makes sense. Following SOLID principles is always a good idea.  
- Meaningful naming for your classes and APIs.  
- Tests: Implement 2-3 tests that you think are the most important. 

## Getting Started

Choose the programming language you feel most comfortable with and open the corresponding starter project:

- **Python**: Open the `python-project` directory in your IDE


**Each starter project contains a README.md file with detailed setup instructions, including:**
- Prerequisites and dependencies
- How to build and run the application
- How to run tests
- IDE-specific setup instructions
- Project structure overview

Please refer to the README.md file inside your chosen starter project for complete instructions.

## Submitting the Exercise

We will review the solution on your laptop.   
Make sure it complies and runs.  
