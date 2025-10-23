# KTL Microservices

A microservices architecture project built with Django, featuring authentication, organization management, and an admin panel.

## Services

- **Auth Service**: Handles user authentication, roles, and permissions
- **Organization Service**: Manages organizations and related entities
- **Admin Panel**: Django admin interface for system management

## Shared Components

- **Shared**: Common utilities, models, permissions, and middleware used across services

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/shamimkhaled/demo-microservices.git
   cd ktl-microservices
   ```

2. Set up each service:

   **Auth Service:**
   ```bash
   cd services/auth-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver 8001
   ```

   **Organization Service:**
   ```bash
   cd services/organization-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver 8002
   ```

   **Admin Panel:**
   ```bash
   cd admin-panel
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver 8000
   ```

3. Access the services:
   - Admin Panel: http://localhost:8000/admin/
   - Auth Service: http://localhost:8001/
   - Organization Service: http://localhost:8002/

## Project Structure

```
ktl-microservices/
├── admin-panel/           # Django admin panel
├── services/
│   ├── auth-service/      # Authentication microservice
│   └── organization-service/  # Organization management microservice
├── shared/                # Shared utilities and models
├── .env                   # Environment variables
├── .env.example           # Environment variables template
└── README.md
```

## Development

- Each service is a separate Django project
- Shared components are in the `shared/` directory
- Use virtual environments for each service
- Database: SQLite (for development)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License.