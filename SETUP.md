# HR Policies & Benefits Copilot - Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd hr-copilot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration (especially OPENAI_API_KEY)
```

### 3. Initialize Database

```bash
# Initialize database with sample data
python init_db.py
```

### 4. Run the Application

```bash
# Start the development server
uvicorn app.main:app --reload
```

The application will be available at:
- **Employee Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=sqlite:///./hr_copilot.db
REDIS_URL=redis://localhost:6379

# OpenAI API (Required for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=8000

# ChromaDB (Vector Database)
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### Getting OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

## Features Overview

### 1. Employee Interface
- **Ask Questions**: Natural language queries about HR policies
- **Quick Questions**: Pre-defined common questions
- **Form Suggestions**: Automatically suggests relevant forms
- **Feedback System**: Rate responses for continuous improvement

### 2. Admin Dashboard
- **Document Upload**: Upload and process HR documents (PDF, DOCX)
- **Policy Management**: Create, edit, and manage policies
- **Form Management**: Add and link forms to policies
- **Analytics**: View system performance and usage metrics
- **System Health**: Monitor database and vector database status

### 3. API Endpoints

#### Query Endpoints
- `POST /api/query/` - Submit HR questions
- `POST /api/query/feedback` - Submit feedback on responses
- `GET /api/query/history/{user_id}` - Get query history

#### Policy Endpoints
- `GET /api/policies/` - List all policies
- `POST /api/policies/` - Create new policy
- `PUT /api/policies/{id}` - Update policy
- `DELETE /api/policies/{id}` - Delete policy

#### Form Endpoints
- `GET /api/forms/` - List all forms
- `POST /api/forms/` - Create new form
- `POST /api/forms/link-policy` - Link form to policy

#### Analytics Endpoints
- `GET /api/analytics/` - Get system analytics
- `GET /api/analytics/queries` - Get query analytics
- `GET /api/analytics/performance` - Get performance metrics

## Usage Examples

### 1. Asking Questions

```bash
# Example API call
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I request PTO?",
    "user_id": "employee_123"
  }'
```

### 2. Uploading Documents

```bash
# Upload a policy document
curl -X POST "http://localhost:8000/api/admin/upload-document" \
  -F "file=@policy_document.pdf" \
  -F "category=PTO" \
  -F "title=Updated PTO Policy"
```

### 3. Creating Policies

```bash
# Create a new policy
curl -X POST "http://localhost:8000/api/policies/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Remote Work Policy",
    "content": "Policy content here...",
    "category": "General",
    "version": "1.0"
  }'
```

## Testing

### Run Test Suite

```bash
# Start the application first
uvicorn app.main:app --reload

# In another terminal, run tests
python test_app.py
```

### Manual Testing

1. Open http://localhost:8000 in your browser
2. Try asking questions like:
   - "How do I request PTO?"
   - "What's the travel reimbursement policy?"
   - "Can I work remotely?"
3. Check the admin panel for analytics and document upload

## Docker Deployment

### Using Docker Compose

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d
```

### Using Docker

```bash
# Build the image
docker build -t hr-copilot .

# Run the container
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key hr-copilot
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure you have a valid OpenAI API key
   - Check that the key is correctly set in `.env`
   - Verify you have sufficient API credits

2. **Database Connection Error**
   - Check that the database URL is correct
   - Ensure the database file is writable
   - Try running `python init_db.py` again

3. **Vector Database Error**
   - Ensure the `chroma_db` directory is writable
   - Try deleting the directory and reinitializing

4. **Port Already in Use**
   - Change the port in `.env` or use a different port
   - Kill any existing processes using port 8000

### Logs and Debugging

```bash
# Run with debug logging
uvicorn app.main:app --reload --log-level debug

# Check application logs
tail -f app.log
```

## Production Deployment

### Security Considerations

1. **Change Default Secret Key**
   - Generate a strong secret key
   - Use environment variables for sensitive data

2. **Database Security**
   - Use PostgreSQL in production
   - Enable SSL connections
   - Regular backups

3. **API Security**
   - Implement authentication
   - Rate limiting
   - Input validation

### Performance Optimization

1. **Database Optimization**
   - Use connection pooling
   - Index frequently queried fields
   - Regular maintenance

2. **Caching**
   - Redis for session storage
   - Cache frequent queries
   - CDN for static files

3. **Monitoring**
   - Application performance monitoring
   - Error tracking
   - Usage analytics

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check the logs for error messages
4. Create an issue in the repository

## License

This project is licensed under the MIT License - see the LICENSE file for details.

