# psy-level

## Introduction
This project implements a psychological levels breakout strategy for cryptocurrency trading. The following instructions will guide you through setting up the environment, running the backtest, and viewing the results.

## Prerequisites
- A GitHub account
- Access to GitHub Codespaces

## Setup Instructions

### 1. Create a Codespace
1. Navigate to the repository on GitHub.
2. Click on the green "Code" button.
3. Select "Open with Codespaces" and create a new Codespace.

### 2. Install Required Extensions
Once the Codespace is open, you need to install the following extensions:
1. **Live Server**: This extension allows you to serve the HTML file and view it in the browser.
2. **Jupyter**: This extension is required for running Jupyter notebooks.
3. **Python**: This extension provides Python language support.

To install these extensions:
1. Click on the Extensions icon (four squares) on the left sidebar.
2. Search for "Live Server" and click "Install".
3. Search for "Jupyter" and click "Install".
4. Search for "Python" and click "Install".

### 3. Install Python Dependencies
Open a terminal in the Codespace:
1. Click on the three-bar icon (hamburger menu) in the top-left corner.
2. Select "Terminal" and then "New Terminal".

In the terminal, run the following command to install the required Python packages:
```sh
pip install -r requirements.txt
```

### 4. Adjust Configuration
Edit the config.py file to adjust the strategy parameters as needed. You can change settings like the symbol, timeframe, initial capital, and backtest period.

### 5. Run the Backtest
Use the config.py file and change the parameters as you like. Aslos the strategy.py file needs work as it is the core strategy file. Once they are done, in the terminal, run the following command to execute the backtest:

```sh
python run_backtest.py
```
### 6. View the Results
After running the backtest, a file named backtest_results.html will be generated. To view the results:

- Right-click on the backtest_results.html file in the file explorer.
- Select "Open with Live Server".
- If the file does not open automatically, refresh the browser window.

### 7. Stop the Terminal
To stop the terminal, press Ctrl + C.

### Additional Tips
If you encounter any issues, try refreshing the Codespace window.
Make sure to save any changes to the configuration file before running the backtest.
By following these steps, you should be able to set up the environment, run the backtest, and view the results without any issues. If you have any questions or need further assistance, please feel free to reach out.

