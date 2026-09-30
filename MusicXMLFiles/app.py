#app.py 
import json
import sys
from pathlib import Path
from converter import convert_musicxml

def main():
    if len(sys.argv) < 3:
        print("🎼 MusicXML → JSON Converter")
        print("Usage:")
        print("  python app.py input.musicxml output.json")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print("❌ Fichier MusicXML introuvable")
        sys.exit(1)

    partition = convert_musicxml(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(partition, f, indent=4)

    print("✅ Conversion réussie")
    print(f"📄 {output_path}")

if __name__ == "__main__":
    main()
