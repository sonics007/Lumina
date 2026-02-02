#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to download images for existing movies in the database.
This will replace remote image URLs with local paths for better quality and faster loading.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from app import create_app
from app.models import db, Movie
from app.services.image_downloader import image_downloader

def download_all_images():
    """Download images for all movies that have remote URLs."""
    app = create_app()
    
    with app.app_context():
        # Get all movies with remote image URLs
        movies = Movie.query.filter(
            Movie.image.isnot(None),
            Movie.image != ''
        ).all()
        
        print(f"Found {len(movies)} movies with images")
        
        remote_movies = []
        for movie in movies:
            # Check if image is remote URL (not local path)
            if movie.image and (movie.image.startswith('http://') or movie.image.startswith('https://')):
                remote_movies.append(movie)
        
        print(f"Found {len(remote_movies)} movies with remote images to download")
        
        if not remote_movies:
            print("All images are already local!")
            return
        
        # Download images in batches
        batch_size = 50
        total_downloaded = 0
        total_failed = 0
        
        for i in range(0, len(remote_movies), batch_size):
            batch = remote_movies[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(remote_movies)-1)//batch_size + 1}")
            
            # Collect URLs
            url_to_movie = {}
            for movie in batch:
                url_to_movie[movie.image] = movie
            
            # Download batch
            print(f"Downloading {len(url_to_movie)} images...")
            results = image_downloader.download_images_batch(list(url_to_movie.keys()), max_workers=10)
            
            # Update database
            for url, local_path in results.items():
                movie = url_to_movie[url]
                if local_path:
                    old_url = movie.image
                    movie.image = local_path
                    total_downloaded += 1
                    print(f"[OK] {movie.title[:40]}: {old_url[:50]} -> {local_path}")
                else:
                    total_failed += 1
                    print(f"[FAIL] Failed: {movie.title[:40]}")
            
            # Commit batch
            try:
                db.session.commit()
                print(f"Committed batch to database")
            except Exception as e:
                print(f"Error committing batch: {e}")
                db.session.rollback()
        
        print(f"\n{'='*60}")
        print(f"Download complete!")
        print(f"Successfully downloaded: {total_downloaded}")
        print(f"Failed: {total_failed}")
        print(f"{'='*60}")

if __name__ == '__main__':
    print("="*60)
    print("Movie Image Downloader")
    print("="*60)
    print("\nThis script will download all remote movie images and save them locally.")
    print("Images will be stored in: static/posters/")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(0)
    
    download_all_images()
