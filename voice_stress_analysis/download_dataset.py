"""
Kaggle Dataset Downloader for JL-Corpus
Stress Detection Audio Dataset
"""

import os
import sys
import subprocess

def check_kaggle_setup():
    """Check if Kaggle API is set up."""
    print("🔍 Checking Kaggle API setup...")
    
    # Check if kaggle package is installed
    try:
        import kaggle
        print("✅ Kaggle package installed")
    except ImportError:
        print("❌ Kaggle package not found")
        print("\n📦 Installing kaggle package...")
        subprocess.run([sys.executable, "-m", "pip", "install", "kaggle"], check=True)
        print("✅ Kaggle package installed")
    
    # Check for API credentials
    kaggle_dir = os.path.expanduser("~/.kaggle")
    kaggle_json = os.path.join(kaggle_dir, "kaggle.json")
    
    if os.path.exists(kaggle_json):
        print(f"✅ Kaggle credentials found at {kaggle_json}")
        return True
    else:
        print(f"❌ Kaggle credentials not found at {kaggle_json}")
        return False

def setup_kaggle_credentials():
    """Guide user to set up Kaggle credentials."""
    print("\n" + "="*70)
    print("🔑 KAGGLE API SETUP REQUIRED")
    print("="*70)
    print("\nFollow these steps to get your Kaggle API token:\n")
    print("1. Go to: https://www.kaggle.com/")
    print("2. Sign in (or create free account)")
    print("3. Click your profile picture → 'Settings'")
    print("4. Scroll down to 'API' section")
    print("5. Click 'Create New Token'")
    print("6. This downloads 'kaggle.json' file\n")
    
    print("="*70)
    print("📁 PLACE THE FILE HERE:")
    print("="*70)
    
    kaggle_dir = os.path.expanduser("~/.kaggle")
    print(f"\nWindows: {kaggle_dir}")
    print(f"Or: C:\\Users\\YourUsername\\.kaggle\\kaggle.json\n")
    
    print("="*70)
    
    input("\n👉 Press ENTER after you've placed kaggle.json in the folder...")
    
    # Create .kaggle directory if it doesn't exist
    os.makedirs(kaggle_dir, exist_ok=True)
    
    kaggle_json = os.path.join(kaggle_dir, "kaggle.json")
    if os.path.exists(kaggle_json):
        print("✅ Found kaggle.json!")
        
        # Set permissions (important for security)
        if os.name != 'nt':  # Unix-like systems
            os.chmod(kaggle_json, 0o600)
        
        return True
    else:
        print("❌ kaggle.json still not found!")
        print(f"   Expected location: {kaggle_json}")
        return False

def download_jl_corpus():
    """Download JL-Corpus dataset from Kaggle."""
    print("\n" + "="*70)
    print("📥 DOWNLOADING JL-CORPUS DATASET")
    print("="*70)
    
    dataset_name = "tli725/jl-corpus"
    download_path = "dataset/jl_corpus"
    
    print(f"\nDataset: {dataset_name}")
    print(f"Download to: {download_path}")
    print(f"\n⏳ This may take 10-20 minutes depending on your connection...")
    print("📊 Dataset size: ~2-3 GB\n")
    
    # Create download directory
    os.makedirs(download_path, exist_ok=True)
    
    try:
        # Download using Kaggle API
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        api = KaggleApi()
        api.authenticate()
        
        print("🔐 Authentication successful!")
        print("📥 Starting download...\n")
        
        # Download dataset
        api.dataset_download_files(
            dataset_name,
            path=download_path,
            unzip=True
        )
        
        print("\n✅ Download complete!")
        print(f"📁 Dataset saved to: {os.path.abspath(download_path)}")
        
        # Show contents
        print("\n📂 Dataset contents:")
        for root, dirs, files in os.walk(download_path):
            level = root.replace(download_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Show first 5 files
                print(f"{subindent}📄 {file}")
            if len(files) > 5:
                print(f"{subindent}... and {len(files) - 5} more files")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify kaggle.json is in the correct location")
        print("3. Make sure you accepted the dataset rules on Kaggle website")
        print(f"4. Visit: https://www.kaggle.com/datasets/{dataset_name}")
        return False

def main():
    """Main function to download JL-Corpus dataset."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "📥 JL-CORPUS DATASET DOWNLOADER" + " "*22 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\n📌 About JL-Corpus Dataset:")
    print("   • Voice stress detection dataset")
    print("   • Multiple speakers with stress/neutral labels")
    print("   • Perfect for training ML models")
    print("   • Size: ~2-3 GB")
    
    # Check system requirements
    import shutil
    total, used, free = shutil.disk_usage("/")
    free_gb = free // (2**30)
    
    print(f"\n💾 Available disk space: {free_gb} GB")
    if free_gb < 5:
        print("⚠️  Warning: Low disk space. Recommended: 5+ GB free")
        proceed = input("\n   Continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("❌ Download cancelled")
            return
    
    # Step 1: Check Kaggle setup
    if not check_kaggle_setup():
        if not setup_kaggle_credentials():
            print("\n❌ Cannot proceed without Kaggle credentials")
            print("\n💡 Manual download option:")
            print("   1. Go to: https://www.kaggle.com/datasets/tli725/jl-corpus")
            print("   2. Click 'Download' button")
            print("   3. Extract to: dataset/jl_corpus/")
            return
    
    # Step 2: Download dataset
    print("\n" + "-"*70)
    ready = input("\n🚀 Ready to download? (y/n): ")
    if ready.lower() != 'y':
        print("❌ Download cancelled")
        return
    
    success = download_jl_corpus()
    
    if success:
        print("\n" + "="*70)
        print("🎉 SUCCESS! Dataset ready for training")
        print("="*70)
        print("\n📊 Next steps:")
        print("   1. Run feature extraction script")
        print("   2. Train XGBoost model")
        print("   3. Evaluate performance")
        print("\n✅ You're all set!\n")
    else:
        print("\n" + "="*70)
        print("❌ Download failed - Manual option available")
        print("="*70)
        print("\n📥 Manual download:")
        print("   1. Visit: https://www.kaggle.com/datasets/tli725/jl-corpus")
        print("   2. Click 'Download' (requires Kaggle login)")
        print("   3. Extract ZIP to: dataset/jl_corpus/")
        print("   4. Run training script\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
