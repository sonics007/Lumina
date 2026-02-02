import os
import hashlib
import requests
from urllib.parse import urlparse
from pathlib import Path
import logging

class ImageDownloader:
    """
    Service for downloading and managing movie poster images.
    Downloads images locally and provides URLs for better quality and faster loading.
    """
    
    def __init__(self, base_dir='static/posters'):
        """
        Initialize the image downloader.
        
        Args:
            base_dir: Directory where images will be stored (relative to app root)
        """
        self.base_dir = base_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def ensure_directory(self):
        """Create the posters directory if it doesn't exist."""
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)
        
    def get_image_hash(self, url):
        """Generate a unique hash for an image URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_file_extension(self, url, content_type=None):
        """
        Determine file extension from URL or content type.
        
        Args:
            url: Image URL
            content_type: HTTP Content-Type header
            
        Returns:
            File extension (e.g., '.jpg', '.png', '.webp')
        """
        # Try to get extension from URL
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if path.endswith('.webp'):
            return '.webp'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.gif'):
            return '.gif'
        elif path.endswith(('.jpg', '.jpeg')):
            return '.jpg'
        
        # Try to determine from content type
        if content_type:
            ct = content_type.lower()
            if 'webp' in ct:
                return '.webp'
            elif 'png' in ct:
                return '.png'
            elif 'gif' in ct:
                return '.gif'
            elif 'jpeg' in ct or 'jpg' in ct:
                return '.jpg'
        
        # Default to jpg
        return '.jpg'
    
    def download_image(self, url, force=False):
        """
        Download an image from URL and save it locally.
        
        Args:
            url: Image URL to download
            force: Force re-download even if file exists
            
        Returns:
            Local path to the downloaded image (relative to static folder)
            or None if download failed
        """
        if not url:
            return None
            
        try:
            self.ensure_directory()
            
            # Generate unique filename based on URL hash
            img_hash = self.get_image_hash(url)
            
            # Try to download to determine extension
            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Determine extension
            content_type = response.headers.get('Content-Type', '')
            extension = self.get_file_extension(url, content_type)
            
            # Full local path
            filename = f"{img_hash}{extension}"
            local_path = os.path.join(self.base_dir, filename)
            
            # Check if already exists
            if os.path.exists(local_path) and not force:
                logging.info(f"Image already exists: {filename}")
                return f"/{self.base_dir}/{filename}"
            
            # Download and save
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logging.info(f"Downloaded image: {url} -> {filename}")
            return f"/{self.base_dir}/{filename}"
            
        except Exception as e:
            logging.error(f"Failed to download image {url}: {e}")
            return None
    
    def download_images_batch(self, urls, max_workers=5):
        """
        Download multiple images in parallel.
        
        Args:
            urls: List of image URLs
            max_workers: Number of parallel downloads
            
        Returns:
            Dictionary mapping original URLs to local paths
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.download_image, url): url 
                for url in urls if url
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    local_path = future.result()
                    results[url] = local_path
                except Exception as e:
                    logging.error(f"Error downloading {url}: {e}")
                    results[url] = None
        
        return results
    
    def cleanup_unused_images(self, used_images):
        """
        Remove images that are no longer referenced in the database.
        
        Args:
            used_images: Set of image paths currently in use
        """
        try:
            if not os.path.exists(self.base_dir):
                return
                
            # Get all files in posters directory
            all_files = set(os.listdir(self.base_dir))
            
            # Extract filenames from used paths
            used_filenames = set()
            for path in used_images:
                if path and path.startswith(f"/{self.base_dir}/"):
                    filename = path.split('/')[-1]
                    used_filenames.add(filename)
            
            # Remove unused files
            removed_count = 0
            for filename in all_files:
                if filename not in used_filenames:
                    file_path = os.path.join(self.base_dir, filename)
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        logging.info(f"Removed unused image: {filename}")
                    except Exception as e:
                        logging.error(f"Failed to remove {filename}: {e}")
            
            logging.info(f"Cleanup complete: removed {removed_count} unused images")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

# Global instance
image_downloader = ImageDownloader()
