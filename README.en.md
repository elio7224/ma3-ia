# MA3-IA — grandMA3 AI Control

🇫🇷 [Version française](README.md)

An AI assistant (Claude, Anthropic API) that drives a **grandMA3 onPC** console on Windows:
it reads your showfile (index + XML exports) and sends commands to the console over **OSC**.

> ⚠️ **Independent project, not affiliated with MA Lighting Technology GmbH**, nor endorsed or supported by it.
> See [Notices](#notices).

> 🎭 **A preparation tool, not a show operator.** MA3-IA helps you build and understand your show
> (programming, macros, searching, explanations). It **does not replace a human during a live show**: never let it
> drive the console on its own mid-performance. The AI can be wrong, and OSC does not confirm that a command
> succeeded. During a live show, the lighting operator always stays in control.

## What it can do
- Answer questions about your show (macros, sequences, presets, groups, MAtricks, appearances).
- Create and edit objects: macros (including in bulk), MAtricks, effect grids, free commands.
- Look up the official grandMA3 manual when it is unsure about a syntax.
- **Command log**: everything sent to the console, with the time and the AI tool that sent it.
- **Cost guard**: spending limit per session, warning at 80%, requests blocked at the limit.
- **English and French interface** (automatic from the Windows language, can be changed in Settings).

The AI answers in the language you write in.

## Requirements
- Windows 10/11 (64-bit), grandMA3 onPC. Python 3.12 only for the "from source" version.
- An Anthropic API key (https://console.anthropic.com).
- On the console: incoming OSC enabled (UDP, address `/cmd`) and the `ai_index.lua` Lua plugin imported.

## Installation
**Easiest: the installer** (no Python needed)
1. Download `MA3-IA-Setup-x.y.z.exe` from the [Releases](https://github.com/elio7224/ma3-ia/releases).
2. Run it: it installs for your Windows account, without admin rights, with shortcuts and an uninstaller.
3. On first launch, a wizard asks for the API key and the console's OSC address, and checks the plugin.

> **"Windows protected your PC"?** The installer is not code-signed yet, and Windows SmartScreen warns about any
> new unsigned program. Click **More info → Run anyway**.
> To verify the file: it is built by GitHub Actions straight from this source code (*Actions* tab),
> and its SHA-256 checksum is published with the Release (`Get-FileHash .\MA3-IA-Setup-x.y.z.exe`).

**From source**: download the project, then double-click `run.bat` (creates the Python environment,
installs everything, creates an `MA3-IA` shortcut on the Desktop).

More details (data locations, building the `.exe`, tests): see [README_BUREAU.md](README_BUREAU.md) (in French).

## Security
- The API key is stored in Windows Credential Manager, never in a project file.
- OSC is one-way: the AI sends commands but cannot confirm they succeeded.
  Always test on a copy of your show first.
- No AI at the controls during a show: use MA3-IA for preparation, rehearsals or with no audience,
  and always check the result on the console before going live.
- Your chat history, settings and command log stay on your PC (the app's configuration folder),
  never in the project folder.

## License
Code released under the [MIT](LICENSE) license: free to use, modify and redistribute, as long as the copyright notice is kept.

## Notices
- This project is **independent**: it is not affiliated with, endorsed, sponsored or supported by **MA Lighting Technology GmbH**.
- "grandMA3" and "MA Lighting" are trademarks of MA Lighting Technology GmbH, mentioned only to indicate
  which hardware the application works with.
- The grandMA3 manual is not included: the `doc_grandma3` tool downloads the public pages of
  help.malighting.com on demand, for local use.
- The application is provided without warranty (see the license). Always test on a copy of your show before a performance.
