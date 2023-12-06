import os
import glob

def run_across_files(_files_list):
    """
        _files_list: list of files to run
    """
    for _file in _files_list:
        print(f"Running {_file}")
        
        # update the team_5.py file
        with open('players/team_5.bak', 'r') as f:
            team_file = f.read()
        
        team_file = team_file.replace('CHECKPOINT_FILE_NAME_TO_BE_REPLACES_HERE', _file)

        with open('players/team_5.py', 'w') as f:
            f.write(team_file)
        
        # run the evaluation

        print('Running evaluation for team 5')
        # first with just team 5
        try:
            os.system('python3 main.py -teams 5 -s 42 -T 360 -g False')
            
            # log the results
            with open('logs/results.txt', 'r') as f:
                data = f.read()
                results = data.split('\n')[5:8]
            print('results: ', results)
            with open('all_results.txt', 'a') as f:
                f.write(_file + ' Team-5\n' + '\n'.join(results) + '\n')
        except:
            with open('all_results.txt', 'a') as f:
                f.write(_file + ' Team-5' + '\nERROR!\n')

        print('Running evaluation for all teams')
        
        # then with all teams
        try:
            os.system('python3 main.py -teams 1 2 3 4 5 6 -s 42 -T 360 -g False')

            # log the results
            with open('logs/results.txt', 'r') as f:
                data = f.read()
                results = data.split('\n')[5:12]
            print('results: ', results)
            with open('all_results.txt', 'a') as f:
                f.write(_file + ' All teams\n' + '\n'.join(results) + '\n')
        except:
            with open('all_results.txt', 'a') as f:
                f.write(_file + ' All teams' + '\nERROR!\n')

if __name__ == '__main__':
    files_list = glob.glob('RLEnvironment/*.zip')
    run_across_files(files_list)