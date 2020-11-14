# Requirements:
- NodeJS 8 or higher: https://nodejs.org
- NPM 5.3 or higher: https://www.npmjs.com/

# Bundle
$ npm install
$ npm run build

You can add "npm run watch" command to development purposes.

# Long Setup instructions:
1. Install NodeJS
2. Open terminal or Windows PowerShell
3. Use "cd <path to this directory>" command
4. Run "npm install" in this directory
5. Run "npm run watch" in this directory
6. Start the game with the launch parameter "-cef_remote_dbg_port 8080"
7. In Chrome navigate to localhost:8080
8. Select main menu page. Now you can use the dev tools to inspect and reload the page!

# Before committing:
1. Run: npm run build
2. Make sure all files in "build" folder are added
