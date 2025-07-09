# Deployment Checklist for Render

## ✅ Pre-Deployment Steps

### 1. Database Setup (Supabase)
- [ ] Go to your Supabase project dashboard
- [ ] Navigate to SQL Editor
- [ ] Run the contents of `schema.sql` to create tables
- [ ] Verify tables are created: `cattle_info`, `doctors`, `health_log`

### 2. Environment Variables
- [ ] Generate a strong SECRET_KEY (you can use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Get your Supabase connection string from Database settings
- [ ] Note down the connection string format: `postgresql://postgres:[PASSWORD]@db.sklrifdmdyzofielkvsj.supabase.co:5432/postgres`

### 3. Repository Preparation
- [ ] Ensure all files are committed to your Git repository
- [ ] Verify `requirements.txt` has all dependencies
- [ ] Verify `Procfile` exists and contains: `web: gunicorn app:app`

## ✅ Render Deployment Steps

### 1. Create Web Service
- [ ] Go to [Render Dashboard](https://dashboard.render.com)
- [ ] Click "New +" → "Web Service"
- [ ] Connect your GitHub repository
- [ ] Choose the repository with your cattle farm storage code

### 2. Configure Service
- [ ] **Name**: `cattle-farm-storage` (or your preferred name)
- [ ] **Environment**: `Python 3`
- [ ] **Region**: Choose closest to your users
- [ ] **Branch**: `main` (or your default branch)
- [ ] **Build Command**: `pip install -r requirements.txt`
- [ ] **Start Command**: `gunicorn app:app`

### 3. Set Environment Variables
- [ ] Click on "Environment" tab
- [ ] Add the following variables:
  - `SECRET_KEY`: Your generated secret key
  - `DATABASE_URL`: Your Supabase connection string

### 4. Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for build to complete
- [ ] Check logs for any errors

## ✅ Post-Deployment Verification

### 1. Test Application
- [ ] Visit your deployed URL
- [ ] Should redirect to login page
- [ ] Login with default credentials:
  - Username: `admin`
  - Password: `admin123`

### 2. Test Features
- [ ] Add a new cattle record
- [ ] Upload photos
- [ ] Search for cattle
- [ ] Add health logs
- [ ] View health logs

### 3. Security
- [ ] Change default admin password
- [ ] Verify file uploads work
- [ ] Test logout functionality

## ❌ Troubleshooting

### Common Issues

1. **Build Fails**
   - Check `requirements.txt` for correct package names
   - Verify Python version compatibility

2. **Database Connection Error**
   - Verify `DATABASE_URL` is correct
   - Check Supabase database is accessible
   - Ensure schema is created

3. **Login Issues**
   - Run the setup script: `python setup_database.py`
   - Check if admin user exists in database

4. **File Upload Issues**
   - Verify `static/uploads` folder exists
   - Check file permissions

### Useful Commands

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Test database connection locally
python setup_database.py

# Run application locally
python app.py
```

## 📞 Support

If you encounter issues:
1. Check Render logs in the dashboard
2. Verify all environment variables are set
3. Ensure database schema is created
4. Test locally first with `python app.py` 