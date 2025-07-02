from bs4 import BeautifulSoup
import requests
import time
import os
from urllib.parse import quote_plus
from typing import List, Dict, Optional
import re

class JobScraper:
    def __init__(self):
        self.base_url = "https://www.timesjobs.com/candidate/job-search.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def build_search_url(self, search_query: str = "", location: str = "", page: int = 1) -> str:
        """Build the search URL based on user input"""
        params = {
            'from': 'submit',
            'luceneResultSize': '25',
            'txtKeywords': search_query,
            'postWeek': '60',
            'searchType': 'personalizedSearch',
            'actualTxtKeywords': search_query,
            'searchBy': '0',
            'rdoOperator': 'OR',
            'pDate': 'I',
            'sequence': str(page),
            'startPage': '1'
        }
        
        if location:
            params['txtLocation'] = location
        
        url_params = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in params.items()])
        return f"{self.base_url}?{url_params}"
    
    def extract_job_info(self, job_element) -> Optional[Dict]:
        """Extract comprehensive job information from a job element"""
        try:
            # Company name
            company_elem = job_element.find('h3', class_='joblist-comp-name')
            company = company_elem.text.strip() if company_elem else "N/A"
            
            # Job title
            job_title_elem = job_element.find('h2',class_='heading-trun')
            job_title = job_title_elem.text.strip() if job_title_elem else "N/A"
            
            # Skills
            skills_section = job_element.find('div', class_='more-skills-sections')
            skills_list = []
            if skills_section:
                skills_list = [skill.text.strip() for skill in skills_section.find_all('span')]
            
            # Experience
            tot_elem = job_element.find('ul', class_='top-jd-dtl mt-16 clearfix')

            location = "N/A"
            experience = "N/A"
            salary = "N/A"

            if tot_elem:
                li_elements = tot_elem.find_all('li')
                if len(li_elements) >= 3:
                    if li_elements[0].text.strip():
                        location = li_elements[0].text.strip()
                    if li_elements[1].text.strip():
                        experience = li_elements[1].text.strip()
                    if li_elements[2].text.strip():
                        salary = li_elements[2].text.strip()

            
            # Posted date
            published_elem = job_element.find('span', class_='sim-posted')
            published = "N/A"
            if published_elem and published_elem.span:
                published = published_elem.span.text.strip()
            
            # More info link
            more_info = "N/A"
            link_elem = job_element.find('a')
            if link_elem and link_elem.get('href'):
                more_info = link_elem['href']
            
            # TODO: 
            job_description = "N/A"  
            job_elem=job_element.find('li',class_='job-description__')
            if job_elem:
                job_description=job_elem.text.strip()

            
            return {
                'company': company,
                'job_title': job_title,
                'skills': skills_list,
                'experience': experience,
                'salary': salary,
                'location': location,
                'job_description': job_description,
                'posted_date': published,
                'more_info': more_info
            }
            
        except Exception as e:
            print(f"Error extracting job info: {e}")
            return None
    
    def filter_jobs_by_skills(self, jobs: List[Dict], unfamiliar_skills: List[str]) -> List[Dict]:
        """Filter out jobs that require unfamiliar skills"""
        filtered_jobs = []
        
        for job in jobs:
            job_skills = [skill.lower() for skill in job.get('skills', [])]
            unfamiliar_lower = [skill.lower().strip() for skill in unfamiliar_skills]
            
            # Check if any unfamiliar skill is in job requirements
            has_unfamiliar = any(
                any(unfamiliar in job_skill for job_skill in job_skills)
                for unfamiliar in unfamiliar_lower
            )
            
            if not has_unfamiliar:
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def scrape_jobs(self, search_query: str = "", location: str = "", 
                unfamiliar_skills: Optional[List[str]] = None, max_pages: int = 10) -> List[Dict]:
        """Main method to scrape jobs based on criteria"""
        if unfamiliar_skills is None:
            unfamiliar_skills = []
        
        all_jobs = []
        
        for page in range(1, max_pages + 1):
            url = self.build_search_url(search_query, location, page)
            
            try:
                print(f"Scraping page {page}: {url}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                job_elements = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')
                
                if not job_elements:
                    print(f"No jobs found on page {page}, stopping pagination")
                    break
                
                print(f"Found {len(job_elements)} job listings on page {page}")
                
                page_jobs = []
                for job_element in job_elements:
                    job_info = self.extract_job_info(job_element)
                    if job_info:
                        page_jobs.append(job_info)
                
                all_jobs.extend(page_jobs)
                
                # Add delay between requests
                time.sleep(2)
                
            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue
            except Exception as e:
                print(f"Error parsing page {page}: {e}")
                continue
        
        # Filter by skills
        filtered_jobs = self.filter_jobs_by_skills(all_jobs, unfamiliar_skills)
        
        print(f"Total jobs scraped: {len(all_jobs)}")
        print(f"After filtering: {len(filtered_jobs)} suitable jobs found")
        return filtered_jobs


def main():
    """Command line interface for the job scraper"""
    scraper = JobScraper()
    
    # Get user input
    search_query = input("Enter job search keywords (e.g., 'python developer'): ").strip()
    location = input("Enter preferred location (optional): ").strip()
    unfamiliar_input = input("Enter skills you're not familiar with (comma-separated): ").strip()
    
    unfamiliar_skills = [skill.strip() for skill in unfamiliar_input.split(',') if skill.strip()]
    max_pages = int(input("How many pages to scrape? (1–10): ").strip() or 10)

    print(f"\nSearching for: '{search_query}' in '{location if location else 'all locations'}'")
    print(f"Filtering out jobs requiring: {unfamiliar_skills}\n")
    
    # Scrape jobs
    jobs = scraper.scrape_jobs(
        search_query=search_query,
        location=location,
        unfamiliar_skills=unfamiliar_skills,
        max_pages=max_pages
    )
    
    if jobs:
        print(f"\nFound {len(jobs)} suitable jobs!")
        
        # Display summary
        for i, job in enumerate(jobs[:5]):  # Show first 5 jobs
            print(f"\n--- Job {i + 1} ---")
            print(f"Title: {job['job_title']}")
            print(f"Company: {job['company']}")
            print(f"Skills: {', '.join(job['skills'][:3])}...")  # Show first 3 skills
            print(f"Posted: {job['posted_date']}")
    else:
        print("No suitable jobs found. Try adjusting your search criteria.")


if __name__ == "__main__":
    main()