from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    png_source = Path(r"C:\Users\Praveen\.gemini\antigravity-ide\brain\1e92500d-fb76-455d-b054-38236f15e064\ai_model_icon_new_1780674482368.png")
    
    # Target locations
    resources_icon_dir = project_root / "src" / "gui" / "resources" / "icons"
    resources_icon_dir.mkdir(parents=True, exist_ok=True)
    
    png_target = resources_icon_dir / "ai_model_icon.png"
    ico_target = project_root / "ai_model.ico"
    
    if not png_source.exists():
        print(f"Source PNG not found at: {png_source}")
        return 1
        
    # Copy PNG to resource folder
    img = Image.open(png_source).convert("RGBA")
    img.save(png_target, format="PNG")
    print(f"Copied source icon to: {png_target}")
    
    # Save as multi-size ICO
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (96, 96), (128, 128), (256, 256)]
    img.save(ico_target, format="ICO", sizes=sizes)
    print(f"Generated multi-size ICO at: {ico_target}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
