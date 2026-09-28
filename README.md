# CareerNest Hub

CareerNest Hub is a comprehensive career platform built with Django, featuring job and internship postings, applications, course management, interview scheduling, and AI-assisted chat support.

## Features
- **Job & Internship Portal**: Search, browse, and apply for opportunities.
- **Application Tracking**: Track status of submitted applications.
- **Course Learning**: Access courses and track completion progress.
- **Interactive Chat**: AI-powered career assistant.
- **Employer / Admin Dashboard**: Manage listings, applications, and reviews.

## Getting Started

### Prerequisites
- Python 3.11+
- Virtual environment

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/vegadasamarth1111-sys/CareerNest_Hub.git
   cd CareerNest_Hub/CareerNest_Hub/pro_career
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # On Windows
   # source venv/bin/activate # On macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install django pillow razorpay requests
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```
