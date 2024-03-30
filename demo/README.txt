Running the following commands in the terminal would help you to launch the
demo tracker we have been working on.

1) Create a Folder where you want to store the code and open terminal.

2) Cloning the Roundup code: 
hg clone http://hg.code.sf.net/p/roundup/code roundup

3) Opening Roundup Project on VSCode:
code roundup

4) Cloning the demo tracker(which we are currently working on) from the git repository of our team: 
git clone https://github.com/UMB-CS682-Team-02/tracker.git

5) Install pygal if not already installed:
pip install pygal

6) Rename the config.ini.sample file to config.ini which is located in tracker/demo.

7) initializing the roundup_admin script which will initialize the admin and demo user:
python roundup/scripts/roundup_admin.py demo init

8) To load the tracker with dummy data :

Setting PYTHONPATH
==================

Before running any scripts in the Roundup project, ensure that the PYTHONPATH environment variable includes
 the directory containing the `roundup` package. This is necessary for proper module imports.

Instructions for setting the PYTHONPATH:

Windows:
---------
1. Open the Start menu and search for "Environment Variables" or "Edit the system environment variables" and select it.
2. In the System Properties window, click on the "Environment Variables..." button at the bottom right.
3. In the Environment Variables window, under the "System Variables" section, click on the "New..." button.
4. In the "New System Variable" dialog, enter PYTHONPATH as the variable name and the path to the Roundup directory
(e.g., C:\path\to\Roundup) as the variable value.
5. Click "OK" to close the dialog.
6. Click "OK" again to close the Environment Variables window.
7. You may need to restart any running command prompts or applications for the changes to take effect.

Mac and Linux:
--------------
1. Open a terminal.
2. Run the following command, replacing /path/to/Roundup with the actual path to your Roundup directory:
   export PYTHONPATH=/path/to/Roundup:$PYTHONPATH
3. This command sets the PYTHONPATH environment variable for the duration of the terminal session.

Running load_tracker.py file:
=============================
To run the load_tracker.py file, follow these steps:

1. Set the PYTHONPATH environment variable as described above.
2. Navigate to the 'demo' directory where the load_tracker.py file is located using the terminal.
3. Run the load_tracker.py file using the terminal, providing two arguments:
   - The path to the demo directory.
   - The number of data records you want to generate.

Example:
python load_tracker.py /path/to/demo_directory 1000

Replace '/path/to/demo_directory' with the actual path to the demo directory containing the load_tracker.py file, 
and '1000' with the desired number of data records to generate.

9) To run the demo tracker in the localhost:
python roundup/scripts/roundup_server.py demo=tracker\demo

After running this in the terminal - paste http://localhost:8080/demo/ in the browser to run
the demo tracker
