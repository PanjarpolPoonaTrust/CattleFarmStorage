# Cattle Farm Storage System

A Flask-based web application for managing cattle information and health logs.

## Features

- 🔐 Secure authentication system
- 📊 Cattle information management
- 🏥 Health log tracking
- 📸 Photo upload support
- 🔍 Advanced search functionality

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL (Supabase)
- **Deployment**: Render
- **Authentication**: Custom scrypt-based password hashing

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd CattleFarmStorage-main
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `env_template.txt` to `.env`
   - Fill in your Supabase credentials

4. **Set up the database**
   - Go to your Supabase project SQL editor
   - Run the contents of `schema.sql`

5. **Run the application**
   ```bash
   python app.py
   ```

## Deployment on Render

### 1. Database Setup (Supabase)

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the following SQL commands:

```sql
-- Create cattle_info table
CREATE TABLE IF NOT EXISTS cattle_info (
    id SERIAL PRIMARY KEY,
    breed VARCHAR(100),
    color VARCHAR(50),
    age INTEGER,
    shed_no VARCHAR(20),
    notes TEXT,
    photo1 VARCHAR(255),
    photo2 VARCHAR(255),
    photo3 VARCHAR(255),
    photo4 VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create doctors table for authentication
CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create health_log table
CREATE TABLE IF NOT EXISTS health_log (
    id SERIAL PRIMARY KEY,
    cattle_id INTEGER REFERENCES cattle_info(id) ON DELETE CASCADE,
    checkup_date DATE,
    diagnosis TEXT,
    medicines TEXT,
    remarks TEXT,
    photo VARCHAR(255),
    doctor_username VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin account (username: admin, password: admin123)
INSERT INTO doctors (username, password) VALUES 
('admin', 'scrypt:16384:8:1$dGVtcG9yYXJ5LXNhbHQ=$73637279707400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')
ON CONFLICT (username) DO NOTHING;
```

### 2. Render Deployment

1. **Connect your repository to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the service**
   - **Name**: `cattle-farm-storage` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

3. **Set environment variables**
   - Go to your service settings
   - Add the following environment variables:
     - `SECRET_KEY`: Generate a strong secret key
     - `DATABASE_URL`: Your Supabase connection string

4. **Get Supabase connection string**
   - Go to your Supabase project settings
   - Navigate to Database → Connection string
   - Copy the connection string and set it as `DATABASE_URL`

### 3. Environment Variables for Render

Set these in your Render service environment variables:

```
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.sklrifdmdyzofielkvsj.supabase.co:5432/postgres
```

## Default Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change the default password after first login!

## File Structure

```
CattleFarmStorage-main/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── schema.sql            # Database schema
├── Procfile              # Render deployment configuration
├── static/               # Static files (CSS, uploads)
│   ├── style.css
│   └── uploads/          # Photo uploads
└── templates/            # HTML templates
    ├── base.html
    ├── login.html
    ├── index.html
    ├── add_cattle.html
    ├── add_log.html
    └── view_logs.html
```

## Security Features

- Scrypt password hashing for secure authentication
- Session-based authentication
- Secure file upload handling
- SQL injection prevention with parameterized queries

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify your `DATABASE_URL` is correct
   - Check if your Supabase database is accessible
   - Ensure the schema has been created

2. **Upload Folder Issues**
   - The app automatically creates the upload folder
   - Ensure Render has write permissions

3. **Login Issues**
   - Verify the default admin account was created
   - Check if the password hash is correct

### Logs

Check Render logs for detailed error information:
- Go to your service dashboard
- Click on "Logs" tab
- Look for error messages

## Support

For issues or questions:
1. Check the logs in Render dashboard
2. Verify all environment variables are set correctly
3. Ensure the database schema is properly created

## License

This project is open source and available under the MIT License. 