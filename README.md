# MathAssistant

**Version:** v0.1 (MVP)
**Last Updated:** June 04, 2026

## Overview

MathAssistant is an AI-powered algebra tutoring application designed to help students learn **how to solve problems**, rather than simply providing answers.

Unlike traditional AI math tools that immediately reveal solutions, MathAssistant guides students through the problem-solving process by:

* Identifying the type of algebra problem
* Validating each submitted step
* Detecting the first incorrect transformation
* Classifying mathematical errors
* Generating contextual hints
* Supporting a structured step-by-step workflow

The goal is to encourage independent problem-solving skills while reducing reliance on answer-generating systems.

---

## Problem Statement

Many AI-based math applications prioritize answer generation over student learning. While this can be useful for verification, it may create dependency on automated solutions and reduce opportunities for developing critical thinking and algebraic reasoning skills.

MathAssistant addresses this issue by focusing on guided learning and feedback. Instead of immediately revealing answers, the system provides targeted hints and validation that help students discover the correct solution themselves.

---

## Goals

### Primary Goals

* Identify the type of algebra problem being solved
* Detect the first incorrect algebraic step
* Generate pedagogically useful hints
* Support a step-by-step solving workflow
* Verify whether a final answer is correct

### Success Metrics

| Metric                        | Target |
| ----------------------------- | ------ |
| Problem Type Detection        | 100%   |
| Final Answer Accuracy         | ≥ 80%  |
| Error Classification Accuracy | ≥ 70%  |
| First Error Detection         | 100%   |
| Hint Usefulness               | ≥ 75%  |

---

## Target Users

* High School Algebra I students
* High School Algebra II students
* Self-study STEM learners
* SAT preparation students (future support)

---

## Core User Flow

1. Student enters an algebra problem.
2. A problem-solving session is created.
3. Student submits a solution step.
4. The system validates the step.
5. Feedback and hints are generated.
6. Student continues solving.
7. After multiple attempts, the system can verify the final solution.

---

## MVP Scope

### Included

* Algebra problem solving
* Step validation
* Error detection
* Error classification
* Hint generation
* Attempt tracking
* Final answer verification

### Excluded

* OCR/Image processing
* Geometry
* Calculus
* Statistics
* Automatic problem generation
* Systems with more than five variables

---

## Features

### Problem Type Detection

Determine the algebraic category of a submitted problem.

Examples:

* Linear equations
* Quadratic equations
* Factoring
* Polynomial simplification
* Rational expressions

---

### Step Validation Engine

The core feature of MathAssistant.

Responsibilities:

* Compare step transitions
* Validate algebraic transformations
* Detect the first incorrect operation
* Identify where an error occurs

---

### Error Classification

Categorizes student mistakes into a structured taxonomy.

Examples:

* Arithmetic error
* Sign error
* Distribution error
* Combining-like-terms error
* Equation balancing error

---

### Hint Generation

Hints are generated using:

* Error classification
* Current equation state
* Student attempt history

The system provides guidance toward the next step rather than revealing the complete solution.

---

### Attempt Tracking

Tracks:

* Number of attempts
* Error frequency
* Session progress
* Completion status

---

## Technical Architecture

### System Flow

```text
Frontend
    ↓
FastAPI API Layer
    ↓
Problem Session Manager
    ↓
Step Parsing Layer
    ↓
Validation Engine
    ↓
Error Classification Layer
    ↓
Hint Engine
    ↓
Response
```

---

## Technology Stack

### Frontend

* Next.js
* TypeScript
* Tailwind CSS
* KaTeX

### Backend

* Python
* FastAPI

### Mathematics Engine

* SymPy

### Database

* PostgreSQL

---

## System Components

### Frontend Module

Responsibilities:

* Problem input UI
* Step submission
* Math rendering
* Hint display

---

### API Layer (FastAPI)

Responsibilities:

* Request routing
* Session management
* Validation endpoints

---

### Problem Session Manager

Responsibilities:

* Track attempts
* Store submitted steps
* Manage session state

---

### Step Parsing Layer

Responsibilities:

* Parse algebraic expressions
* Convert input into symbolic form
* Normalize expressions

---

### Validation Engine

Responsibilities:

* Compare successive steps
* Verify transformation validity
* Detect first incorrect step

---

### Error Classification Layer

Responsibilities:

* Categorize mistakes
* Generate structured error data

---

### Hint Engine

Responsibilities:

* Produce contextual hints
* Adjust guidance based on attempt history

---

### Database Layer

Responsibilities:

* User storage
* Problem storage
* Session tracking
* Attempt tracking

---

## Data Models

### Users

| Field               | Type              |
| ------------------- | ----------------- |
| user_id             | UUID              |
| name                | String            |
| email               | String            |
| grade               | String (Optional) |
| problem_solve_count | Integer           |
| signup_date         | DateTime          |

---

### Problems

| Field       | Type    |
| ----------- | ------- |
| problem_id  | UUID    |
| type        | String  |
| date        | Date    |
| time        | Time    |
| guess_count | Integer |

---

### Attempts

| Field        | Type    |
| ------------ | ------- |
| attempt_id   | UUID    |
| problem_id   | UUID    |
| count        | Integer |
| success_bool | Boolean |
| error_count  | Integer |

---

### Sessions

| Field       | Type     |
| ----------- | -------- |
| session_id  | UUID     |
| start_time  | DateTime |
| end_time    | DateTime |
| error_count | Integer  |

---

## Core Algorithm

The validation workflow follows these steps:

1. Parse the student's algebraic expression.
2. Identify the problem type.
3. Determine the expected next valid transformation.
4. Compare the submitted step against the expected transformation.
5. Detect and classify errors.
6. Generate a contextual hint.
7. Continue until completion.
8. Verify the final answer through substitution into the original equation when applicable.

Validation follows standard algebraic rules and order of operations (PEMDAS):

* Parentheses
* Exponents
* Multiplication/Division
* Addition/Subtraction

The system is designed to reveal only the next helpful step rather than the entire solution process.

---

## API Endpoints

### Start Session

```http
POST /start-session
```

Creates a new problem-solving session.

---

### Submit Step

```http
POST /submit-step
```

Submits and validates a student step.

---

### Retrieve Problem

```http
GET /problem/{id}
```

Returns stored problem information.

---

### Sample Problem

```http
GET /sample-problem
```

Returns a sample algebra problem.

> Note: Sample problem generation is planned and may not be included in the MVP.

---

## Risks & Limitations

### Known Risks

* Ambiguous mathematical notation
* Symbolic equivalence edge cases
* Incorrect problem classification
* LLM hallucinations
* Invalid hint generation

### Current Limitations

* Algebra-only support
* Structured input required
* No OCR support
* Limited equation complexity

---

## Future Roadmap

### Planned Features

* OCR-based problem input
* Multi-subject expansion
* Adaptive tutoring system
* Concept re-teaching workflows
* SAT-focused learning mode
* Personalized learning analytics

---

## Development

### Run the Frontend

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

---

### Backend (Planned)

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## Educational Philosophy

MathAssistant is built around the principle that students learn mathematics most effectively when they actively engage with the problem-solving process. The application prioritizes guided discovery, error correction, and conceptual understanding over immediate answer generation.

---

**MathAssistant v0.1 — Helping students learn algebra through guided problem solving.**
