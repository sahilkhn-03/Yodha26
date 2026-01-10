# Deploy to Vercel

## Quick Deploy (Recommended)

### Option 1: Using Vercel CLI (Fastest)

1. **Install Vercel CLI globally:**
```bash
npm install -g vercel
```

2. **Deploy from project directory:**
```bash
cd C:\Users\91903\Yodha26\voice_stress_analysis\project
vercel
```

3. **Follow the prompts:**
   - Login to Vercel (first time)
   - Link to existing project or create new
   - Confirm settings
   - Deploy!

4. **Set environment variables in Vercel dashboard:**
   - Go to your project settings on vercel.com
   - Add these environment variables:
     - `VITE_SUPABASE_URL` = https://rwrhwrwqhymupfxlottq.supabase.co
     - `VITE_SUPABASE_ANON_KEY` = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3cmh3cndxaHltdXBmeGxvdHRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc5OTI0MjUsImV4cCI6MjA4MzU2ODQyNX0.7rNuzkMEaWa6B6Eqzlw8-o9E6VB4W2nlyko_LSys6hQ
     - `VITE_API_URL` = (Your backend API URL when deployed)

5. **Redeploy after adding env vars:**
```bash
vercel --prod
```

---

### Option 2: Using GitHub + Vercel (Automatic deployments)

1. **Push to GitHub:**
```bash
cd C:\Users\91903\Yodha26
git add voice_stress_analysis/project
git commit -m "Add voice stress frontend"
git push origin main
```

2. **Connect to Vercel:**
   - Go to https://vercel.com/new
   - Import your GitHub repository: `sahilkhn-03/Yodha26`
   - Root Directory: `voice_stress_analysis/project`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Add Environment Variables:**
   - In Vercel project settings, add:
     - `VITE_SUPABASE_URL`
     - `VITE_SUPABASE_ANON_KEY`
     - `VITE_API_URL`

4. **Deploy!**
   - Click "Deploy"
   - Vercel will auto-deploy on every push to main branch

---

## After Deployment

Your frontend will be live at: `https://your-project-name.vercel.app`

**Important:** Update `VITE_API_URL` to point to your deployed backend API URL (we'll deploy the backend next with Docker).

---

## Backend Deployment (Next Step)

After frontend is deployed, we need to deploy the Python backend API:

### Option 1: Deploy to Render.com (Free tier available)
### Option 2: Deploy to Railway.app
### Option 3: Deploy to Google Cloud Run (with Docker)

Would you like me to help deploy the backend next?
