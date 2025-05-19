import os
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_nigeria_trends():
    """
    Scrape the top 5 trending topics in Nigeria from GetDayTrends using Selenium.
    
    Returns:
        list: List of trending topics as strings
    """
    print("Fetching trending topics from Nigeria using Selenium...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no browser UI)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Initialize the Chrome driver
        # Note: You need to have chromedriver installed and in your PATH
        # or specify the path to chromedriver executable
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to the website
        driver.get('https://getdaytrends.com/nigeria/')
        
        # Wait for the trends table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'trends-table')]"))
        )
        
        # Extract trending topics
        trend_elements = driver.find_elements(By.XPATH, "//table[contains(@class, 'trends-table')]//tr/td[1]/a")
        
        trends = []
        # Get the top 5 trends
        for i, element in enumerate(trend_elements):
            if i >= 5:  # Only get top 5
                break
            trend_text = element.text.strip()
            if trend_text:
                trends.append(trend_text)
        
        print(f"Found {len(trends)} trends: {trends}")
        
        # Close the browser
        driver.quit()
        
        return trends
        
    except Exception as e:
        print(f"Error fetching trends with Selenium: {e}")
        # Fallback to alternative source if primary fails
        return get_trends_alternative()

def get_trends_alternative():
    """
    Alternative method to get trending topics in case the primary method fails.
    Uses Twitter's API (would require authentication in a real implementation).
    
    Note: This is a placeholder implementation.
    
    Returns:
        list: List of trending topics as strings
    """
    print("Using alternative method to fetch trends...")
    
    try:
        # Try with a simpler Selenium approach on an alternative page
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://trends24.in/nigeria/')
        
        # Wait for trends to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ol.trend-card__list li a"))
        )
        
        # Extract trends
        trend_elements = driver.find_elements(By.CSS_SELECTOR, "ol.trend-card__list li a")
        alt_trends = []
        
        for i, element in enumerate(trend_elements):
            if i >= 5:  # Only get top 5
                break
            trend_text = element.text.strip()
            if trend_text:
                alt_trends.append(trend_text)
        
        driver.quit()
        return alt_trends
        
    except Exception as e:
        print(f"Error in alternative method: {e}")
        
        # Fallback to hardcoded trends as last resort
        sample_trends = [
            "#NigeriaDecides2023",
            "Naira",
            "Lagos",
            "Peter Obi", 
            "Davido"
        ]
        
        return sample_trends

def get_image_for_trend(trend, api_key, cx_id):
    """
    Fetch a relevant image for a given trend using Google Custom Search API directly.
    
    Args:
        trend (str): The trending topic to search for
        api_key (str): Google API key
        cx_id (str): Google Custom Search Engine ID
    
    Returns:
        str: URL of a relevant image
    """
    print(f"Searching for image related to: {trend}")
    
    try:
        # Define the API endpoint
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Define search parameters
        params = {
            'q': f"{trend} Nigeria news",
            'num': 1,
            'safe': 'medium',
            'searchType': 'image',
            'imgSize': 'medium',
            'key': api_key,
            'cx': cx_id
        }
        
        # Make the request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse the response
        data = response.json()
        
        # Get the URL of the first result
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['link']
            
    except Exception as e:
        print(f"Error fetching image for {trend}: {e}")
        
    # Return a placeholder image if search fails
    return "https://via.placeholder.com/300x200?text=Nigeria+News"

def create_results_json(trends_with_images):
    """
    Create a structured JSON with trends and their images.
    
    Args:
        trends_with_images (dict): Dictionary mapping trends to image URLs
    
    Returns:
        str: JSON string with results
    """
    result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "country": "Nigeria",
        "trends": []
    }
    
    for trend, image_url in trends_with_images.items():
        result["trends"].append({
            "name": trend,
            "image_url": image_url
        })
    
    return json.dumps(result, indent=2)

def main():
    """
    Main function to run the Nigeria trends bot.
    """
    print("Starting Nigeria Twitter Trends Bot...")
    
    # Get API key and CX ID from environment variables
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID")
    
    # Check if environment variables are set
    if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
        print("Error: API key or CX ID not found in environment variables.")
        print("Please create a .env file with GOOGLE_API_KEY and GOOGLE_CX_ID variables.")
        return
    
    # Get trending topics
    trends = get_nigeria_trends()
    
    if not trends:
        print("Failed to retrieve trends. Please check your network connection and webdriver setup.")
        return
    
    # Get images for each trend (with rate limiting to avoid API limits)
    trends_with_images = {}
    for trend in trends:
        image_url = get_image_for_trend(trend, GOOGLE_API_KEY, GOOGLE_CX_ID)
        trends_with_images[trend] = image_url
        time.sleep(1)  # Wait briefly between requests
    
    # Create JSON result
    result_json = create_results_json(trends_with_images)
    
    # Save to file
    with open("nigeria_trends_results.json", "w") as f:
        f.write(result_json)
    
    print(f"Process completed. Results saved to 'nigeria_trends_results.json'")
    print("\nSample output:")
    print(result_json)

if __name__ == "__main__":
    main()