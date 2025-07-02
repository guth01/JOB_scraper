import streamlit as st
import pandas as pd
from job_scraper import JobScraper
from datetime import datetime
import plotly.express as px

st.set_page_config(
    page_title="Job Scraper",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
<style>
    .job-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .skill-tag {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 0.2rem 0.4rem;
        border-radius: 12px;
        margin: 0.1rem;
        display: inline-block;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'jobs_data' not in st.session_state:
        st.session_state.jobs_data = []
    if 'scraper' not in st.session_state:
        st.session_state.scraper = JobScraper()

def display_job_card(job):
    with st.container():
        st.markdown(f"""
        <div class="job-card">
            <h4 style="color: #1565c0; margin-bottom: 0.3rem;">{job['job_title']}</h4>
            <p style="color: #666; margin-bottom: 0.5rem; font-weight: bold;">{job['company']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if job['skills']:
                st.write("**Skills:**")
                skills_html = ""
                for skill in job['skills'][:5]:  # Show first 5 skills
                    skills_html += f'<span class="skill-tag">{skill}</span> '
                if len(job['skills']) > 5:
                    skills_html += f'<span class="skill-tag">+{len(job["skills"]) - 5} more</span>'
                st.markdown(skills_html, unsafe_allow_html=True)
        
        with col2:
            st.write(f"**Location:** {job['location']}")
            st.write(f"**Experience:** {job['experience']}")
            st.write(f"**Posted:** {job['posted_date']}")
        
        if job['job_description'] != "N/A":
            with st.expander("View Description"):
                # In display_job_card function, after the description expander:
                if job['more_info'] != "N/A":
                    st.markdown(f"[🔗 View Full Job Details]({job['more_info']})")
                st.write(job['job_description'])
        
        st.markdown("---")

def create_simple_analytics(jobs):
    """Create simple analytics for scraped jobs"""
    if not jobs:
        return
    
    st.subheader("📊 Quick Stats")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Jobs", len(jobs))
    
    with col2:
        unique_companies = len(set(job['company'] for job in jobs if job['company'] != "N/A"))
        st.metric("Companies", unique_companies)
    
    with col3:
        all_skills = []
        for job in jobs:
            all_skills.extend(job['skills'])
        unique_skills = len(set(all_skills))
        st.metric("Unique Skills", unique_skills)
    
    # Top skills chart
    if all_skills:
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        if top_skills:
            skills, counts = zip(*top_skills)
            
            fig = px.bar(x=counts, y=skills, orientation='h',
                        title="Top 10 Skills in Demand")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def main():
    initialize_session_state()
    
    st.title("💼 Job Scraper")
    st.write("Find jobs that match your skills from TimesJobs.com")
    
    # form
    with st.form("job_search_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input(
                "Job Keywords", 
                value="python developer",
                help="e.g., 'python developer', 'data scientist'"
            )
        
        with col2:
            location = st.text_input(
                "Location (optional)", 
                value="",
                help="e.g., 'Bangalore', 'Mumbai'"
            )
        
        unfamiliar_skills = st.text_input(
            "Skills to avoid (comma-separated)",
            value="",
            help="Enter skills you don't know, separated by commas"
        )
        max_pages = st.slider("Pages to scrape", min_value=1, max_value=10, value=5)
        submitted = st.form_submit_button("🔍 Search Jobs", type="primary")
        
        if submitted:
            with st.spinner("Searching for jobs..."):
                unfamiliar_list = [skill.strip() for skill in unfamiliar_skills.split(',') if skill.strip()]
                
                jobs = st.session_state.scraper.scrape_jobs(
                    search_query=search_query,
                    location=location,
                    unfamiliar_skills=unfamiliar_list,
                    max_pages=max_pages
                )
                
                st.session_state.jobs_data = jobs
                
                if jobs:
                    st.success(f"Found {len(jobs)} suitable jobs!")
                else:
                    st.warning("No jobs found. Try different keywords or remove some skill filters.")
    
    # Display results
    if st.session_state.jobs_data:
        tab1, tab2, tab3 = st.tabs(["📋 Jobs", "📊 Analytics", "📥 Export"])
        
        with tab1:
            st.subheader(f"Job Results ({len(st.session_state.jobs_data)})")
            
            #filter
            search_filter = st.text_input("🔍 Filter by company or job title:", "")
            
            filtered_jobs = st.session_state.jobs_data
            if search_filter:
                filtered_jobs = [
                    job for job in filtered_jobs 
                    if search_filter.lower() in job['company'].lower() or 
                       search_filter.lower() in job['job_title'].lower()
                ]
            
            st.write(f"Showing {len(filtered_jobs)} jobs")
            
            # Display jobs
            for job in filtered_jobs:
                display_job_card(job)
        
        with tab2:
            create_simple_analytics(st.session_state.jobs_data)
        
        with tab3:
            st.subheader("Export Data")
            
            # Convert to DataFrame for export
            df_data = []
            for job in st.session_state.jobs_data:
                df_data.append({
                    'Job Title': job['job_title'],
                    'Company': job['company'],
                    'Skills': ', '.join(job['skills']),
                    'Experience': job['experience'],
                    'Location': job['location'],
                    'Salary': job['salary'],
                    'Posted Date': job['posted_date'],
                    'Job Description': job['job_description'],
                    'More Info': job['more_info']
                })
            
            df = pd.DataFrame(df_data)
            
            # Download
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                json_data = df.to_json(orient='records', indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Preview
            st.subheader("Data Preview")
            st.dataframe(df, use_container_width=True)
    
    else:
        # Instructions when no data
        st.markdown("""
        ## How to use:
        
        1. **Enter job keywords** - What type of job are you looking for?
        2. **Add location** (optional) - Where do you want to work?
        3. **List skills to avoid** - Skills you don't have or want to avoid
        4. **Click Search** - We'll find matching jobs for you!
        
        ### Features:
        - ✅ Filter out jobs requiring unfamiliar skills
        - ✅ View job details and descriptions  
        - ✅ See analytics on skill demand
        - ✅ Export results to CSV or JSON
        
        **Note:** This tool scrapes data from TimesJobs.com for educational purposes.
        """)

if __name__ == "__main__":
    main()