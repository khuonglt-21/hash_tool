# Hash Tool

A lightweight Windows context menu tool for quickly calculating various hash values of files.

## 🧰 Features

- Right-click on any file and select **"Calculate hash..."** to launch the tool.
- Supports multiple hash types:
  - MD5
  - SHA-1
  - SHA-256
  - CRC32
  - SHA-384
  - SHA-512
- Saves calculated hashes to a `.txt` file.
- Faster than native PowerShell hash calculations.
- Option to generate PowerShell command for manual hashing.

## 🛠️ Installation Steps

1. **Install Python**  
   Download and install the latest version of Python from [https://www.python.org](https://www.python.org).

2. **Install PyInstaller**  
   Open a terminal and run:  
   ```bash
   pip install pyinstaller
   ```

3. **Build the Executable**  
   Navigate to the directory containing `hash_tool.py` and run:  
   ```bash
   pyinstaller --onefile --noconsole hash_tool.py
   ```

4. **Adjust Executable Path**  
   Edit the registry file `Add-HashToolSubmenu.reg` to update the path to the newly generated `hash_tool.exe`.  

5. **Add Context Menu Entry**  
   Run the `Add-HashToolSubmenu.reg` file by double-clicking it and accepting the changes to the Windows registry.

6. **Test the Tool**  
   Right-click on any file and choose **"Calculate hash..."** from the context menu to verify it works as expected.

7. **Uninstall the Tool (Optional)**  
   To remove the context menu entry, run `Remove-HashToolContextMenu.reg`.

## ⚠️ Notes

- The first time you run the tool, some antivirus programs may flag or scan the file. This is expected behavior for new executables.  
  If it doesn’t run immediately, please wait a bit or try again.
- **Tip:** After resizing the window, click the checkbox **"Save hash file"** twice to ensure the window size is remembered.

---

Made with 🐍 Python + ❤️ for fast and simple file hashing.
