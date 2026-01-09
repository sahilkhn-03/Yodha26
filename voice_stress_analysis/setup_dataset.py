"""
Extract and Organize JL-Corpus Dataset
Moves dataset from Downloads to project folder
"""

import os
import shutil
import zipfile
from pathlib import Path

def extract_and_organize_dataset():
    """Extract and organize JL-Corpus dataset."""
    print("\n" + "="*70)
    print("📦 EXTRACTING & ORGANIZING JL-CORPUS DATASET")
    print("="*70)
    
    # Source (your download location)
    zip_path = r"C:\Users\91903\Downloads\archive(1).zip"
    
    # Destination (project folder)
    project_dir = Path(__file__).parent
    dataset_dir = project_dir / "dataset" / "jl_corpus"
    
    print(f"\n📂 Source ZIP: {zip_path}")
    print(f"📁 Destination: {dataset_dir}")
    
    # Check if ZIP exists
    if not os.path.exists(zip_path):
        print(f"\n❌ ZIP file not found at: {zip_path}")
        print("\n💡 Please check the path. Current Downloads folder:")
        downloads = r"C:\Users\91903\Downloads"
        if os.path.exists(downloads):
            files = os.listdir(downloads)
            zip_files = [f for f in files if f.endswith('.zip')]
            print(f"\nFound {len(zip_files)} ZIP files:")
            for f in zip_files[:10]:
                print(f"   • {f}")
        return False
    
    print(f"\n✅ Found ZIP file: {os.path.basename(zip_path)}")
    file_size = os.path.getsize(zip_path) / (1024*1024)
    print(f"📊 Size: {file_size:.2f} MB")
    
    # Extract ZIP
    print("\n⏳ Extracting ZIP file...")
    temp_extract = project_dir / "dataset" / "temp_extract"
    temp_extract.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get total files
            total_files = len(zip_ref.namelist())
            print(f"📦 Total files in ZIP: {total_files}")
            
            # Extract with progress
            for i, file in enumerate(zip_ref.namelist(), 1):
                if i % 100 == 0 or i == total_files:
                    print(f"   Extracting: {i}/{total_files} files...", end='\r')
                zip_ref.extract(file, temp_extract)
            
            print(f"\n✅ Extraction complete!")
        
        # Find the audio files
        print("\n🔍 Locating audio files...")
        
        # Look for the JL corpus folder
        jl_folder = None
        for root, dirs, files in os.walk(temp_extract):
            if 'JL(wav+txt)' in root or any('wav' in f.lower() for f in files[:5]):
                jl_folder = root
                break
        
        if jl_folder:
            print(f"✅ Found audio folder: {os.path.basename(jl_folder)}")
            
            # Count files
            audio_files = [f for f in os.listdir(jl_folder) if f.endswith('.wav')]
            txt_files = [f for f in os.listdir(jl_folder) if f.endswith('.txt')]
            
            print(f"\n📊 Dataset contents:")
            print(f"   🎵 Audio files (.wav): {len(audio_files)}")
            print(f"   📄 Text files (.txt): {len(txt_files)}")
            
            # Copy to destination
            print(f"\n📋 Copying files to project folder...")
            dataset_dir.mkdir(parents=True, exist_ok=True)
            
            copied_count = 0
            for file in os.listdir(jl_folder):
                if file.endswith(('.wav', '.txt')):
                    src = os.path.join(jl_folder, file)
                    dst = dataset_dir / file
                    shutil.copy2(src, dst)
                    copied_count += 1
                    if copied_count % 50 == 0:
                        print(f"   Copied: {copied_count} files...", end='\r')
            
            print(f"\n✅ Copied {copied_count} files successfully!")
            
            # Clean up temp folder
            print("\n🧹 Cleaning up temporary files...")
            shutil.rmtree(temp_extract)
            print("✅ Cleanup complete!")
            
            # Show sample files
            print(f"\n📂 Dataset location: {dataset_dir}")
            print(f"\n📋 Sample files:")
            sample_files = sorted(os.listdir(dataset_dir))[:5]
            for f in sample_files:
                file_path = dataset_dir / f
                size = os.path.getsize(file_path) / 1024
                print(f"   • {f} ({size:.1f} KB)")
            
            return True
        else:
            print("❌ Could not find JL corpus audio folder in ZIP")
            print("\n📂 ZIP contents:")
            for root, dirs, files in os.walk(temp_extract):
                level = root.replace(str(temp_extract), '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:3]:
                    print(f"{subindent}{file}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_dataset():
    """Verify dataset is ready for training."""
    print("\n" + "="*70)
    print("✅ DATASET VERIFICATION")
    print("="*70)
    
    project_dir = Path(__file__).parent
    dataset_dir = project_dir / "dataset" / "jl_corpus"
    
    if not dataset_dir.exists():
        print(f"❌ Dataset folder not found: {dataset_dir}")
        return False
    
    audio_files = list(dataset_dir.glob("*.wav"))
    txt_files = list(dataset_dir.glob("*.txt"))
    
    print(f"\n📊 Dataset Statistics:")
    print(f"   Location: {dataset_dir}")
    print(f"   Audio files: {len(audio_files)}")
    print(f"   Text files: {len(txt_files)}")
    
    if len(audio_files) > 0:
        total_size = sum(f.stat().st_size for f in audio_files) / (1024*1024)
        print(f"   Total size: {total_size:.2f} MB")
        
        print(f"\n✅ Dataset ready for training!")
        print(f"\n🎯 Next steps:")
        print(f"   1. Run feature extraction")
        print(f"   2. Train XGBoost model")
        print(f"   3. Evaluate performance")
        return True
    else:
        print(f"\n❌ No audio files found in dataset folder")
        return False

def main():
    """Main function."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "📦 DATASET SETUP & ORGANIZATION" + " "*21 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\n📌 This script will:")
    print("   1. Extract archive(1).zip from Downloads")
    print("   2. Find JL-Corpus audio files")
    print("   3. Copy them to project folder")
    print("   4. Clean up temporary files")
    
    proceed = input("\n🚀 Ready to proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("❌ Setup cancelled")
        return
    
    # Extract and organize
    success = extract_and_organize_dataset()
    
    if success:
        # Verify
        verify_dataset()
        
        print("\n" + "="*70)
        print("🎉 SUCCESS! Dataset is ready for training!")
        print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("❌ Setup incomplete - Please check errors above")
        print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
