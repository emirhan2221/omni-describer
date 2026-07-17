# sapi5_helper_32bit.py
# This script MUST be compiled with a 32-BIT Python interpreter.
# It acts as a bridge for a 64-bit application to access 32-bit SAPI5 voices.
import sys
import json
import traceback
import platform

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

def list_voices():
    """Lists available 32-bit SAPI5 voices and prints them as JSON."""
    voice_list = []
    try:
        engine = pyttsx3.init('sapi5')
        all_voices = engine.getProperty('voices')
        engine.stop()

        for v in all_voices:
            try:
                # The act of accessing these properties can trigger the bug
                voice_data = {"name": v.name, "id": v.id, "age": v.age}
                voice_list.append(voice_data)
            except ValueError as e:
                # This is where we catch the 'invalid literal for int() with base 16' error
                print(f"Warning: Skipping a problematic SAPI5 voice. Name: {getattr(v, 'name', 'N/A')}, Error: {e}", file=sys.stderr)
                continue
        return voice_list
        
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return {"error": f"Failed to initialize pyttsx3 or get voices: {str(e)}"}

def synthesize(data):
    """Synthesizes text to a WAV file based on the provided data."""
    try:
        text = data['text']
        output_path = data['output_path']
        voice_id = data.get('voice_id')
        rate = data.get('rate', 180)

        engine = pyttsx3.init('sapi5')

        if voice_id:
            engine.setProperty('voice', voice_id)
        
        engine.setProperty('rate', rate)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        engine.stop()

    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main entry point for the helper.
    - If run with --list-voices, it outputs JSON.
    - If given data via stdin, it synthesizes speech.
    """
    # 1. Critical dependency check
    if not PYTTSX3_AVAILABLE:
        error_msg = ("FATAL: 'pyttsx3' library not found in this Python environment. "
                     "Please install it in your 32-BIT Python environment using: "
                     "python.exe -m pip install pyttsx3")
        try:
            print(error_msg, file=sys.stderr)
        except Exception:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("SAPI Helper Error", error_msg)
        sys.exit(1)

    # 2. Handle --list-voices command
    if len(sys.argv) > 1 and sys.argv[1] == '--list-voices':
        voices = list_voices()
        print(json.dumps(voices))
        sys.exit(0)
    
    # 3. Handle synthesis command from stdin
    #    If not listing voices, assume we are synthesizing.
    try:
        if sys.stdin is None:
             print("Error: Standard input is not available.", file=sys.stderr)
             sys.exit(1)

        input_line = sys.stdin.readline()
        if not input_line:
            print("Error: No data received from stdin.", file=sys.stderr)
            sys.exit(1)
            
        data = json.loads(input_line)
        synthesize(data)
        sys.exit(0)

    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()